import re
from enum import StrEnum

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Markdown, Static

from .expandable import ExpandableContent, ExpandableMarkdown


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
        max_command_length = 60
        display_command = (
            self.command[:max_command_length] + "…" if len(self.command) > max_command_length else self.command
        )

        # Header line
        header = f"{self.tool_name}({display_command})"
        yield MessageHeader("⏺", header, status=self.status)

        # # Output lines (only show if we have output)
        if self.output:
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    yield ExpandableContent(self.output, truncated_lines=3, classes="tool-output-expandable")


class PythonToolMessage(BaseMessage):
    """A widget to display Python code execution messages."""

    code: reactive[str] = reactive("")
    output: reactive[str] = reactive("", recompose=True)

    def __init__(self, code: str, output: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs) -> None:
        """
        Construct a PythonToolMessage.

        Args:
            code: The Python code being executed.
            output: The output from the execution (optional, can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.code = code
        self.output = output

    def update(self, status: MessageStatus, output: str | None = None) -> None:
        """Update the status and optionally the output of the Python execution."""
        self.status = status
        if output is not None:
            self.output = output

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.has_class("copy-button"):
            # Copy the Python code to clipboard
            self.app.copy_to_clipboard(self.code)

    def compose(self) -> ComposeResult:
        """Create child widgets for the Python execution message."""
        # Header line
        yield MessageHeader("⏺", "Python", status=self.status)

        # Python code display
        with Horizontal(classes="python-code"):
            yield Static("└─", classes="python-code-prefix")
            yield Button("Copy", classes="copy-button", variant="primary")
            with Vertical(classes="python-code-content code-container"):
                # Use ExpandableMarkdown for code display
                yield ExpandableMarkdown(
                    self.code, language="python", truncated_lines=8, classes="python-code-expandable"
                )

        # Output (only show if we have output)
        if self.output:
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    yield ExpandableContent(self.output, truncated_lines=5, classes="tool-output-expandable")


class ReadToolMessage(BaseMessage):
    """A widget to display file read operations with collapsible content."""

    file_path: reactive[str] = reactive("")
    content: reactive[str] = reactive("", recompose=True)
    line_count: reactive[int] = reactive(0, recompose=True)

    line_number_pattern_ = re.compile(r"^\s*\d+\t", re.MULTILINE)

    def __init__(
        self, file_path: str, content: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs
    ) -> None:
        """
        Construct a ReadToolMessage.

        Args:
            file_path: The file path being read.
            content: The file content (can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.file_path = file_path
        self.content = content
        self.line_count = len(content.splitlines()) if content else 0

    def update(self, status: MessageStatus, content: str | None = None) -> None:
        """Update the status and optionally the content of the read operation."""
        self.status = status
        if content is not None:
            self.content = content
            self.line_count = len(content.splitlines())

    def compose(self) -> ComposeResult:
        """Create child widgets for the read message."""
        # Truncate file path if too long
        max_path_length = 60
        display_path = (
            self.file_path[:max_path_length] + "…" if len(self.file_path) > max_path_length else self.file_path
        )

        # Header line
        header = f"Read({display_path})"
        yield MessageHeader("⏺", header, status=self.status)

        # Content display based on status
        if self.status == MessageStatus.SUCCESS and self.content:
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    # Remove cat -n style line numbers from content for display
                    clean_content = self.line_number_pattern_.sub("", self.content)
                    # Use ExpandableContent with custom collapsed text
                    yield ExpandableContent(
                        Content(clean_content),
                        collapsed_text=f"Read [b]{self.line_count}[/b] lines (view)",
                        classes="read-expandable",
                    )


class TodoWriteToolMessage(BaseMessage):
    """A widget to display todo list updates."""

    todos: reactive[list[dict[str, str]]] = reactive([], recompose=True)
    output: reactive[str] = reactive("", recompose=True)

    def __init__(
        self, todos: list[dict[str, str]], output: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs
    ) -> None:
        """
        Construct a TodoWriteToolMessage.

        Args:
            todos: The list of todos being written.
            output: The output from the tool (optional, can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.todos = todos
        self.output = output

    def update(self, status: MessageStatus, output: str | None = None) -> None:
        """Update the status and optionally the output of the todo write operation."""
        self.status = status
        if output is not None:
            self.output = output

    def compose(self) -> ComposeResult:
        """Create child widgets for the todo write message."""
        # Header line
        yield MessageHeader("⏺", "TodoWrite", status=self.status)

        # Todo list display
        if self.todos:
            with Horizontal(classes="todo-list"):
                yield Static("└─", classes="todo-list-prefix")
                with Vertical(classes="todo-list-content"):
                    # Display all todos in a single list
                    for todo in self.todos:
                        status = todo.get("status", "pending")
                        icon = "☒" if status == "completed" else "☐"
                        yield Static(f"{icon} {todo.get('content', '')}", classes=f"todo-item {status}")
