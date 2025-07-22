from enum import StrEnum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Markdown, Static


class MessageStatus(StrEnum):
    """Status values for messages."""

    IDLE = "idle"
    EXECUTING = "executing"
    SUCCESS = "success"
    ERROR = "error"


class MessageHeader(Widget):
    """A widget to display a message header."""

    text: reactive[str] = reactive("")
    status: reactive[MessageStatus] = reactive(MessageStatus.IDLE)
    _prefix_visible: reactive[bool] = reactive(False, init=False)

    def __init__(
        self, prefix: str, text: str, status: MessageStatus = MessageStatus.IDLE, use_markdown: bool = False, **kwargs
    ) -> None:
        """
        Construct a MessageHeader.

        Args:
            text: The text to display.
            **kwargs: Additional keyword arguments for Static.
        """
        super().__init__(**kwargs)
        self.prefix = prefix
        self.set_reactive(MessageHeader.text, text)
        self.set_reactive(MessageHeader.status, status)
        self._update_status_class(status)
        self.use_markdown = use_markdown

    def _update_status_class(self, status: MessageStatus) -> None:
        """Update the status class based on the current status."""
        self.set_class(status == MessageStatus.IDLE, "status-idle")
        self.set_class(status == MessageStatus.EXECUTING, "status-executing")
        self.set_class(status == MessageStatus.SUCCESS, "status-success")
        self.set_class(status == MessageStatus.ERROR, "status-error")

    def watch_status(self, status: MessageStatus) -> None:
        """Watch for changes in the status and update classes accordingly."""
        self._update_status_class(status)
        if status == MessageStatus.EXECUTING:
            self.blink_timer.resume()
        else:
            self._prefix_visible = True
            self.blink_timer.pause()

    def watch_text(self, text: str) -> None:
        """Watch for changes in the text and update the header."""
        if self.use_markdown:
            self.query_one(".text", Markdown).update(text)
        else:
            self.query_one(".text", Static).update(text)

    def watch__prefix_visible(self, visible: bool) -> None:
        """Watch for changes in the prefix visibility."""
        self.query_one(".prefix").visible = visible

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
        # self.query_one(".prefix").visible = self._prefix_visible

    def _on_mount(self, event) -> None:
        self.blink_timer = self.set_interval(
            0.5,
            self._toggle_cursor_blink_visible,
            pause=(self.status != "executing"),
        )


class BaseMessage(Widget):
    """Base class for all message widgets."""

    status: reactive[MessageStatus] = reactive(MessageStatus.IDLE)

    def __init__(self, status: MessageStatus = MessageStatus.IDLE, **kwargs) -> None:
        """
        Construct a BaseMessage.

        Args:
            status: The status of the message.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(**kwargs)
        self.set_reactive(BaseMessage.status, status)
        self.add_class("message")

    def get_header_params(self) -> tuple[str, str, bool]:
        """
        Get parameters for MessageHeader.

        Returns:
            A tuple of (prefix, text, use_markdown).
        """
        raise NotImplementedError("Subclasses must implement get_header_params")

    def compose(self) -> ComposeResult:
        """Create child widgets for the message."""
        prefix, text, use_markdown = self.get_header_params()
        yield MessageHeader(prefix, text, status=self.status, use_markdown=use_markdown)

    def watch_status(self, status: MessageStatus) -> None:
        """Watch for changes in the status and update classes accordingly."""
        self.query_one(MessageHeader).status = status


class UserMessage(BaseMessage):
    """A widget to display user messages."""

    def __init__(self, text: str, status: MessageStatus = MessageStatus.IDLE, **kwargs) -> None:
        """
        Construct a UserMessage.

        Args:
            text: The text to display.
            status: The status of the message.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.text = text

    def get_header_params(self) -> tuple[str, str, bool]:
        """Get parameters for MessageHeader."""
        return (">", self.text, False)


class AgentMessage(BaseMessage):
    """A widget to display agent messages."""

    text: reactive[str] = reactive("")

    def __init__(self, text: str, status: MessageStatus = MessageStatus.IDLE, **kwargs) -> None:
        """
        Construct an AgentMessage.

        Args:
            text: The text to display.
            status: The status of the message.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.set_reactive(AgentMessage.text, text)

    def get_header_params(self) -> tuple[str, str, bool]:
        """Get parameters for MessageHeader."""
        return ("⏺", self.text, True)

    def update(self, text: str, status: MessageStatus | None = None) -> None:
        """Update the text of the agent message."""
        self.text = text
        if status is not None:
            self.status = status

    def watch_text(self, text: str) -> None:
        """Watch for changes in the text and update the header."""
        self.query_one(MessageHeader).text = text


class ToolMessage(BaseMessage):
    """A widget to display tool execution messages."""

    tool_name: reactive[str] = reactive("")
    command: reactive[str] = reactive("")
    output: reactive[str] = reactive("", recompose=True)

    def __init__(
        self, tool_name: str, command: str, output: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs
    ) -> None:
        """
        Construct a ToolMessage.

        Args:
            tool_name: The name of the tool (e.g., "Bash").
            command: The command being executed.
            output: The output from the tool (optional, can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.tool_name = tool_name
        self.command = command
        self.output = output

    def update(self, status: MessageStatus, output: str | None = None) -> None:
        """Update the status and optionally the output of the tool message."""
        self.status = status
        if output is not None:
            self.output = output

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
