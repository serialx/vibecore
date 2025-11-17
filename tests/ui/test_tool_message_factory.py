"""Tests for the tool message factory."""

import json

from vibecore.widgets.messages import MessageStatus
from vibecore.widgets.tool_message_factory import create_tool_message
from vibecore.widgets.tool_messages import (
    MCPToolMessage,
    PythonToolMessage,
    ReadToolMessage,
    TodoWriteToolMessage,
    ToolMessage,
    WriteToolMessage,
)


class TestToolMessageFactory:
    """Test cases for create_tool_message factory function."""

    def test_create_python_tool_message(self):
        """Test creating PythonToolMessage."""
        code = "print('Hello, World!')"
        arguments = json.dumps({"code": code})

        # Test without output
        message = create_tool_message("execute_python", arguments)
        assert isinstance(message, PythonToolMessage)
        assert message.code == code
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "Hello, World!"
        message_with_output = create_tool_message(
            "execute_python", arguments, output=output, status=MessageStatus.SUCCESS
        )
        assert isinstance(message_with_output, PythonToolMessage)
        assert message_with_output.code == code
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_create_todo_write_tool_message(self):
        """Test creating TodoWriteToolMessage."""
        todos = [{"id": "1", "content": "Test task", "status": "pending", "priority": "high"}]
        arguments = json.dumps({"todos": todos})

        # Test without output
        message = create_tool_message("todo_write", arguments)
        assert isinstance(message, TodoWriteToolMessage)
        assert message.todos == todos
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "Todos updated successfully"
        message_with_output = create_tool_message("todo_write", arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, TodoWriteToolMessage)
        assert message_with_output.todos == todos
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_create_read_tool_message(self):
        """Test creating ReadToolMessage."""
        file_path = "/path/to/file.txt"
        arguments = json.dumps({"file_path": file_path})

        # Test without output
        message = create_tool_message("read", arguments)
        assert isinstance(message, ReadToolMessage)
        assert message.file_path == file_path
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "File contents here"
        message_with_output = create_tool_message("read", arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, ReadToolMessage)
        assert message_with_output.file_path == file_path
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_create_write_tool_message(self):
        """Test creating WriteToolMessage."""
        file_path = "/path/to/newfile.py"
        content = "def hello():\n    print('Hello, World!')"
        arguments = json.dumps({"file_path": file_path, "content": content})

        # Test without output
        message = create_tool_message("write", arguments)
        assert isinstance(message, WriteToolMessage)
        assert message.file_path == file_path
        assert message.content == content
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "Successfully wrote 42 bytes to /path/to/newfile.py"
        message_with_output = create_tool_message("write", arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, WriteToolMessage)
        assert message_with_output.file_path == file_path
        assert message_with_output.content == content
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_create_bash_tool_message(self):
        """Test creating BashToolMessage for bash tool."""
        from vibecore.widgets.tool_messages import BashToolMessage

        tool_name = "bash"
        command = "ls -la"
        arguments = json.dumps({"command": command})

        # Test without output
        message = create_tool_message(tool_name, arguments)
        assert isinstance(message, BashToolMessage)
        assert message.command == command
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "file1.txt\nfile2.txt"
        message_with_output = create_tool_message(tool_name, arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, BashToolMessage)
        assert message_with_output.command == command
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_create_generic_tool_message(self):
        """Test creating generic ToolMessage for unknown tools."""
        tool_name = "custom_tool"
        arguments = json.dumps({"param": "value"})

        # Test without output
        message = create_tool_message(tool_name, arguments)
        assert isinstance(message, ToolMessage)
        assert message.tool_name == tool_name
        assert message.command == arguments
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "custom output"
        message_with_output = create_tool_message(tool_name, arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, ToolMessage)
        assert message_with_output.tool_name == tool_name
        assert message_with_output.command == arguments
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_invalid_json_arguments(self):
        """Test handling of invalid JSON arguments."""
        # Test with invalid JSON for execute_python
        message = create_tool_message("execute_python", "invalid json")
        assert isinstance(message, PythonToolMessage)
        assert message.code == ""  # Falls back to empty code

        # Test with invalid JSON for todo_write
        message = create_tool_message("todo_write", "invalid json")
        assert isinstance(message, TodoWriteToolMessage)
        assert message.todos == []  # Falls back to empty list

        # Test with invalid JSON for read
        message = create_tool_message("read", "invalid json")
        assert isinstance(message, ReadToolMessage)
        assert message.file_path == ""  # Falls back to empty path

        # Test with invalid JSON for write
        message = create_tool_message("write", "invalid json")
        assert isinstance(message, WriteToolMessage)
        assert message.file_path == ""  # Falls back to empty path
        assert message.content == ""  # Falls back to empty content

        # Test with invalid JSON for bash
        from vibecore.widgets.tool_messages import BashToolMessage

        message = create_tool_message("bash", "invalid json")
        assert isinstance(message, BashToolMessage)
        assert message.command == ""  # Falls back to empty command

        # Test with invalid JSON for generic tool
        message = create_tool_message("custom_tool", "invalid json")
        assert isinstance(message, ToolMessage)
        assert message.command == "invalid json"  # Uses raw string

    def test_missing_fields_in_arguments(self):
        """Test handling of missing fields in parsed arguments."""
        # Test execute_python without code field
        arguments = json.dumps({"other_field": "value"})
        message = create_tool_message("execute_python", arguments)
        assert isinstance(message, PythonToolMessage)
        assert message.code == ""

        # Test todo_write without todos field
        arguments = json.dumps({"other_field": "value"})
        message = create_tool_message("todo_write", arguments)
        assert isinstance(message, TodoWriteToolMessage)
        assert message.todos == []

        # Test read without file_path field
        arguments = json.dumps({"other_field": "value"})
        message = create_tool_message("read", arguments)
        assert isinstance(message, ReadToolMessage)
        assert message.file_path == ""

        # Test write without required fields
        arguments = json.dumps({"other_field": "value"})
        message = create_tool_message("write", arguments)
        assert isinstance(message, WriteToolMessage)
        assert message.file_path == ""
        assert message.content == ""

    def test_unknown_tool_fallback(self):
        """Test that unknown tools use the generic ToolMessage widget."""
        msg = create_tool_message(
            tool_name="unknown_tool",
            arguments='{"some": "args"}',
            output="Some output",
            status=MessageStatus.SUCCESS,
        )

        assert isinstance(msg, ToolMessage)
        assert msg.tool_name == "unknown_tool"
        assert msg.command == '{"some": "args"}'
        assert msg.output == "Some output"
        assert msg.status == MessageStatus.SUCCESS

    def test_mcp_tool_detection(self):
        """Test that MCP tools with mcp__servername__toolname pattern are correctly detected."""
        # Test with proper MCP tool naming pattern
        msg = create_tool_message(
            tool_name="mcp__filesystem__read_file",
            arguments='{"path": "/etc/hosts"}',
            output="127.0.0.1 localhost",
            status=MessageStatus.SUCCESS,
        )

        # Should create MCPToolMessage with extracted server and tool names
        assert isinstance(msg, MCPToolMessage)
        assert msg.server_name == "filesystem"
        assert msg.tool_name == "read_file"
        assert msg.arguments == '{"path": "/etc/hosts"}'
        assert msg.output == "127.0.0.1 localhost"
        assert msg.status == MessageStatus.SUCCESS

        # Test MCP tool without output
        msg_no_output = create_tool_message(
            tool_name="mcp__github__create_issue",
            arguments='{"title": "Bug report", "body": "Description"}',
        )
        assert isinstance(msg_no_output, MCPToolMessage)
        assert msg_no_output.server_name == "github"
        assert msg_no_output.tool_name == "create_issue"
        assert msg_no_output.status == MessageStatus.EXECUTING

        # Test malformed MCP tool name (missing parts)
        msg_malformed = create_tool_message(
            tool_name="mcp__malformed",
            arguments='{"test": "data"}',
            output="output",
            status=MessageStatus.SUCCESS,
        )
        # Should fall back to generic ToolMessage
        assert isinstance(msg_malformed, ToolMessage)
        assert msg_malformed.tool_name == "mcp__malformed"

        # Test non-MCP tool (doesn't start with mcp__)
        msg_non_mcp = create_tool_message(
            tool_name="regular_tool",
            arguments='{"param": "value"}',
            output="result",
            status=MessageStatus.SUCCESS,
        )
        # Should be generic ToolMessage
        assert isinstance(msg_non_mcp, ToolMessage)
        assert msg_non_mcp.tool_name == "regular_tool"
