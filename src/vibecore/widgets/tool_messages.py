"""Tool-specific message widgets for vibecore.

This module contains specialized message widgets for displaying
the execution and results of various tools.
"""

import json
import re
from typing import TYPE_CHECKING

from agents import Agent, StreamEvent
from textual import log
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.reactive import reactive
from textual.widgets import Button, Static

from vibecore.widgets.core import MainScroll

from .expandable import ExpandableContent, ExpandableMarkdown
from .messages import AgentMessage, BaseMessage, MessageHeader, MessageStatus

if TYPE_CHECKING:
    from vibecore.handlers.stream_handler import AgentStreamHandler


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
                        Content(output),
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

    description: reactive[str] = reactive("", recompose=True)
    prompt: reactive[str] = reactive("", recompose=True)

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
        self._agent_stream_handler: AgentStreamHandler | None = None
        self.main_scroll = MainScroll(id="messages")

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

        # XXX(serialx): self.output being a recompose=True field means whenever self.output changes, main_scroll will be
        #               emptied. So let's just hide it for now.
        # TODO(serialx): Turn all recompose=True fields into TCSS display: none toggle to avoid this issue.
        if not self.output:
            with Horizontal(classes="message-content"):
                yield Static("└─", classes="message-content-prefix")
                with Vertical(classes="message-content-body"):
                    log(f"self id: {id(self)}")
                    log(f"self.main_scroll(id: {id(self.main_scroll)}): {self.main_scroll}")
                    yield self.main_scroll

        # Output lines
        yield from self._render_output(self.output, truncated_lines=5)

    async def handle_task_tool_event(self, event: StreamEvent) -> None:
        """Handle task tool events from the agent.
        Note: This is called by the main app's AgentStreamHandler to process tool events.
        """
        # Create handler lazily to avoid circular import
        if self._agent_stream_handler is None:
            from vibecore.handlers.stream_handler import AgentStreamHandler

            self._agent_stream_handler = AgentStreamHandler(self)

        await self._agent_stream_handler.handle_event(event)

    async def add_message(self, message: BaseMessage) -> None:
        """Add a message widget to the main scroll area.

        Args:
            message: The message to add
        """
        await self.main_scroll.mount(message)

    async def handle_agent_message(self, message: BaseMessage) -> None:
        """Add a message widget to the main scroll area."""
        await self.add_message(message)

    async def handle_agent_update(self, new_agent: Agent) -> None:
        """Handle agent updates."""
        pass

    async def handle_agent_error(self, error: Exception) -> None:
        """Handle errors during streaming."""
        log(f"Error during task agent response: {type(error).__name__}: {error!s}")

        # Create an error message for the user
        error_msg = f"❌ Error: {type(error).__name__}"
        if str(error):
            error_msg += f"\n\n{error!s}"

        # Display the error to the user
        # TODO(serialx): Use a dedicated error message widget
        error_agent_msg = AgentMessage(error_msg, status=MessageStatus.ERROR)
        await self.add_message(error_agent_msg)

    async def handle_agent_finished(self) -> None:
        """Handle when the agent has finished processing."""
        # Remove the last agent message if it is still executing (which means the agent run was cancelled)
        main_scroll = self.query_one("#messages", MainScroll)
        try:
            last_message = main_scroll.query_one("BaseMessage:last-child", BaseMessage)
            if last_message.status == MessageStatus.EXECUTING:
                last_message.remove()
        except Exception:
            # No messages to clean up
            pass


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


class MCPToolMessage(BaseToolMessage):
    """A widget to display MCP tool execution messages."""

    server_name: reactive[str] = reactive("")
    tool_name: reactive[str] = reactive("")
    arguments: reactive[str] = reactive("")

    def __init__(
        self,
        server_name: str,
        tool_name: str,
        arguments: str,
        output: str = "",
        status: MessageStatus = MessageStatus.EXECUTING,
        **kwargs,
    ) -> None:
        """
        Construct an MCPToolMessage.

        Args:
            server_name: The name of the MCP server.
            tool_name: The name of the tool being called.
            arguments: JSON string of tool arguments.
            output: The output from the tool (optional, can be set later).
            status: The status of execution.
            **kwargs: Additional keyword arguments for Widget.
        """
        super().__init__(status=status, **kwargs)
        self.server_name = server_name
        self.tool_name = tool_name
        self.arguments = arguments
        self.output = output

    def _prettify_json_output(self, output: str) -> tuple[bool, str]:
        """Try to prettify JSON output.

        Args:
            output: The raw output string.

        Returns:
            A tuple of (is_json, formatted_output).
        """
        if not output or not output.strip():
            return False, output

        try:
            # Try to parse as JSON
            json_obj = json.loads(output)
            # Pretty print with 2-space indentation
            formatted = json.dumps(json_obj, indent=2, ensure_ascii=False)
            return True, formatted
        except (json.JSONDecodeError, TypeError, ValueError):
            # Not valid JSON, return as-is
            return False, output

    def compose(self) -> ComposeResult:
        """Create child widgets for the MCP tool message."""
        # Header line showing MCP server and tool
        # Access the actual values, not the reactive descriptors
        server_name = self.server_name
        tool_name = self.tool_name
        header = f"MCP[{server_name}]::{tool_name}"
        yield MessageHeader("⏺", header, status=self.status)

        # Arguments display (if any)
        if self.arguments and self.arguments != "{}":
            with Horizontal(classes="mcp-arguments"):
                yield Static("└─", classes="mcp-arguments-prefix")
                with Vertical(classes="mcp-arguments-content"):
                    # Truncate arguments if too long
                    max_args_length = 100
                    display_args = (
                        self.arguments[:max_args_length] + "…"
                        if len(self.arguments) > max_args_length
                        else self.arguments
                    )
                    yield Static(f"Args: {display_args}", classes="mcp-arguments-text")

        # Output - check if it's JSON and prettify if so
        if self.output:
            if json_output := json.loads(self.output):
                assert json_output.get("type") == "text", "Expected JSON output type to be 'text'"
                is_json, processed_output = self._prettify_json_output(json_output.get("text", ""))
            else:
                # output should always be a JSON string, but if not, treat it as plain text
                is_json, processed_output = False, self.output
            with Horizontal(classes="tool-output"):
                yield Static("└─", classes="tool-output-prefix")
                with Vertical(classes="tool-output-content"):
                    if is_json:
                        # Use ExpandableMarkdown for JSON with syntax highlighting
                        yield ExpandableMarkdown(
                            processed_output, language="json", truncated_lines=8, classes="mcp-output-json"
                        )
                    else:
                        # Use ExpandableMarkdown for non-JSON content (renders as markdown without code block)
                        yield ExpandableMarkdown(
                            processed_output, language="", truncated_lines=5, classes="mcp-output-markdown"
                        )
