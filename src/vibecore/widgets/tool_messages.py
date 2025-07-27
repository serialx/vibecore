"""Tool-specific message widgets for vibecore.

This module contains specialized message widgets for displaying
the execution and results of various tools.
"""

import difflib
import json
import re

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Button, Static

from .expandable import ExpandableContent, ExpandableMarkdown
from .messages import BaseMessage, MessageHeader, MessageStatus


class BaseToolMessage(BaseMessage):
    """Base class for all tool execution messages."""

    output: reactive[str] = reactive("", recompose=True)

    def update(self, status: MessageStatus, output: str | None = None) -> None:
        """Update the status and optionally the output of the tool message."""
        self.status = status
        if output is not None:
            self.output = output

    def _render_output(
        self, output, truncated_lines: int = 3, collapsed_text: str | Content | None = None
    ) -> ComposeResult:
        """Render the output section if output exists."""
        if output:
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    yield ExpandableContent(
                        output,
                        truncated_lines=truncated_lines,
                        classes="tool-output-expandable",
                        collapsed_text=collapsed_text,
                    )


class ToolMessage(BaseToolMessage):
    """A widget to display generic tool execution messages."""

    tool_name: reactive[str] = reactive("")
    command: reactive[str] = reactive("")

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

        # Output lines
        yield from self._render_output(self.output, truncated_lines=3)


class PythonToolMessage(BaseToolMessage):
    """A widget to display Python code execution messages."""

    code: reactive[str] = reactive("")

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

        # Output
        yield from self._render_output(self.output, truncated_lines=5)


class ReadToolMessage(BaseToolMessage):
    """A widget to display file read operations with collapsible content."""

    file_path: reactive[str] = reactive("")
    content: reactive[str] = reactive("", recompose=True)

    _LINE_NUMBER_PATTERN = re.compile(r"^\s*\d+\t", re.MULTILINE)

    def __init__(
        self, file_path: str, output: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs
    ) -> None:
        """
        Construct a ReadToolMessage.

        Args:
            file_path: The file path being read.
            output: The output from the read operation (can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.file_path = file_path
        self.output = output

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

        clean_output = self._LINE_NUMBER_PATTERN.sub("", self.output)
        line_count = len(self.output.splitlines()) if self.output else 0
        collapsed_text = f"Read [b]{line_count}[/b] lines (view)"

        yield from self._render_output(clean_output, truncated_lines=0, collapsed_text=collapsed_text)


class TaskToolMessage(BaseToolMessage):
    """A widget to display task execution messages."""

    description: reactive[str] = reactive("")
    prompt: reactive[str] = reactive("")

    def __init__(
        self, description: str, prompt: str, output: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs
    ) -> None:
        """
        Construct a TaskToolMessage.

        Args:
            description: Short task description.
            prompt: Full task instructions.
            output: The output from the task execution (optional, can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.description = description
        self.prompt = prompt
        self.output = output

    def compose(self) -> ComposeResult:
        """Create child widgets for the task message."""
        # Header line
        header = f"Task({self.description})"
        yield MessageHeader("⏺", header, status=self.status)

        # Show prompt if available and status is executing
        if self.prompt and self.status == MessageStatus.EXECUTING:
            with Horizontal(classes="task-prompt"):
                yield Static("└─", classes="task-prompt-prefix")
                with Vertical(classes="task-prompt-content"):
                    yield ExpandableContent(
                        self.prompt,
                        truncated_lines=5,
                        classes="task-prompt-expandable",
                    )

        # Output lines
        yield from self._render_output(self.output, truncated_lines=5)


class TodoWriteToolMessage(BaseToolMessage):
    """A widget to display todo list updates."""

    todos: reactive[list[dict[str, str]]] = reactive([], recompose=True)

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


class WriteToolMessage(BaseToolMessage):
    """A widget to display file write operations with markdown content viewer."""

    file_path: reactive[str] = reactive("")
    content: reactive[str] = reactive("", recompose=True)

    def __init__(
        self, file_path: str, content: str, output: str = "", status: MessageStatus = MessageStatus.EXECUTING, **kwargs
    ) -> None:
        """
        Construct a WriteToolMessage.

        Args:
            file_path: The file path being written to.
            content: The content being written.
            output: The output from the write operation (can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.file_path = file_path
        self.content = content
        self.output = output

    def compose(self) -> ComposeResult:
        """Create child widgets for the write message."""
        # Truncate file path if too long
        max_path_length = 60
        display_path = (
            self.file_path[:max_path_length] + "…" if len(self.file_path) > max_path_length else self.file_path
        )

        # Header line
        header = f"Write({display_path})"
        yield MessageHeader("⏺", header, status=self.status)

        # Content display with markdown support
        if self.content:
            with Horizontal(classes="write-content"):
                yield Static("└─", classes="write-content-prefix")
                with Vertical(classes="write-content-body"):
                    yield ExpandableContent(
                        Content(self.content), truncated_lines=10, classes="write-content-expandable"
                    )

        # Output (success/error message)
        if self.output:
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    yield Static(self.output, classes="write-output-message")


class EditToolMessage(BaseToolMessage):
    """A widget to display file edit operations with diff view."""

    file_path: reactive[str] = reactive("")
    arguments: reactive[str] = reactive("")
    diff_content: reactive[str] = reactive("", recompose=True)

    def __init__(
        self,
        file_path: str,
        arguments: str,
        output: str = "",
        status: MessageStatus = MessageStatus.EXECUTING,
        **kwargs,
    ) -> None:
        """
        Construct an EditToolMessage.

        Args:
            file_path: The file path being edited.
            arguments: The JSON arguments containing edit operations.
            output: The output from the edit operation (can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.file_path = file_path
        self.arguments = arguments
        self.output = output
        self._generate_diff()

    def _generate_diff(self) -> None:
        """Generate unified diff from the edit arguments."""
        try:
            args = json.loads(self.arguments)

            # Handle both single edit and multi_edit
            if "old_string" in args and "new_string" in args:
                # Single edit
                edits = [(args["old_string"], args["new_string"])]
            elif "edits" in args:
                # Multi edit
                edits = [(edit["old_string"], edit["new_string"]) for edit in args["edits"]]
            else:
                self.diff_content = ""
                return

            # Generate unified diff for each edit
            diff_parts = []
            for i, (old_string, new_string) in enumerate(edits):
                old_lines = old_string.splitlines(keepends=True)
                new_lines = new_string.splitlines(keepends=True)

                # Create diff
                diff = difflib.unified_diff(
                    old_lines,
                    new_lines,
                    fromfile=f"{self.file_path} (before)",
                    tofile=f"{self.file_path} (after)",
                    n=3,  # Number of context lines
                    lineterm="",
                )

                diff_text = "".join(diff)
                if diff_text:
                    if len(edits) > 1:
                        diff_parts.append(f"Edit {i + 1}:\n{diff_text}")
                    else:
                        diff_parts.append(diff_text)

            self.diff_content = "\n\n".join(diff_parts) if diff_parts else "No changes"

        except (json.JSONDecodeError, KeyError):
            self.diff_content = ""

    def update(self, status: MessageStatus, output: str | None = None) -> None:
        """Update the status and optionally the output of the tool message."""
        super().update(status, output)
        # Regenerate diff if arguments changed
        if hasattr(self, "_last_arguments") and self._last_arguments != self.arguments:
            self._generate_diff()
        self._last_arguments = self.arguments

    def compose(self) -> ComposeResult:
        """Create child widgets for the edit message."""
        # Truncate file path if too long
        max_path_length = 60
        display_path = (
            self.file_path[:max_path_length] + "…" if len(self.file_path) > max_path_length else self.file_path
        )

        # Header line
        header = f"Edit({display_path})"
        yield MessageHeader("⏺", header, status=self.status)

        # Diff display
        if self.diff_content:
            with Horizontal(classes="edit-diff"):
                yield Static("└─", classes="edit-diff-prefix")
                with Vertical(classes="edit-diff-content code-container"):
                    # Use ExpandableMarkdown for diff display with syntax highlighting
                    yield ExpandableMarkdown(
                        f"```diff\n{self.diff_content}\n```", truncated_lines=15, classes="edit-diff-expandable"
                    )

        # Output (success/error message)
        if self.output:
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    yield Static(self.output, classes="edit-output-message")
