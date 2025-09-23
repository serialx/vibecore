import os
from enum import StrEnum

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.content import Content
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Markdown, Static


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
            # Use Content to prevent markup interpretation
            self.query_one(".text", Static).update(Content(text))

    def watch__prefix_visible(self, visible: bool) -> None:
        """Watch for changes in the prefix visibility."""
        self.query_one(".prefix").visible = visible

    def compose(self) -> ComposeResult:
        """Create child widgets for the message header."""
        yield Static(self.prefix, classes="prefix")
        if self.use_markdown:
            yield Markdown(self.text, classes="text")
        else:
            # Use Content to prevent markup interpretation of square brackets
            yield Static(Content(self.text), classes="text")

    def _toggle_cursor_blink_visible(self) -> None:
        """Toggle visibility of the cursor for the purposes of 'cursor blink'."""
        self._prefix_visible = not self._prefix_visible
        # self.query_one(".prefix").visible = self._prefix_visible

    def _on_mount(self, event) -> None:
        disable_blink = bool(os.environ.get("TEXTUAL_SNAPSHOT_TEMPDIR"))
        self.blink_timer = self.set_interval(
            0.5,
            self._toggle_cursor_blink_visible,
            pause=(self.status != MessageStatus.EXECUTING) or disable_blink,
        )
        # Ensure the prefix starts visible for executing statuses so snapshot tests
        # and initial renders see the indicator before the first timer tick hides it.
        if self.status == MessageStatus.EXECUTING:
            self._prefix_visible = True


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

    def compose(self) -> ComposeResult:
        """Create child widgets for the agent message."""
        prefix, text, use_markdown = self.get_header_params()
        with Horizontal(classes="agent-message-header"):
            yield MessageHeader(prefix, text, status=self.status, use_markdown=use_markdown)
            yield Button("Copy", classes="copy-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.has_class("copy-button"):
            # Copy the markdown text to clipboard
            self.app.copy_to_clipboard(self.text)

    def update(self, text: str, status: MessageStatus | None = None) -> None:
        """Update the text of the agent message."""
        self.text = text
        if status is not None:
            self.status = status

    def watch_text(self, text: str) -> None:
        """Watch for changes in the text and update the header."""
        self.query_one(MessageHeader).text = text


class SystemMessage(BaseMessage):
    """A widget to display system messages."""

    def __init__(self, text: str, status: MessageStatus = MessageStatus.SUCCESS, **kwargs) -> None:
        """
        Construct a SystemMessage.

        Args:
            text: The text to display.
            status: The status of the message.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.text = text
        self.add_class("system-message")

    def get_header_params(self) -> tuple[str, str, bool]:
        """Get parameters for MessageHeader."""
        return ("!", self.text, False)


class ReasoningMessage(BaseMessage):
    """A widget to display reasoning summaries from AI agents."""

    text: reactive[str] = reactive("")

    def __init__(self, text: str = "", status: MessageStatus = MessageStatus.IDLE, **kwargs) -> None:
        """
        Construct a ReasoningMessage.

        Args:
            text: The reasoning summary text to display.
            status: The status of the message.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.set_reactive(ReasoningMessage.text, text)
        self.add_class("reasoning-message")

    def get_header_params(self) -> tuple[str, str, bool]:
        """Get parameters for MessageHeader."""
        return ("*", self.text, True)

    def update(self, text: str, status: MessageStatus | None = None) -> None:
        """Update the text of the reasoning message."""
        self.text = text
        if status is not None:
            self.status = status

    def watch_text(self, text: str) -> None:
        """Watch for changes in the text and update the header."""
        self.query_one(MessageHeader).text = text
