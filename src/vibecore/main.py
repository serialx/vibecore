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
    ResponseOutputItemDoneEvent,
    ResponseTextDeltaEvent,
)
from textual import log, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Header
from textual.worker import Worker

from vibecore.agents.default import default_agent
from vibecore.context import VibecoreContext
from vibecore.settings import settings
from vibecore.widgets.core import AppFooter, MainScroll, MyTextArea
from vibecore.widgets.info import Welcome
from vibecore.widgets.messages import AgentMessage, ToolMessage, UserMessage

AgentStatus = Literal["idle", "running"]


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH: ClassVar = ["widgets/core.tcss", "widgets/messages.tcss", "widgets/info.tcss", "main.tcss"]
    BINDINGS: ClassVar = [
        ("ctrl+shift+d", "toggle_dark", "Toggle dark mode"),
        Binding("escape", "cancel_agent", "Cancel agent", show=False),
    ]

    agent_status = reactive[AgentStatus]("idle")

    def __init__(self, context: VibecoreContext, agent: Agent) -> None:
        """Initialize the Vibecore app with context and agent."""
        self.context = context
        self.agent = agent
        self.input_items: list[TResponseInputItem] = []
        self.current_result: RunResultStreaming | None = None
        self.current_worker: Worker[None] | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AppFooter()
        with MainScroll(id="messages"):
            yield Welcome()

    async def add_message(self, message: UserMessage | AgentMessage | ToolMessage) -> None:
        """Add a message widget to the main scroll area."""
        messages = self.query_one("#messages", MainScroll)
        await messages.mount(message)
        message.scroll_visible()

    def watch_agent_status(self, old_status: AgentStatus, new_status: AgentStatus) -> None:
        """React to agent_status changes."""
        footer = self.query_one(AppFooter)
        if new_status == "running":
            footer.show_loading()
        else:
            footer.hide_loading()

    async def on_my_text_area_user_message(self, event: MyTextArea.UserMessage) -> None:
        """Handle user messages from the text area."""
        if event.text:
            self.input_items.append({"role": "user", "content": event.text})
            user_message = UserMessage(event.text)
            await self.add_message(user_message)

            result = Runner.run_streamed(
                self.agent, input=self.input_items, context=self.context, max_turns=settings.max_turns
            )

            self.current_worker = self.handle_streamed_response(result)

    @work(exclusive=True)
    async def handle_streamed_response(self, result: RunResultStreaming) -> None:
        self.agent_status = "running"
        self.current_result = result
        message_content = ""
        agent_message: AgentMessage | None = None
        last_tool_message: ToolMessage | None = None

        try:
            async for event in result.stream_events():
                match event:
                    case RawResponsesStreamEvent(data=data):
                        match data:
                            case ResponseTextDeltaEvent(delta=delta) if delta:
                                message_content += delta
                                if not agent_message:
                                    agent_message = AgentMessage(message_content, status="executing")
                                    await self.add_message(agent_message)
                                else:
                                    agent_message.update(message_content)

                            case ResponseOutputItemDoneEvent(
                                item=ResponseFunctionToolCall(name=tool_name, arguments=arguments)
                            ):
                                # TODO(serialx): proper implementation for parallel tool calls
                                last_tool_message = ToolMessage(tool_name, arguments)
                                await self.add_message(last_tool_message)

                    case RunItemStreamEvent(item=item):
                        match item:
                            case ToolCallItem():
                                pass
                            case ToolCallOutputItem(output=output):
                                if last_tool_message:
                                    last_tool_message.update("success", str(output))
                            case MessageOutputItem():
                                if agent_message:
                                    agent_message.update(message_content, status="idle")
                                    agent_message = None
                                    message_content = ""

                    case AgentUpdatedStreamEvent(new_agent=new_agent):
                        log(f"Agent updated: {new_agent.name}")
                        self.agent = new_agent

        finally:
            # We save even if the agent run was cancelled or failed
            self.input_items = result.to_input_list()
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


def main() -> None:
    import logging

    from textual.logging import TextualHandler

    logging.basicConfig(
        level="WARNING",
        handlers=[TextualHandler()],
    )

    logger = logging.getLogger("openai.agents")
    logger.addHandler(TextualHandler())

    ctx = VibecoreContext()

    app = VibecoreApp(ctx, default_agent)
    app.run()
