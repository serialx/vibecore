import asyncio
import contextlib
import datetime
import sys
import threading
from collections.abc import Callable, Coroutine
from typing import Any, Generic, Protocol, TypeAlias, overload

from agents import (
    Agent,
    RunConfig,
    RunHooks,
    Runner,
    Session,
    TContext,
    TResponseInputItem,
)
from agents.result import RunResultBase
from agents.run import DEFAULT_MAX_TURNS
from textual.pilot import Pilot
from typing_extensions import TypeVar

from vibecore.context import VibecoreContext
from vibecore.main import AppIsExiting, VibecoreApp
from vibecore.session import JSONLSession
from vibecore.settings import settings
from vibecore.widgets.core import MyTextArea
from vibecore.widgets.messages import SystemMessage


class UserInputFunc(Protocol):
    """Protocol for user input function with optional prompt parameter."""

    async def __call__(self, prompt: str = "") -> str:
        """Get user input with optional prompt message.

        Args:
            prompt: Optional prompt to display before getting input.

        Returns:
            The user's input string.
        """
        ...


TWorkflowReturn = TypeVar("TWorkflowReturn", default=RunResultBase)
DecoratedCallable: TypeAlias = Callable[..., Coroutine[Any, Any, TWorkflowReturn]]


class VibecoreRunnerBase(Generic[TWorkflowReturn]):
    def __init__(self, vibecore: "Vibecore[TWorkflowReturn]") -> None:
        self.vibecore = vibecore

    @property
    def session(self) -> Session:
        raise NotImplementedError("session property implemented.")

    async def user_input(self, prompt: str = "") -> str:
        raise NotImplementedError("user_input method not implemented.")

    async def print(self, message: str) -> None:
        print(message, file=sys.stderr)

    async def run_agent(
        self,
        starting_agent: Agent[TContext],
        input: str | list[TResponseInputItem],
        *,
        context: TContext | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        hooks: RunHooks[TContext] | None = None,
        run_config: RunConfig | None = None,
        previous_response_id: str | None = None,
        session: Session | None = None,
    ) -> RunResultBase:
        result = await Runner.run(
            starting_agent=starting_agent,
            input=input,  # Pass string directly when using session
            context=context,
            max_turns=max_turns,
            hooks=hooks,
            run_config=run_config,
            previous_response_id=previous_response_id,
            session=session,
        )
        return result


class VibecoreSimpleRunner(VibecoreRunnerBase[TWorkflowReturn]):
    def __init__(self, vibecore: "Vibecore[TWorkflowReturn]") -> None:
        super().__init__(vibecore)

        session_id = f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._session = JSONLSession(
            session_id=session_id,
            project_path=None,  # Will use current working directory
            base_dir=settings.session.base_dir,
        )

    @property
    def session(self) -> Session:
        return self._session


class VibecoreCliRunner(VibecoreSimpleRunner[TWorkflowReturn]):
    def __init__(self, vibecore: "Vibecore[TWorkflowReturn]") -> None:
        super().__init__(vibecore)

    async def user_input(self, prompt: str = "") -> str:
        return input(prompt)

    async def run(self) -> TWorkflowReturn:
        assert self.vibecore.workflow_logic is not None, (
            "Workflow logic not defined. Please use the @vibecore.workflow() decorator."
        )
        return await self.vibecore.workflow_logic()


class VibecoreStaticRunner(VibecoreSimpleRunner[TWorkflowReturn]):
    def __init__(self, vibecore: "Vibecore[TWorkflowReturn]") -> None:
        super().__init__(vibecore)
        self.inputs: list[str] = []
        self.prints: list[str] = []

    async def user_input(self, prompt: str = "") -> str:
        assert self.inputs, "No more user inputs available."
        return self.inputs.pop()

    async def print(self, message: str) -> None:
        # Capture printed messages instead of displaying them
        self.prints.append(message)

    async def run(self, inputs: list[str] | None = None) -> TWorkflowReturn:
        if inputs is None:
            inputs = []
        assert self.vibecore.workflow_logic is not None, (
            "Workflow logic not defined. Please use the @vibecore.workflow() decorator."
        )
        self.inputs.extend(inputs)
        return await self.vibecore.workflow_logic()


class VibecoreTextualRunner(VibecoreRunnerBase[TWorkflowReturn]):
    def __init__(self, vibecore: "Vibecore[TWorkflowReturn]") -> None:
        super().__init__(vibecore)
        self.app = VibecoreApp(self.vibecore.context, self.vibecore.starting_agent, show_welcome=False)
        self.app_ready_event = asyncio.Event()

    @property
    def session(self) -> Session:
        return self.app.session

    async def user_input(self, prompt: str = "") -> str:
        if prompt:
            await self.print(prompt)
        self.app.query_one(MyTextArea).disabled = False
        self.app.query_one(MyTextArea).focus()
        user_input = await self.app.wait_for_user_input()
        if self.vibecore.disable_user_input:
            self.app.query_one(MyTextArea).disabled = True
        return user_input

    async def print(self, message: str) -> None:
        await self.app.add_message(SystemMessage(message))

    async def run_agent(
        self,
        starting_agent: Agent[TContext],
        input: str | list[TResponseInputItem],
        *,
        context: TContext | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        hooks: RunHooks[TContext] | None = None,
        run_config: RunConfig | None = None,
        previous_response_id: str | None = None,
        session: Session | None = None,
    ) -> RunResultBase:
        result = Runner.run_streamed(
            starting_agent=starting_agent,
            input=input,  # Pass string directly when using session
            context=context,
            max_turns=max_turns,
            hooks=hooks,
            run_config=run_config,
            previous_response_id=previous_response_id,
            session=session,
        )

        self.app.current_worker = self.app.handle_streamed_response(result)
        await self.app.current_worker.wait()
        return result

    def on_app_ready(self) -> None:
        """Called when app is ready to process events."""
        self.app_ready_event.set()

    async def _run_app(self) -> None:
        """Run the apps message loop.

        Args:
            app: App to run.
        """

        with self.app._context():
            try:
                self.app._loop = asyncio.get_running_loop()
                self.app._thread_id = threading.get_ident()
                await self.app._process_messages(
                    ready_callback=self.on_app_ready,
                    headless=False,
                )
            finally:
                self.app_ready_event.set()

    async def _run_logic(self) -> TWorkflowReturn:
        assert self.vibecore.workflow_logic is not None, (
            "Workflow logic not defined. Please use the @vibecore.workflow() decorator."
        )
        try:
            return await self.vibecore.workflow_logic()
        except AppIsExiting:
            raise

    async def run(self, shutdown: bool = False) -> TWorkflowReturn:
        self.app = VibecoreApp(self.vibecore.context, self.vibecore.starting_agent, show_welcome=False)
        app_task = asyncio.create_task(self._run_app(), name=f"run_app({self.app})")
        await self.app_ready_event.wait()
        pilot = Pilot(self.app)
        logic_task: asyncio.Task[TWorkflowReturn] | None = None

        await pilot._wait_for_screen()
        if self.vibecore.disable_user_input:
            self.app.query_one(MyTextArea).disabled = True
        logic_task = asyncio.create_task(self._run_logic(), name="logic_task")
        done, pending = await asyncio.wait([logic_task, app_task], return_when=asyncio.FIRST_COMPLETED)

        # If app has exited and logic is still running, cancel logic
        if app_task in done and logic_task in pending:
            logic_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await logic_task
            raise AppIsExiting()
        # If logic is finished and app is still running
        elif logic_task in done and app_task in pending:
            result = logic_task.result()
            if shutdown:
                await pilot._wait_for_screen()
                await asyncio.sleep(1.0)
                self.app.exit()
                await app_task
            else:
                # Enable text input so users can interact freely
                self.app.query_one(MyTextArea).disabled = False
                # Wait until app is exited
                await app_task
            return result

        raise RuntimeError("Unexpected state: both tasks completed")


class Vibecore(Generic[TWorkflowReturn]):
    def __init__(self, starting_agent: Agent[TContext], disable_user_input: bool = True) -> None:
        self.context = VibecoreContext()
        self.workflow_logic: Callable[..., Coroutine[Any, Any, TWorkflowReturn]] | None = None
        self.starting_agent = starting_agent
        self.disable_user_input = disable_user_input
        self.runner: VibecoreRunnerBase[TWorkflowReturn] = VibecoreRunnerBase(self)

    @property
    def session(self) -> Session:
        return self.runner.session

    async def user_input(self, prompt: str = "") -> str:
        return await self.runner.user_input(prompt)

    async def print(self, message: str) -> None:
        return await self.runner.print(message)

    def workflow(self) -> Callable[[DecoratedCallable[TWorkflowReturn]], DecoratedCallable[TWorkflowReturn]]:
        """Decorator to define the workflow logic for the app.

        Returns:
            A decorator that wraps the workflow logic function.
        """

        def decorator(
            func: DecoratedCallable[TWorkflowReturn],
        ) -> DecoratedCallable[TWorkflowReturn]:
            self.workflow_logic = func
            return func

        return decorator

    async def run_agent(
        self,
        starting_agent: Agent[TContext],
        input: str | list[TResponseInputItem],
        *,
        context: TContext | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        hooks: RunHooks[TContext] | None = None,
        run_config: RunConfig | None = None,
        previous_response_id: str | None = None,
        session: Session | None = None,
    ) -> RunResultBase:
        return await self.runner.run_agent(
            starting_agent=starting_agent,
            input=input,
            context=context,
            max_turns=max_turns,
            hooks=hooks,
            run_config=run_config,
            previous_response_id=previous_response_id,
            session=session,
        )

    async def run_textual(self, shutdown: bool = False) -> TWorkflowReturn:
        if self.workflow_logic is None:
            raise ValueError("Workflow logic not defined. Please use the @vibecore.workflow() decorator.")

        self.runner = VibecoreTextualRunner(self)
        return await self.runner.run(shutdown=shutdown)

    async def run_cli(self) -> TWorkflowReturn:
        if self.workflow_logic is None:
            raise ValueError("Workflow logic not defined. Please use the @vibecore.workflow() decorator.")

        self.runner = VibecoreCliRunner(self)
        return await self.runner.run()

    @overload
    async def run(self, inputs: str) -> TWorkflowReturn: ...

    @overload
    async def run(self, inputs: list[str]) -> TWorkflowReturn: ...

    async def run(self, inputs: str | list[str]) -> TWorkflowReturn:
        if isinstance(inputs, str):
            inputs = [inputs]

        if self.workflow_logic is None:
            raise ValueError("Workflow logic not defined. Please use the @vibecore.workflow() decorator.")

        self.runner = VibecoreStaticRunner(self)
        return await self.runner.run(inputs=inputs)
