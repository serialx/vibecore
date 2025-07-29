import traceback
from collections import deque
from typing import ClassVar, Literal

from agents import (
    Agent,
    Runner,
    RunResultStreaming,
    StreamEvent,
    TResponseInputItem,
)
from openai.types.responses.response_output_message import Content
from textual import log, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Header
from textual.worker import Worker

from vibecore.context import VibecoreContext
from vibecore.handlers import AgentStreamHandler
from vibecore.session import JSONLSession
from vibecore.session.loader import SessionLoader
from vibecore.settings import settings
from vibecore.utils.text import TextExtractor
from vibecore.widgets.core import AppFooter, MainScroll, MyTextArea
from vibecore.widgets.info import Welcome
from vibecore.widgets.messages import AgentMessage, BaseMessage, MessageStatus, UserMessage

AgentStatus = Literal["idle", "running"]


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH: ClassVar = [
        "widgets/core.tcss",
        "widgets/messages.tcss",
        "widgets/tool_messages.tcss",
        "widgets/expandable.tcss",
        "widgets/info.tcss",
        "main.tcss",
    ]
    BINDINGS: ClassVar = [
        ("ctrl+shift+d", "toggle_dark", "Toggle dark mode"),
        Binding("escape", "cancel_agent", "Cancel agent", show=False),
    ]

    agent_status = reactive[AgentStatus]("idle")

    def __init__(
        self,
        context: VibecoreContext,
        agent: Agent,
        session_id: str | None = None,
        print_mode: bool = False,
    ) -> None:
        """Initialize the Vibecore app with context and agent.

        Args:
            context: The VibecoreContext instance
            agent: The Agent instance to use
            session_id: Optional session ID to load existing session
            print_mode: Whether to run in print mode (useful for pipes)
        """
        self.context = context
        self.context.app = self  # Set the app reference in context
        self.agent = agent
        self.input_items: list[TResponseInputItem] = []
        self.current_result: RunResultStreaming | None = None
        self.current_worker: Worker[None] | None = None
        self._session_id_provided = session_id is not None  # Track if continuing session
        self.print_mode = print_mode
        self.message_queue: deque[str] = deque()  # Queue for user messages

        # Initialize session based on settings
        if settings.session.storage_type == "jsonl":
            if session_id is None:
                # Generate a new session ID based on current date/time
                import datetime

                session_id = f"chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

            self.session = JSONLSession(
                session_id=session_id,
                project_path=None,  # Will use current working directory
                base_dir=settings.session.base_dir,
            )
        else:
            raise NotImplementedError("SQLite session support will be added later")

        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AppFooter()
        with MainScroll(id="messages"):
            yield Welcome()

    async def on_mount(self) -> None:
        """Called when the app is mounted."""
        # Load session history if we're continuing from a previous session
        if self._session_id_provided:
            await self.load_session_history()

    def extract_text_from_content(self, content: list[Content]) -> str:
        """Extract text from various content formats."""
        return TextExtractor.extract_from_content(content)

    async def add_message(self, message: BaseMessage) -> None:
        """Add a message widget to the main scroll area.

        Args:
            message: The message to add
        """
        main_scroll = self.query_one("#messages", MainScroll)
        await main_scroll.mount(message)

    async def handle_agent_message(self, message: BaseMessage) -> None:
        """Add a message widget to the main scroll area."""
        await self.add_message(message)

    async def handle_agent_update(self, new_agent: Agent) -> None:
        """Handle agent updates."""
        log(f"Agent updated: {new_agent.name}")
        self.agent = new_agent

    async def handle_agent_error(self, error: Exception) -> None:
        """Handle errors during streaming."""
        log(f"Error during agent response: {type(error).__name__}: {error!s}")

        # Create an error message for the user
        error_msg = f"❌ Error: {type(error).__name__}"
        if str(error):
            error_msg += f"\n\n{error!s}"

        error_msg += f"\n\n```\n{traceback.format_exc()}\n```"

        # Display the error to the user
        # TODO(serialx): Use a dedicated error message widget
        error_agent_msg = AgentMessage(error_msg, status=MessageStatus.ERROR)
        await self.add_message(error_agent_msg)

    async def handle_agent_finished(self) -> None:
        """Handle when the agent has finished processing."""
        # Remove the last agent message if it is still executing (which means the agent run was cancelled)
        main_scroll = self.query_one("#messages", MainScroll)
        try:
            last_message = main_scroll.query_one("BaseMessage:last-child", BaseMessage)
            if last_message.status == MessageStatus.EXECUTING:
                last_message.remove()
        except Exception:
            # No messages to clean up
            pass

    async def load_session_history(self) -> None:
        """Load and display messages from session history."""
        loader = SessionLoader(self.session)
        messages = await loader.load_history()

        # Remove Welcome widget if we have messages
        if messages:
            welcome = self.query_one("#messages").query("Welcome")
            if welcome:
                welcome.first().remove()

        # Add all messages to the UI
        for message in messages:
            await self.add_message(message)

    def watch_agent_status(self, _old_status: AgentStatus, new_status: AgentStatus) -> None:
        """React to agent_status changes."""
        footer = self.query_one(AppFooter)
        if new_status == "running":
            footer.show_loading()
        else:
            footer.hide_loading()

    async def on_my_text_area_user_message(self, event: MyTextArea.UserMessage) -> None:
        """Handle user messages from the text area."""
        if event.text:
            user_message = UserMessage(event.text)
            await self.add_message(user_message)
            user_message.scroll_visible()

            # If agent is running, queue the message
            if self.agent_status == "running":
                self.message_queue.append(event.text)
                log(f"Message queued: {event.text}")
                footer = self.query_one(AppFooter)
                # Update the loading message to show queued messages
                queued_count = len(self.message_queue)
                footer.show_loading(
                    status="Generating…", metadata=f"{queued_count} message{'s' if queued_count > 1 else ''} queued"
                )
            else:
                # Process the message immediately
                result = Runner.run_streamed(
                    self.agent,
                    input=event.text,  # Pass string directly when using session
                    context=self.context,
                    max_turns=settings.max_turns,
                    session=self.session,
                )

                self.current_worker = self.handle_streamed_response(result)

    @work(exclusive=True)
    async def handle_streamed_response(self, result: RunResultStreaming) -> None:
        self.agent_status = "running"
        self.current_result = result

        self.agent_stream_handler = AgentStreamHandler(self)
        await self.agent_stream_handler.process_stream(result)

        self.agent_status = "idle"
        self.current_result = None
        self.current_worker = None

        # Process any queued messages
        await self.process_message_queue()

    async def process_message_queue(self) -> None:
        """Process any messages that were queued while the agent was running."""
        if self.message_queue:
            # Get the next message from the queue
            next_message = self.message_queue.popleft()
            log(f"Processing queued message: {next_message}")

            # Process the message
            result = Runner.run_streamed(
                self.agent,
                input=next_message,
                context=self.context,
                max_turns=settings.max_turns,
                session=self.session,
            )

            self.current_worker = self.handle_streamed_response(result)

    def on_click(self) -> None:
        """Handle focus events."""
        self.query_one("#input-textarea").focus()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

    def action_cancel_agent(self) -> None:
        """Cancel the current agent run."""
        if self.agent_status == "running":
            log("Cancelling agent run")
            if self.current_result:
                self.current_result.cancel()
            if self.current_worker:
                self.current_worker.cancel()

    async def run_print(self, prompt: str | None = None) -> str:
        """Run the agent and return the raw output for printing.

        Args:
            prompt: Optional prompt text. If not provided, reads from stdin.

        Returns:
            The agent's text output as a string
        """
        import sys

        # Use provided prompt or read from stdin
        input_text = prompt.strip() if prompt else sys.stdin.read().strip()

        if not input_text:
            return ""

        # Import needed event types
        from agents import RawResponsesStreamEvent
        from openai.types.responses import ResponseTextDeltaEvent

        # Run the agent
        result = Runner.run_streamed(
            self.agent,
            input=input_text,
            context=self.context,
            max_turns=settings.max_turns,
            session=self.session,
        )

        # Collect all agent text output
        agent_output = ""

        async for event in result.stream_events():
            # Handle text output from agent
            match event:
                case RawResponsesStreamEvent(data=data):
                    match data:
                        case ResponseTextDeltaEvent(delta=delta) if delta:
                            agent_output += delta

        return agent_output.strip()

    async def handle_task_tool_event(self, tool_name: str, tool_call_id: str, event: StreamEvent) -> None:
        """Handle streaming events from task tool sub-agents.

        Args:
            tool_name: Name of the tool (e.g., "task")
            tool_call_id: Unique identifier for this tool call
            event: The streaming event from the sub-agent

        Note: The main app receives this event from the agent's task tool handler.
        """
        await self.agent_stream_handler.handle_task_tool_event(tool_name, tool_call_id, event)
