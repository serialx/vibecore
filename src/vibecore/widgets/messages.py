from textual import log
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Resize
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Markdown, Static


class MessageHeader(Widget):
    """A widget to display a message header."""

    text: reactive[str] = reactive("")
    status: reactive[str] = reactive("idle")
    _prefix_visible: reactive[bool] = reactive(False, init=False)

    def __init__(self, prefix: str, text: str, status: str = "idle", use_markdown: bool = False, **kwargs) -> None:
        """
        Construct a MessageHeader.

        Args:
            text: The text to display.
            **kwargs: Additional keyword arguments for Static.
        """
        super().__init__(**kwargs)
        self.prefix = prefix
        self.set_reactive(MessageHeader.text, text)
        self.status = status
        self.use_markdown = use_markdown

    def watch_status(self, status: str) -> None:
        """Watch for changes in the status and update classes accordingly."""
        self.set_class(status == "idle", "status-idle")
        self.set_class(status == "executing", "status-executing")
        self.set_class(status == "success", "status-success")
        self.set_class(status == "error", "status-error")
        log(f"Status changed to {status}")

    def watch_text(self, text: str) -> None:
        """Watch for changes in the text and update the header."""
        if self.use_markdown:
            self.query_one(".text", Markdown).update(text)
        else:
            self.query_one(".text", Static).update(text)

    def compose(self) -> ComposeResult:
        """Create child widgets for the message header."""
        yield Static(self.prefix, classes="prefix")
        if self.use_markdown:
            yield Markdown(self.text, classes="text")
        else:
            yield Static(self.text, classes="text")

    def _toggle_cursor_blink_visible(self) -> None:
        """Toggle visibility of the cursor for the purposes of 'cursor blink'."""
        self._prefix_visible = not self._prefix_visible
        log(f"Prefix blink toggled: {self._prefix_visible}")
        self.query_one(".prefix").visible = self._prefix_visible

    def _on_mount(self, event):
        self.blink_timer = self.set_interval(
            0.5,
            self._toggle_cursor_blink_visible,
            pause=(self.status != "executing"),
        )


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
        yield MessageHeader("⏺", self.text, use_markdown=True)

    def update(self, text: str) -> None:
        """Update the text of the agent message."""
        self.text = text
        header = self.query_one(MessageHeader)
        header.text = text



class ToolMessage(Widget):
    """A widget to display tool execution messages."""

    tool_name: reactive[str] = reactive("")
    command: reactive[str] = reactive("")
    output: reactive[str] = reactive("", recompose=True)
    status: reactive[str] = reactive("executing")

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
            lines = self.output.splitlines()
            N = 3
            first_n_lines = lines[:N]
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    yield Static("\n".join(first_n_lines), classes="tool-output-content-excerpt")
                    if len(lines) > N:
                        yield Static(
                            f"… +{len(lines) - N} lines (ctrl+r to expand)", classes="tool-output-content-more"
                        )
