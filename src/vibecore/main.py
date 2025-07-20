from typing import ClassVar

from textual import log
from textual.app import App, ComposeResult
from textual.widgets import Header

from vibecore.widgets.core import AppFooter, MainScroll, MyTextArea
from vibecore.widgets.messages import AgentMessage, ToolMessage, UserMessage


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH: ClassVar = ["widgets/core.tcss", "widgets/messages.tcss", "main.tcss"]
    BINDINGS: ClassVar = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield AppFooter()
        yield MainScroll(id="messages")

    def on_my_text_area_user_message(self, event: MyTextArea.UserMessage) -> None:
        """Handle user messages from the text area."""
        log(f"User message: {event.text}")
        user_message = UserMessage(event.text)
        self.query_one("#messages").mount(user_message)

        # Example: simulate a tool execution when user types "git commit"
        if "git commit" in event.text.lower():
            # Create tool message in executing state
            tool_msg = ToolMessage(
                tool_name="Bash", command='git commit -m "docs: add CLAUDE.md for Claude Code guidance"'
            )
            self.query_one("#messages").mount(tool_msg)
            tool_msg.scroll_visible()

            agent_message = AgentMessage("Git commiting...")
            self.query_one("#messages").mount(agent_message)
            agent_message.scroll_visible()

            # Simulate execution delay and then show success
            def update_tool_message():
                log("Updating tool message to success state")
                output = (
                    "[main 557a5e2] docs: add CLAUDE.md for Claude Code guidance\n"
                    "1 file changed, 78 insertions(+)\n"
                    "create mode 100644 CLAUDE.md"
                )
                tool_msg.update("success", output)

            log("Setting timer to update tool message")
            self.set_timer(1.0, update_tool_message)
        else:
            agent_message = AgentMessage("Processing your message...")
            self.query_one("#messages").mount(agent_message)
            agent_message.scroll_visible()

    def on_click(self) -> None:
        """Handle focus events."""
        self.query_one("#input-textarea").focus()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"


def main() -> None:
    """Run the StopwatchApp."""
    import logging

    from textual.logging import TextualHandler

    logging.basicConfig(
        level="NOTSET",
        handlers=[TextualHandler()],
    )

    app = VibecoreApp()
    app.run()
