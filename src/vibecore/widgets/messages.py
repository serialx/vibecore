from textual import log
from textual.app import ComposeResult
from textual.reactive import Reactive, reactive
from textual.widget import Widget
from textual.widgets import Static


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
