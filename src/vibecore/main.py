from typing import ClassVar

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
from textual.widgets import Header

from vibecore.agents.default import default_agent
from vibecore.context import VibecoreContext
from vibecore.settings import settings
from vibecore.widgets.core import AppFooter, MainScroll, MyTextArea
from vibecore.widgets.messages import AgentMessage, ToolMessage, UserMessage


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH: ClassVar = ["widgets/core.tcss", "widgets/messages.tcss", "main.tcss"]
    BINDINGS: ClassVar = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def __init__(self, context: VibecoreContext, agent: Agent) -> None:
        """Initialize the Vibecore app with context and agent."""
        self.context = context
        self.agent = agent
        self.input_items: list[TResponseInputItem] = []
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AppFooter()
        yield MainScroll(id="messages")

    async def add_message(self, message: UserMessage | AgentMessage | ToolMessage) -> None:
        """Add a message widget to the main scroll area."""
        messages = self.query_one("#messages", MainScroll)
        await messages.mount(message)
        message.scroll_visible()

    async def on_my_text_area_user_message(self, event: MyTextArea.UserMessage) -> None:
        """Handle user messages from the text area."""
        self.input_items.append({"role": "user", "content": event.text})
        user_message = UserMessage(event.text)
        await self.add_message(user_message)

        result = Runner.run_streamed(
            self.agent, input=self.input_items, context=self.context, max_turns=settings.max_turns
        )

        self.handle_streamed_response(result)

    @work(exclusive=True)
    async def handle_streamed_response(self, result: RunResultStreaming) -> None:
        message_content = ""
        agent_message: AgentMessage | None = None
        last_tool_message: ToolMessage | None = None

        async for event in result.stream_events():
            match event:
                case RawResponsesStreamEvent(data=data):
                    match data:
                        case ResponseTextDeltaEvent(delta=delta):
                            message_content += delta
                            if message_content:
                                if not agent_message:
                                    agent_message = AgentMessage(message_content)
                                    await self.add_message(agent_message)
                                else:
                                    agent_message.update(message_content)

                        case ResponseOutputItemDoneEvent(item=item) if isinstance(item, ResponseFunctionToolCall):
                            tool_name = item.name
                            last_tool_message = ToolMessage(tool_name, item.arguments)
                            await self.add_message(last_tool_message)

                case RunItemStreamEvent(item=item):
                    match item:
                        case ToolCallItem():
                            pass
                        case ToolCallOutputItem(output=output):
                            if last_tool_message:
                                log(f"Tool call output detected: {output}")
                                last_tool_message.update("success", output)
                        case MessageOutputItem():
                            agent_message = None
                            message_content = ""

                case AgentUpdatedStreamEvent(new_agent=new_agent):
                    log(f"Agent updated: {new_agent.name}")
                    self.agent = new_agent

        self.input_items = result.to_input_list()

    def on_click(self) -> None:
        """Handle focus events."""
        self.query_one("#input-textarea").focus()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"


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
