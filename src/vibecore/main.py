import asyncio
import traceback
from collections import deque
from typing import TYPE_CHECKING, ClassVar, Literal

from agents import (
    RunResultStreaming,
    Session,
    StreamEvent,
)
from openai.types.responses.response_output_message import Content
from textual import log, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.selection import Selection
from textual.widget import Widget
from textual.widgets import Header
from textual.worker import Worker

if TYPE_CHECKING:
    from vibecore.flow import TWorkflowReturn, VibecoreTextualRunner

from vibecore.handlers import AgentStreamHandler
from vibecore.session.loader import SessionLoader
from vibecore.utils.text import TextExtractor
from vibecore.widgets.core import AppFooter, MainScroll, MyTextArea
from vibecore.widgets.info import Welcome
from vibecore.widgets.messages import AgentMessage, BaseMessage, MessageStatus, SystemMessage, UserMessage

AgentStatus = Literal["idle", "running", "waiting_user_input"]


class AppIsExiting(Exception):
    pass


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH: ClassVar = [
        "widgets/core.tcss",
        "widgets/messages.tcss",
        "widgets/feedback.tcss",
        "widgets/tool_messages.tcss",
        "widgets/expandable.tcss",
        "widgets/info.tcss",
        "main.tcss",
    ]
    BINDINGS: ClassVar = [
        ("ctrl+shift+d", "toggle_dark", "Toggle dark mode"),
        Binding("escape", "cancel_agent", "Cancel agent", show=False),
        Binding("ctrl+d", "exit_confirm", "Exit", show=False),
    ]

    agent_status = reactive[AgentStatus]("idle")
    _exit_confirmation_active = False
    _exit_confirmation_task: asyncio.Task | None = None

    def __init__(
        self,
        runner: "VibecoreTextualRunner[TWorkflowReturn]",
        show_welcome: bool = True,
    ) -> None:
        """Initialize the Vibecore app with context and agent.

        Args:
            context: The VibecoreContext instance
            agent: The Agent instance to use
            session_id: Optional session ID to load existing session
            show_welcome: Whether to show the welcome message (default: True)
        """
        self.runner = runner
        if runner.context:
            runner.context.app = self  # Set the app reference in context
        self.current_result: RunResultStreaming | None = None
        self.current_worker: Worker[None] | None = None
        self.show_welcome = show_welcome
        self.message_queue: deque[str] = deque()  # Queue for user messages
        self.user_input_event = asyncio.Event()  # Initialize event for user input coordination

        super().__init__()

    def on_mouse_up(self) -> None:
        if not self.screen.selections:
            return None

        widget_text: list[str] = []
        for widget, selection in self.screen.selections.items():
            assert isinstance(widget, Widget) and isinstance(selection, Selection)
            if "copy-button" in widget.classes:  # Skip copy buttons
                continue
            selected_text_in_widget = widget.get_selection(selection)
            if selected_text_in_widget is not None:
                widget_text.extend(selected_text_in_widget)

        selected_text = "".join(widget_text)
        self.copy_to_clipboard(selected_text)
        self.notify("Copied to clipboard")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AppFooter()
        with MainScroll(id="messages") as main_scroll:
            main_scroll.anchor()
            if self.show_welcome:
                yield Welcome()

    def extract_text_from_content(self, content: list[Content]) -> str:
        """Extract text from various content formats."""
        return TextExtractor.extract_from_content(content)

    async def add_message(self, message: BaseMessage) -> None:
        """Add a message widget to the main scroll area.

        Args:
            message: The message to add
        """
        if not self.is_running:
            raise AppIsExiting("App is not running")
        main_scroll = self.query_one("#messages", MainScroll)
        await main_scroll.mount(message)

    async def handle_agent_message(self, message: BaseMessage) -> None:
        """Add a message widget to the main scroll area."""
        await self.add_message(message)

    async def handle_agent_message_update(self, message: BaseMessage) -> None:
        """Message in the widget's message list is updated with new delta or status"""
        pass

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
                # XXX(serialx): Consider marking it as cancelled instead
                # last_message.status = MessageStatus.ERROR
                last_message.remove()
        except Exception:
            # No messages to clean up
            pass

    async def load_session_history(self, session: Session) -> None:
        """Load and display messages from session history."""
        loader = SessionLoader(session)
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

    async def wait_for_user_input(self) -> str:
        """Used in flow mode. See examples/basic_agent.py"""
        if self.message_queue:
            user_input = self.message_queue.popleft()

            user_message = UserMessage(user_input)
            await self.add_message(user_message)
            self.get_child_by_id("messages").scroll_end()

            return user_input

        self.agent_status = "waiting_user_input"
        self.user_input_event.clear()  # Reset the event for next wait
        await self.user_input_event.wait()
        user_input = self.message_queue.popleft()

        user_message = UserMessage(user_input)
        await self.add_message(user_message)
        self.get_child_by_id("messages").scroll_end()

        return user_input

    async def on_my_text_area_user_message(self, event: MyTextArea.UserMessage) -> None:
        """Handle user messages from the text area."""
        if event.text:
            # Check for special commands
            text_strip = event.text.strip()
            if text_strip == "/help":
                help_text = "Available commands:\n"
                help_text += "• /help - Show this help message\n\n"
                help_text += "Keyboard shortcuts:\n"
                help_text += "• Esc - Cancel current agent operation\n"
                help_text += "• Ctrl+Shift+D - Toggle dark/light mode\n"
                help_text += "• Up/Down arrows - Navigate message history\n"
                await self.add_message(SystemMessage(help_text))
                return

            if self.agent_status == "running":
                # If agent is running, queue the message
                self.message_queue.append(event.text)
                log(f"Message queued: {event.text}")
                footer = self.query_one(AppFooter)
                # Update the loading message to show queued messages
                queued_count = len(self.message_queue)
                footer.show_loading(
                    status="Generating…", metadata=f"{queued_count} message{'s' if queued_count > 1 else ''} queued"
                )
            else:
                self.message_queue.append(event.text)
                self.user_input_event.set()

    @work(exclusive=True)
    async def handle_streamed_response(self, result: RunResultStreaming) -> None:
        self.agent_status = "running"
        self.current_result = result

        self.agent_stream_handler = AgentStreamHandler(self)
        await self.agent_stream_handler.process_stream(result)

        # Determine usage based on the last model response rather than the aggregated usage
        # from the entire session so that context fullness reflects the most recent request.
        used_tokens: float = 0.0
        if result.raw_responses:
            last_response = result.raw_responses[-1]
            last_usage = getattr(last_response, "usage", None)
            if last_usage:
                used_tokens = float(last_usage.total_tokens)

        max_ctx = self._get_model_context_window()
        log(f"Context usage: {used_tokens} / {max_ctx} total tokens")
        context_fullness = min(1.0, used_tokens / float(max_ctx))
        footer = self.query_one(AppFooter)
        footer.set_context_progress(context_fullness)

        self.agent_status = "idle"
        self.current_result = None
        self.current_worker = None

    def _get_model_context_window(self) -> int:
        # TODO(serialx): Implement later
        return 200000

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

    async def action_exit_confirm(self) -> None:
        """Handle Ctrl-D press for exit confirmation."""
        if self._exit_confirmation_active:
            # Second Ctrl-D within the timeframe - exit the app
            self.exit()
        else:
            # First Ctrl-D - show confirmation message
            self._exit_confirmation_active = True

            # Cancel any existing confirmation task
            if self._exit_confirmation_task and not self._exit_confirmation_task.done():
                self._exit_confirmation_task.cancel()

            # Show confirmation message
            confirmation_msg = SystemMessage("Press Ctrl-D again to exit")
            await self.add_message(confirmation_msg)

            # Start the 1-second timer
            self._exit_confirmation_task = asyncio.create_task(self._reset_exit_confirmation(confirmation_msg))

    async def _reset_exit_confirmation(self, confirmation_msg: SystemMessage) -> None:
        """Reset exit confirmation after 1 second and remove the message."""
        try:
            # Wait for 1 second
            await asyncio.sleep(2.0)

            # Reset confirmation state
            self._exit_confirmation_active = False

            # Remove the confirmation message
            confirmation_msg.remove()
        except asyncio.CancelledError:
            # Task was cancelled (new Ctrl-D pressed)
            pass

    async def handle_task_tool_event(self, tool_name: str, tool_call_id: str, event: StreamEvent) -> None:
        """Handle streaming events from task tool sub-agents.

        Args:
            tool_name: Name of the tool (e.g., "task")
            tool_call_id: Unique identifier for this tool call
            event: The streaming event from the sub-agent

        Note: The main app receives this event from the agent's task tool handler.
        """
        await self.agent_stream_handler.handle_task_tool_event(tool_name, tool_call_id, event)
