"""Tests for the tool message factory."""

import json

from vibecore.widgets.messages import MessageStatus
from vibecore.widgets.tool_message_factory import create_tool_message
from vibecore.widgets.tool_messages import (
    EditToolMessage,
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

        # Test with invalid JSON for write
        message = create_tool_message("write", "invalid json")
        assert isinstance(message, WriteToolMessage)
        assert message.file_path == ""  # Falls back to empty path
        assert message.content == ""  # Falls back to empty content

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

        # Test write without required fields
        arguments = json.dumps({"other_field": "value"})
        message = create_tool_message("write", arguments)
        assert isinstance(message, WriteToolMessage)
        assert message.file_path == ""
        assert message.content == ""

    def test_create_edit_tool_message(self):
        """Test creating EditToolMessage."""
        file_path = "/path/to/file.py"
        old_string = "def hello():\n    print('Hello')"
        new_string = "def hello():\n    print('Hello, World!')"
        arguments = json.dumps(
            {"file_path": file_path, "old_string": old_string, "new_string": new_string, "replace_all": False}
        )

        # Test without output
        message = create_tool_message("edit", arguments)
        assert isinstance(message, EditToolMessage)
        assert message.file_path == file_path
        assert message.arguments == arguments
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING
        # Check that diff content was generated
        assert message.diff_content != ""
        assert "(before)" in message.diff_content
        assert "(after)" in message.diff_content

        # Test with output
        output = "Successfully replaced 1 occurrence(s) in /path/to/file.py"
        message_with_output = create_tool_message("edit", arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, EditToolMessage)
        assert message_with_output.file_path == file_path
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_create_multi_edit_tool_message(self):
        """Test creating EditToolMessage for multi_edit."""
        file_path = "/path/to/file.py"
        edits = [
            {"old_string": "foo", "new_string": "bar", "replace_all": True},
            {"old_string": "baz", "new_string": "qux"},
        ]
        arguments = json.dumps({"file_path": file_path, "edits": edits})

        # Test without output
        message = create_tool_message("multi_edit", arguments)
        assert isinstance(message, EditToolMessage)
        assert message.file_path == file_path
        assert message.arguments == arguments
        assert message.output == ""
        assert message.status == MessageStatus.EXECUTING
        # Check that diff content was generated for multiple edits
        assert message.diff_content != ""
        assert "Edit 1:" in message.diff_content
        assert "Edit 2:" in message.diff_content

        # Test with output
        output = "Successfully applied 2 edits with 5 total replacements in /path/to/file.py"
        message_with_output = create_tool_message("multi_edit", arguments, output=output, status=MessageStatus.SUCCESS)
        assert isinstance(message_with_output, EditToolMessage)
        assert message_with_output.output == output
        assert message_with_output.status == MessageStatus.SUCCESS

    def test_edit_tool_message_invalid_json(self):
        """Test handling of invalid JSON for edit tools."""
        # Test with invalid JSON for edit
        message = create_tool_message("edit", "invalid json")
        assert isinstance(message, EditToolMessage)
        assert message.file_path == ""
        assert message.diff_content == ""  # No diff generated

        # Test with invalid JSON for multi_edit
        message = create_tool_message("multi_edit", "invalid json")
        assert isinstance(message, EditToolMessage)
        assert message.file_path == ""
        assert message.diff_content == ""  # No diff generated

    def test_edit_tool_message_missing_fields(self):
        """Test handling of missing fields in edit arguments."""
        # Test edit without required fields
        arguments = json.dumps({"file_path": "/test.py"})
        message = create_tool_message("edit", arguments)
        assert isinstance(message, EditToolMessage)
        assert message.file_path == "/test.py"
        assert message.diff_content == ""  # No diff without old/new strings

        # Test multi_edit without edits field
        arguments = json.dumps({"file_path": "/test.py"})
        message = create_tool_message("multi_edit", arguments)
        assert isinstance(message, EditToolMessage)
        assert message.file_path == "/test.py"
        assert message.diff_content == ""  # No diff without edits
