from typing import ClassVar, Literal

from agents import (
    Agent,
    AgentUpdatedStreamEvent,
    MessageOutputItem,
    RawResponsesStreamEvent,
    Runner,
    RunResultStreaming,
    ToolCallItem,
    ToolCallOutputItem,
    TResponseInputItem,
)
from agents.stream_events import (
    RunItemStreamEvent,
)
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputItem,
    ResponseOutputItemDoneEvent,
    ResponseOutputMessage,
    ResponseTextDeltaEvent,
)
from openai.types.responses.response_output_message import Content
from openai.types.responses.response_output_refusal import ResponseOutputRefusal
from openai.types.responses.response_output_text import ResponseOutputText
from pydantic import TypeAdapter
from textual import log, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Header
from textual.worker import Worker

from vibecore.context import VibecoreContext
from vibecore.session import JSONLSession
from vibecore.settings import settings
from vibecore.widgets.core import AppFooter, MainScroll, MyTextArea
from vibecore.widgets.info import Welcome
from vibecore.widgets.messages import AgentMessage, BaseMessage, MessageStatus, ToolMessage, UserMessage

AgentStatus = Literal["idle", "running"]


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH: ClassVar = ["widgets/core.tcss", "widgets/messages.tcss", "widgets/info.tcss", "main.tcss"]
    BINDINGS: ClassVar = [
        ("ctrl+shift+d", "toggle_dark", "Toggle dark mode"),
        Binding("escape", "cancel_agent", "Cancel agent", show=False),
    ]

    agent_status = reactive[AgentStatus]("idle")

    def __init__(self, context: VibecoreContext, agent: Agent, session_id: str | None = None) -> None:
        """Initialize the Vibecore app with context and agent.

        Args:
            context: The VibecoreContext instance
            agent: The Agent instance to use
            session_id: Optional session ID to load existing session
        """
        self.context = context
        self.agent = agent
        self.input_items: list[TResponseInputItem] = []
        self.current_result: RunResultStreaming | None = None
        self.current_worker: Worker[None] | None = None
        self._session_id_provided = session_id is not None  # Track if continuing session

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
        """Extract text from various content formats, inspired by ItemHelpers.text_message_output."""
        # Extract text from content array format (similar to ItemHelpers logic)
        text_parts = []
        for item in content:
            match item:
                case ResponseOutputText(text=text):
                    text_parts.append(text)
                case ResponseOutputRefusal(refusal=text):
                    text_parts.append(text)
        return "".join(text_parts)

    async def add_message(self, message: UserMessage | AgentMessage | ToolMessage) -> None:
        """Add a message widget to the main scroll area."""
        messages = self.query_one("#messages", MainScroll)
        await messages.mount(message)

    async def load_session_history(self) -> None:
        """Load and display messages from session history."""
        # Get all items from the session
        session_items = await self.session.get_items()

        # Remove the Welcome widget if present
        if session_items:
            welcome = self.query_one("#messages").query("Welcome")
            if welcome:
                welcome.first().remove()

        # Process each item - some will convert to output items, others we'll handle directly
        adapter = TypeAdapter(ResponseOutputItem)
        tool_calls_pending: dict[str, tuple[str, str]] = {}  # Track pending tool calls by ID

        for item in session_items:
            # Try to convert to output item first
            try:
                output_item = adapter.validate_python(item)

                match output_item:
                    case ResponseOutputMessage(role="user", content=content):
                        # User message
                        text_content = self.extract_text_from_content(content)
                        user_msg = UserMessage(text_content)
                        await self.add_message(user_msg)

                    case ResponseOutputMessage(role="assistant", content=content):
                        # Handle assistant messages
                        text_content = self.extract_text_from_content(content)
                        if text_content:
                            # If agent decides to immediately tool call, we often have no text content
                            agent_msg = AgentMessage(text_content, status=MessageStatus.IDLE)
                            await self.add_message(agent_msg)

                    case ResponseFunctionToolCall(call_id=call_id, name=name, arguments=arguments) if call_id:
                        log(f"Tool call: {name} with arguments: {arguments}")
                        # Tool call - store for matching with output
                        tool_calls_pending[call_id] = (name, str(arguments))

                    case _:
                        # Log unknown output item types for debugging
                        log(f"Unknown output item type: {type(output_item).__name__}")

            except Exception:
                # If it's not a valid output item, handle it as an input-only item
                if isinstance(item, dict):
                    match item:
                        case {"role": "user", "content": content}:
                            # User message input (EasyInputMessageParam is not convertible to ResponseOutputMessage)
                            text_content = str(content) if isinstance(content, list) else content
                            user_msg = UserMessage(text_content)
                            await self.add_message(user_msg)
                        case {"type": "function_call_output", "call_id": call_id, "output": output}:
                            # Tool output - check if we have a pending call
                            if call_id and call_id in tool_calls_pending:
                                tool_name, command = tool_calls_pending.pop(call_id)

                                # Determine status based on output
                                output_str = str(output) if output else ""
                                status = MessageStatus.SUCCESS

                                tool_msg = ToolMessage(
                                    tool_name=tool_name,
                                    command=command,
                                    output=output_str,
                                    status=status,
                                )
                                await self.add_message(tool_msg)
                        case _:
                            # Log unhandled input items
                            log(f"Unhandled session item: {item}")

        if tool_calls_pending:
            raise RuntimeError(f"Pending tool calls without outputs found: {tool_calls_pending}")

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
        message_content = ""
        agent_message: AgentMessage | None = None
        tool_messages: dict[str, ToolMessage] = {}  # Track multiple tool messages by call_id

        try:
            async for event in result.stream_events():
                match event:
                    case RawResponsesStreamEvent(data=data):
                        match data:
                            case ResponseTextDeltaEvent(delta=delta) if delta:
                                message_content += delta
                                if not agent_message:
                                    agent_message = AgentMessage(message_content, status=MessageStatus.EXECUTING)
                                    await self.add_message(agent_message)
                                else:
                                    agent_message.update(message_content)

                            case ResponseOutputItemDoneEvent(
                                item=ResponseFunctionToolCall(name=tool_name, arguments=arguments, call_id=call_id)
                            ):
                                # Create and track tool message by its call_id
                                tool_message = ToolMessage(tool_name, command=arguments)
                                tool_messages[call_id] = tool_message
                                await self.add_message(tool_message)

                    case RunItemStreamEvent(item=item):
                        match item:
                            case ToolCallItem():
                                pass
                            case ToolCallOutputItem(output=output, raw_item=raw_item):
                                # Find the corresponding tool message by call_id
                                if (
                                    isinstance(raw_item, dict)
                                    and "call_id" in raw_item
                                    and raw_item["call_id"] in tool_messages
                                ):
                                    tool_messages[raw_item["call_id"]].update(MessageStatus.SUCCESS, str(output))
                            case MessageOutputItem():
                                if agent_message:
                                    agent_message.update(message_content, status=MessageStatus.IDLE)
                                    agent_message = None
                                    message_content = ""

                    case AgentUpdatedStreamEvent(new_agent=new_agent):
                        log(f"Agent updated: {new_agent.name}")
                        self.agent = new_agent

        except Exception as e:
            # Log the error
            log(f"Error during agent response: {type(e).__name__}: {e!s}")

            # Create an error message for the user
            error_msg = f"❌ Error: {type(e).__name__}"
            if str(e):
                error_msg += f"\n\n{e!s}"

            # Display the error to the user
            # TODO(serialx): Proper way to handle errors should be attaching error message to the last user message
            error_agent_msg = AgentMessage(error_msg, status=MessageStatus.ERROR)
            await self.add_message(error_agent_msg)
        finally:
            # Remove the last agent message if it is still executing (which means the agent run was cancelled)
            messages = self.query_one("#messages", MainScroll)
            last_message = messages.query_one("BaseMessage:last-child", BaseMessage)
            if last_message.status == MessageStatus.EXECUTING:
                last_message.remove()

            self.agent_status = "idle"
            self.current_result = None
            self.current_worker = None

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
