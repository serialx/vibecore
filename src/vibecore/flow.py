import asyncio
import contextlib
import datetime
import sys
import threading
from collections.abc import Callable, Coroutine
from typing import Any, Concatenate, Generic, TypeAlias, cast, overload

from agents import (
    Agent,
    RunConfig,
    RunHooks,
    Runner,
    Session,
    TResponseInputItem,
)
from agents.result import RunResultBase
from agents.run import DEFAULT_MAX_TURNS
from textual.pilot import Pilot
from typing_extensions import TypeVar

from vibecore.context import AppAwareContext
from vibecore.main import AppIsExiting, VibecoreApp
from vibecore.session import JSONLSession
from vibecore.settings import settings
from vibecore.widgets.core import MyTextArea
from vibecore.widgets.messages import SystemMessage


class NoUserInputLeft(Exception):
    """Raised when no more user inputs are available in static runner."""

    pass


TContext = TypeVar("TContext", default=None)
TWorkflowReturn = TypeVar("TWorkflowReturn", default=RunResultBase)


class VibecoreRunner(Generic[TContext, TWorkflowReturn]):
    def __init__(
        self,
        vibecore: "Vibecore[TContext, TWorkflowReturn]",
        context: TContext | None = None,
        session: Session | None = None,
    ) -> None:
        self.vibecore = vibecore
        self.context = context

        if session is None:
            session_id = f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self._session = JSONLSession(
                session_id=session_id,
                project_path=None,  # Will use current working directory
                base_dir=settings.session.base_dir,
            )
        else:
            self._session = session

    @property
    def session(self) -> Session:
        return self._session

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


class VibecoreCliRunner(VibecoreRunner[TContext, TWorkflowReturn]):
    def __init__(
        self,
        vibecore: "Vibecore[TContext, TWorkflowReturn]",
        context: TContext | None = None,
        session: Session | None = None,
    ) -> None:
        super().__init__(vibecore, context=context, session=session)

    async def _user_input(self, prompt: str = "") -> str:
        return input(prompt)

    async def run(self) -> TWorkflowReturn:
        assert self.vibecore.workflow_logic is not None, (
            "Workflow logic not defined. Please use the @vibecore.workflow() decorator."
        )
        result = None
        while user_message := await self._user_input():
            result = await self.vibecore.workflow_logic(self, user_message)

        assert result, "No result available after inputs exhausted."
        return result


class VibecoreStaticRunner(VibecoreRunner[TContext, TWorkflowReturn]):
    def __init__(
        self,
        vibecore: "Vibecore[TContext, TWorkflowReturn]",
        context: TContext | None = None,
        session: Session | None = None,
    ) -> None:
        super().__init__(vibecore, context=context, session=session)
        self.inputs: list[str] = []
        self.prints: list[str] = []

    async def print(self, message: str) -> None:
        # Capture printed messages instead of displaying them
        self.prints.append(message)

    async def run(self, inputs: list[str] | None = None) -> TWorkflowReturn:
        if inputs is None:
            inputs = []
        assert self.vibecore.workflow_logic is not None, (
            "Workflow logic not defined. Please use the @vibecore.workflow() decorator."
        )
        result = None
        for user_message in inputs:
            result = await self.vibecore.workflow_logic(self, user_message)

        assert result, "No result available after inputs exhausted."
        return result


class VibecoreTextualRunner(VibecoreRunner[AppAwareContext, TWorkflowReturn]):
    def __init__(
        self,
        vibecore: "Vibecore[AppAwareContext, TWorkflowReturn]",
        context: AppAwareContext | None = None,
        session: Session | None = None,
    ) -> None:
        super().__init__(vibecore, context=context, session=session)
        self.app = VibecoreApp(
            self,
            show_welcome=False,
        )
        self.app_ready_event = asyncio.Event()

    async def _user_input(self, prompt: str = "") -> str:
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
        starting_agent: Agent[AppAwareContext],
        input: str | list[TResponseInputItem],
        *,
        context: AppAwareContext | None = None,
        max_turns: int = DEFAULT_MAX_TURNS,
        hooks: RunHooks[AppAwareContext] | None = None,
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
        while True:
            user_message = await self._user_input()
            result = await self.vibecore.workflow_logic(self, user_message)
        assert result, "No result available after inputs exhausted."
        return result

    async def run(self, inputs: list[str] | None = None, shutdown: bool = False) -> TWorkflowReturn:
        if inputs:
            self.app.message_queue.extend(inputs)
        app_task = asyncio.create_task(self._run_app(), name=f"run_app({self.app})")
        await self.app_ready_event.wait()

        await self.app.load_session_history(self.session)
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
                await self.print("Workflow complete. Press Ctrl-Q to exit.")
                # Enable text input so users can interact freely
                self.app.query_one(MyTextArea).disabled = False
                # Wait until app is exited
                await app_task
            return result
        raise AssertionError(f"Unexpected state: done={done}, pending={pending}")


WorkflowLogic: TypeAlias = Callable[
    Concatenate[VibecoreRunner[TContext, TWorkflowReturn], str, ...],
    Coroutine[Any, Any, TWorkflowReturn],
]


class Vibecore(Generic[TContext, TWorkflowReturn]):
    def __init__(self, disable_user_input: bool = True) -> None:
        self.workflow_logic: WorkflowLogic[TContext, TWorkflowReturn] | None = None
        self.disable_user_input = disable_user_input

    def workflow(
        self,
    ) -> Callable[[WorkflowLogic[TContext, TWorkflowReturn]], WorkflowLogic[TContext, TWorkflowReturn]]:
        """Decorator to define the workflow logic for the app.

        Returns:
            A decorator that wraps the workflow logic function.
        """

        def decorator(
            func: WorkflowLogic[TContext, TWorkflowReturn],
        ) -> WorkflowLogic[TContext, TWorkflowReturn]:
            self.workflow_logic = func
            return func

        return decorator

    @overload
    async def run_textual(
        self,
        inputs: str | None = None,
        context: AppAwareContext | None = None,
        session: Session | None = None,
        shutdown: bool = False,
    ) -> TWorkflowReturn: ...
    @overload
    async def run_textual(
        self,
        inputs: list[str] | None = None,
        context: AppAwareContext | None = None,
        session: Session | None = None,
        shutdown: bool = False,
    ) -> TWorkflowReturn: ...

    async def run_textual(
        self,
        inputs: str | list[str] | None = None,
        context: AppAwareContext | None = None,
        session: Session | None = None,
        shutdown: bool = False,
    ) -> TWorkflowReturn:
        if isinstance(inputs, str):
            inputs = [inputs]

        if self.workflow_logic is None:
            raise ValueError("Workflow logic not defined. Please use the @vibecore.workflow() decorator.")

        assert isinstance(context, AppAwareContext) or context is None, (
            "Textual runner requires AppAwareContext or None."
        )
        # Type checker needs help: after the assertion, we know context is AppAwareContext | None
        # and this Vibecore instance can be treated as Vibecore[AppAwareContext, TWorkflowReturn]
        runner = VibecoreTextualRunner(
            cast("Vibecore[AppAwareContext, TWorkflowReturn]", self),
            context=context,
            session=session,
        )
        return await runner.run(inputs=inputs, shutdown=shutdown)

    async def run_cli(self, context: TContext | None = None, session: Session | None = None) -> TWorkflowReturn:
        if self.workflow_logic is None:
            raise ValueError("Workflow logic not defined. Please use the @vibecore.workflow() decorator.")

        runner = VibecoreCliRunner(self, context=context, session=session)
        return await runner.run()

    @overload
    async def run(
        self, inputs: str, context: TContext | None = None, session: Session | None = None
    ) -> TWorkflowReturn: ...

    @overload
    async def run(
        self, inputs: list[str], context: TContext | None = None, session: Session | None = None
    ) -> TWorkflowReturn: ...

    async def run(
        self, inputs: str | list[str], context: TContext | None = None, session: Session | None = None
    ) -> TWorkflowReturn:
        if isinstance(inputs, str):
            inputs = [inputs]

        if self.workflow_logic is None:
            raise ValueError("Workflow logic not defined. Please use the @vibecore.workflow() decorator.")

        runner = VibecoreStaticRunner(self, context=context, session=session)
        return await runner.run(inputs=inputs)
