from typing import ClassVar, override

from textual import events, log
from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Footer, Header, Static, TextArea


class MessageHeader(Widget):
    """A widget to display a message header."""

    text: Reactive[str] = reactive("")
    status: Reactive[str] = reactive("idle")

    def __init__(self, prefix: str, text: str, status: str = "idle", **kwargs) -> None:
        """
        Construct a MessageHeader.

        Args:
            text: The text to display.
            **kwargs: Additional keyword arguments for Static.
        """
        super().__init__(**kwargs)
        self.prefix = prefix
        self.text = text
        self.status = status

    def watch_status(self, status: str) -> None:
        """Watch for changes in the status and update classes accordingly."""
        self.set_class(status == "idle", "status-idle")
        self.set_class(status == "executing", "status-executing")
        self.set_class(status == "success", "status-success")
        self.set_class(status == "error", "status-error")
        log(f"Status changed to {status}")

    def compose(self) -> ComposeResult:
        """Create child widgets for the message header."""
        yield Static(self.prefix, classes="prefix")
        yield Static(self.text)


class UserMessage(Widget):
    """A widget to display user messages."""

    def __init__(self, text: str, **kwargs) -> None:
        """
        Construct a UserMessage.

        Args:
            text: The text to display.
            **kwargs: Additional keyword arguments for Static.
        """
        super().__init__(**kwargs)
        self.text = text
        self.add_class("message")

    def compose(self) -> ComposeResult:
        """Create child widgets for the user message."""
        yield MessageHeader(">", self.text)


class AgentMessage(Widget):
    """A widget to display agent messages."""

    def __init__(self, text: str, **kwargs) -> None:
        """
        Construct an AgentMessage.

        Args:
            text: The text to display.
            **kwargs: Additional keyword arguments for Static.
        """
        super().__init__(**kwargs)
        self.text = text
        self.add_class("message")

    def compose(self) -> ComposeResult:
        """Create child widgets for the agent message."""
        yield MessageHeader("⏺", self.text)


class ToolMessage(Widget):
    """A widget to display tool execution messages."""

    tool_name: Reactive[str] = reactive("")
    command: Reactive[str] = reactive("")
    output: Reactive[str] = reactive("", recompose=True)
    status: Reactive[str] = reactive("executing")

    def __init__(self, tool_name: str, command: str, output: str = "", status: str = "executing", **kwargs) -> None:
        """
        Construct a ToolMessage.

        Args:
            tool_name: The name of the tool (e.g., "Bash").
            command: The command being executed.
            output: The output from the tool (optional, can be set later).
            status: The status of execution ("executing", "success", "error").
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.command = command
        self.output = output
        self.set_reactive(ToolMessage.status, status)
        self.add_class("message")

    def update(self, status: str, output: str | None = None) -> None:
        """Update the status and optionally the output of the tool message."""
        self.status = status
        if output is not None:
            self.output = output

    def watch_status(self, status: str) -> None:
        """Watch for changes in the status and update classes accordingly."""
        self.query_one(MessageHeader).status = status

    def compose(self) -> ComposeResult:
        """Create child widgets for the tool message."""
        # Truncate command if too long
        max_command_length = 50
        display_command = (
            self.command[:max_command_length] + "…" if len(self.command) > max_command_length else self.command
        )

        # Header line
        header = f"{self.tool_name}({display_command})"
        yield MessageHeader("⏺", header, status=self.status)

        # # Output lines (only show if we have output)
        if self.output:
            output_lines = self.output.strip().split("\n")
            for i, line in enumerate(output_lines):
                if i == 0:
                    # First line with special character
                    NO_BREAK_SPACE = "\u00a0"  # Non-breaking space
                    yield Static(f"  ⎿{NO_BREAK_SPACE} {line}", classes="tool-output-first")
                else:
                    # Subsequent lines with more indentation
                    yield Static(f"     {line}", classes="tool-output")


class MyFooter(Widget):
    def compose(self) -> ComposeResult:
        yield InputBox()
        yield Footer()


class MyTextArea(TextArea):
    class UserMessage(Message):
        """A user message input."""

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

        def __repr__(self) -> str:
            return f"UserMessage(text={self.text!r})"

    @override
    async def _on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.post_message(self.UserMessage(self.text))
            self.text = ""
            event.prevent_default()

        self._restart_blink()

        if self.read_only:
            return

        key = event.key
        insert_values = {
            "shift+enter": "\n",
            # Ghostty with config: keybind = shift+enter=text:\n
            "ctrl+j": "\n",
        }
        if self.tab_behavior == "indent":
            if key == "escape":
                event.stop()
                event.prevent_default()
                self.screen.focus_next()
                return
            if self.indent_type == "tabs":
                insert_values["tab"] = "\t"
            else:
                insert_values["tab"] = " " * self._find_columns_to_next_tab_stop()

        if event.is_printable or key in insert_values:
            event.stop()
            event.prevent_default()
            insert = insert_values.get(key, event.character)
            # `insert` is not None because event.character cannot be
            # None because we've checked that it's printable.
            assert insert is not None
            start, end = self.selection
            self._replace_via_keyboard(insert, start, end)


class InputBox(Widget):
    """A simple input box widget."""

    def compose(self) -> ComposeResult:
        """Create child widgets for the input box."""
        log("InputBox compose")
        log(TextArea.__init__.__doc__)
        text_area = MyTextArea(compact=True, id="input-textarea")
        yield Static(">", id="input-label")
        yield text_area


class MainScroll(ScrollableContainer):
    """A container with vertical layout and an automatic scrollbar on the Y axis."""


class VibecoreApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = "main.tcss"
    BINDINGS: ClassVar = [
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield MyFooter()
        # yield Footer()
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
