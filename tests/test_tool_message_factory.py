"""Tests for the tool message factory."""

import json

from vibecore.widgets.messages import (
    MessageStatus,
    PythonToolMessage,
    ReadToolMessage,
    TodoWriteToolMessage,
    ToolMessage,
)
from vibecore.widgets.tool_message_factory import create_tool_message


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

    def test_create_generic_tool_message(self):
        """Test creating generic ToolMessage for unknown tools."""
        tool_name = "bash"
        command = "ls -la"
        arguments = json.dumps({"command": command})

        # Test without output
        message = create_tool_message(tool_name, arguments)
        assert isinstance(message, ToolMessage)
        assert message.tool_name == tool_name
        assert message.command == arguments
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING

        # Test with output
        output = "file1.txt\nfile2.txt"
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

        # Test with invalid JSON for generic tool
        message = create_tool_message("bash", "invalid json")
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
