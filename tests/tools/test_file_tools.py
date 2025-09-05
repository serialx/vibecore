"""Tests for file reading tools."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agents import FunctionTool, RunContextWrapper

from vibecore.context import VibecoreContext
from vibecore.tools.file.executor import edit_file, multi_edit_file, read_file, write_file
from vibecore.tools.file.tools import (
    edit as edit_tool,
)
from vibecore.tools.file.tools import (
    multi_edit as multi_edit_tool,
)
from vibecore.tools.file.tools import (
    read as read_tool,
)
from vibecore.tools.file.tools import (
    write as write_tool,
)
from vibecore.tools.file.utils import PathValidationError, format_line_with_number, validate_file_path


@pytest.fixture
def mock_context():
    """Create a mock RunContextWrapper with VibecoreContext for testing."""

    mock_ctx = MagicMock(spec=RunContextWrapper)

    # Create a real VibecoreContext with current working directory only
    allowed_dirs = [Path.cwd()]
    mock_ctx.context = VibecoreContext(allowed_directories=allowed_dirs)
    return mock_ctx


@pytest.fixture
def temp_dir(tmp_path):
    """Use pytest's tmp_path fixture for temporary directory."""
    return tmp_path


@pytest.fixture
def test_file(temp_dir):
    """Create a test file with sample content."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
    return test_file


@pytest.fixture
def context_with_temp_dir(temp_dir):
    """Create a RunContextWrapper with VibecoreContext for the temp directory."""

    mock_ctx = MagicMock(spec=RunContextWrapper)

    # Create VibecoreContext with the temp directory as allowed
    allowed_dirs = [Path.cwd(), temp_dir]
    mock_ctx.context = VibecoreContext(allowed_directories=allowed_dirs)
    return mock_ctx


class TestPathValidation:
    """Test the path validation utilities."""

    def test_validate_file_path_with_absolute_path_in_base_dir(self, temp_dir):
        """Test validating an absolute path within the base directory."""
        test_file = temp_dir / "test.txt"
        test_file.touch()

        result = validate_file_path(str(test_file), base_dir=temp_dir)
        assert result == test_file.resolve()

    def test_validate_file_path_with_relative_path(self, temp_dir):
        """Test validating a relative path."""
        (temp_dir / "subdir").mkdir()
        test_file = temp_dir / "subdir" / "test.txt"
        test_file.touch()

        result = validate_file_path("subdir/test.txt", base_dir=temp_dir)
        assert result == test_file.resolve()

    def test_validate_file_path_outside_base_dir(self, temp_dir):
        """Test that paths outside base directory are rejected."""
        with pytest.raises(PathValidationError) as excinfo:
            validate_file_path("/etc/passwd", base_dir=temp_dir)
        assert "outside the allowed directory" in str(excinfo.value)

    def test_validate_file_path_with_parent_traversal(self, temp_dir):
        """Test that parent directory traversal is blocked."""
        with pytest.raises(PathValidationError) as excinfo:
            validate_file_path("../../../etc/passwd", base_dir=temp_dir)
        assert "outside the allowed directory" in str(excinfo.value)

    def test_validate_file_path_with_symlink_escape(self, temp_dir):
        """Test that symlinks escaping the base directory are blocked."""
        # Create a symlink pointing outside
        symlink = temp_dir / "escape"
        symlink.symlink_to("/etc")

        with pytest.raises(PathValidationError) as excinfo:
            validate_file_path("escape/passwd", base_dir=temp_dir)
        assert "outside the allowed directory" in str(excinfo.value)

    def test_validate_file_path_with_cwd_default(self):
        """Test that CWD is used as default base directory."""
        # This should work for files in the current directory
        result = validate_file_path("pyproject.toml")
        assert result.is_absolute()
        assert result.name == "pyproject.toml"

    def test_format_line_with_number(self):
        """Test line formatting with line numbers."""
        assert format_line_with_number(1, "Hello") == "     1\tHello"
        assert format_line_with_number(42, "World\n") == "    42\tWorld"
        assert format_line_with_number(999, "Test") == "   999\tTest"

    def test_format_line_with_truncation(self):
        """Test that long lines are truncated."""
        long_line = "x" * 3000
        result = format_line_with_number(1, long_line)
        assert len(result) < 2100  # Line number + tab + 2000 chars + truncation message
        assert result.endswith("... (truncated)")


# The read_file function is the actual implementation to test


@pytest.mark.asyncio
class TestReadTool:
    """Test the read tool functionality."""

    async def test_read_existing_file(self, test_file, context_with_temp_dir):
        """Test reading an existing file."""
        result = await read_file(context_with_temp_dir, str(test_file))

        # Check the format
        lines = result.split("\n")
        assert len(lines) == 5
        assert lines[0] == "     1\tLine 1"
        assert lines[1] == "     2\tLine 2"
        assert lines[4] == "     5\tLine 5"

    async def test_read_non_existent_file(self, temp_dir, context_with_temp_dir):
        """Test reading a non-existent file."""
        result = await read_file(context_with_temp_dir, str(temp_dir / "missing.txt"))
        assert result.startswith("Error: File does not exist:")

    async def test_read_directory(self, temp_dir, context_with_temp_dir):
        """Test attempting to read a directory."""
        result = await read_file(context_with_temp_dir, str(temp_dir))
        assert result.startswith("Error: Path is not a file:")

    async def test_read_with_offset(self, test_file, context_with_temp_dir):
        """Test reading with an offset."""
        result = await read_file(context_with_temp_dir, str(test_file), offset=3)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines[0] == "     3\tLine 3"
        assert lines[2] == "     5\tLine 5"

    async def test_read_with_limit(self, test_file, context_with_temp_dir):
        """Test reading with a limit."""
        result = await read_file(context_with_temp_dir, str(test_file), limit=2)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "     1\tLine 1"
        assert lines[1] == "     2\tLine 2"

    async def test_read_with_offset_and_limit(self, test_file, context_with_temp_dir):
        """Test reading with both offset and limit."""
        result = await read_file(context_with_temp_dir, str(test_file), offset=2, limit=2)
        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "     2\tLine 2"
        assert lines[1] == "     3\tLine 3"

    async def test_read_empty_file(self, temp_dir, context_with_temp_dir):
        """Test reading an empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.touch()

        result = await read_file(context_with_temp_dir, str(empty_file))
        assert "<system-reminder>Warning: The file exists but has empty contents</system-reminder>" in result

    async def test_read_file_with_long_lines(self, temp_dir, context_with_temp_dir):
        """Test reading a file with very long lines."""
        long_file = temp_dir / "long.txt"
        long_line = "x" * 3000
        long_file.write_text(f"{long_line}\nShort line\n")

        result = await read_file(context_with_temp_dir, str(long_file))
        lines = result.split("\n")
        assert "... (truncated)" in lines[0]
        assert "Short line" in lines[1]

    async def test_read_offset_beyond_eof(self, test_file, context_with_temp_dir):
        """Test reading with offset beyond end of file."""
        result = await read_file(context_with_temp_dir, str(test_file), offset=100)
        assert "Error: Offset 100 is beyond the end of file" in result

    async def test_read_invalid_offset(self, test_file, context_with_temp_dir):
        """Test reading with invalid offset."""
        result = await read_file(context_with_temp_dir, str(test_file), offset=0)
        assert "Error: Offset must be 1 or greater" in result

    async def test_read_invalid_limit(self, test_file, context_with_temp_dir):
        """Test reading with invalid limit."""
        result = await read_file(context_with_temp_dir, str(test_file), limit=0)
        assert "Error: Limit must be 1 or greater" in result

    async def test_read_jupyter_notebook(self, temp_dir, context_with_temp_dir):
        """Test that Jupyter notebooks are rejected."""
        notebook = temp_dir / "test.ipynb"
        notebook.write_text('{"cells": []}')

        result = await read_file(context_with_temp_dir, str(notebook))
        assert "Error: For Jupyter notebooks (.ipynb files), please use the NotebookRead tool instead" in result

    async def test_read_file_outside_cwd(self, mock_context):
        """Test that files outside CWD are rejected."""
        result = await read_file(mock_context, "/etc/passwd")
        assert (
            "Error: Path" in result and "outside the allowed director" in result
        )  # Matches both directory/directories

    async def test_read_with_unicode_content(self, temp_dir, context_with_temp_dir):
        """Test reading files with unicode content."""
        unicode_file = temp_dir / "unicode.txt"
        unicode_file.write_text("Hello 世界\n🎉 Emoji test\nÄöü German umlauts\n", encoding="utf-8")

        result = await read_file(context_with_temp_dir, str(unicode_file))
        assert "世界" in result
        assert "🎉" in result
        assert "Äöü" in result

    async def test_read_binary_file_gracefully(self, temp_dir, context_with_temp_dir):
        """Test that binary files are handled gracefully."""
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

        # Should not crash, errors="replace" should handle it
        result = await read_file(context_with_temp_dir, str(binary_file))
        # Result should contain replacement characters but not crash
        assert isinstance(result, str)


class TestReadToolAttributes:
    """Test the read tool's FunctionTool attributes."""

    def test_read_tool_is_function_tool(self):
        """Test that read_tool is a FunctionTool."""
        assert isinstance(read_tool, FunctionTool)

    def test_read_tool_name(self):
        """Test the tool's name."""
        assert read_tool.name == "read"

    def test_read_tool_description(self):
        """Test the tool's description."""
        assert read_tool.description
        assert "filesystem" in read_tool.description
        assert "cat -n" in read_tool.description

    def test_read_tool_schema(self):
        """Test the tool's parameter schema."""
        schema = read_tool.params_json_schema
        assert schema is not None

        # Check properties
        assert "properties" in schema
        props = schema["properties"]
        assert "file_path" in props
        assert "offset" in props
        assert "limit" in props

        # Check file_path is required
        assert "required" in schema
        assert "file_path" in schema["required"]
        # Note: The schema might list all parameters as required due to how function_tool works
        # but offset and limit have None defaults making them effectively optional

        # Check property types
        assert props["file_path"]["type"] == "string"
        # For optional parameters, the type might be in anyOf structure
        if "type" in props["offset"]:
            assert props["offset"]["type"] == "integer"
        else:
            # Check if it's an anyOf with null and integer
            assert "anyOf" in props["offset"]
            types = [t.get("type") for t in props["offset"]["anyOf"]]
            assert "integer" in types or "number" in types

        if "type" in props["limit"]:
            assert props["limit"]["type"] == "integer"
        else:
            # Check if it's an anyOf with null and integer
            assert "anyOf" in props["limit"]
            types = [t.get("type") for t in props["limit"]["anyOf"]]
            assert "integer" in types or "number" in types


@pytest.mark.asyncio
class TestEditTool:
    """Test the edit tool functionality."""

    async def test_edit_simple_replacement(self, test_file, context_with_temp_dir):
        """Test simple string replacement."""
        result = await edit_file(context_with_temp_dir, str(test_file), "Line 2", "Modified Line 2")
        assert "Successfully replaced 1 occurrence(s)" in result

        # Verify the content was changed
        content = test_file.read_text()
        assert "Modified Line 2" in content
        assert content == "Line 1\nModified Line 2\nLine 3\nLine 4\nLine 5\n"

    async def test_edit_with_replace_all(self, temp_dir, context_with_temp_dir):
        """Test replacing all occurrences."""
        file_path = temp_dir / "duplicates.txt"
        file_path.write_text("foo bar foo baz foo")

        result = await edit_file(context_with_temp_dir, str(file_path), "foo", "replaced", replace_all=True)
        assert "Successfully replaced 3 occurrence(s)" in result

        content = file_path.read_text()
        assert content == "replaced bar replaced baz replaced"

    async def test_edit_non_existent_file(self, temp_dir, context_with_temp_dir):
        """Test editing a non-existent file."""
        result = await edit_file(context_with_temp_dir, str(temp_dir / "missing.txt"), "old", "new")
        assert "Error: File does not exist:" in result

    async def test_edit_directory(self, temp_dir, context_with_temp_dir):
        """Test attempting to edit a directory."""
        result = await edit_file(context_with_temp_dir, str(temp_dir), "old", "new")
        assert "Error: Path is not a file:" in result

    async def test_edit_string_not_found(self, test_file, context_with_temp_dir):
        """Test editing when old_string is not found."""
        result = await edit_file(context_with_temp_dir, str(test_file), "Not found", "new")
        assert "Error: String not found in file:" in result

    async def test_edit_multiple_occurrences_without_replace_all(self, temp_dir, context_with_temp_dir):
        """Test error when multiple occurrences exist without replace_all."""
        file_path = temp_dir / "duplicates.txt"
        file_path.write_text("foo bar foo baz")

        result = await edit_file(context_with_temp_dir, str(file_path), "foo", "replaced")
        assert "Error: Multiple occurrences (2) of old_string found" in result
        assert "Use replace_all=True" in result

    async def test_edit_same_old_new_string(self, test_file, context_with_temp_dir):
        """Test error when old_string equals new_string."""
        result = await edit_file(context_with_temp_dir, str(test_file), "Line 1", "Line 1")
        assert "Error: old_string and new_string cannot be the same" in result

    async def test_edit_jupyter_notebook(self, temp_dir, context_with_temp_dir):
        """Test that Jupyter notebooks are rejected."""
        notebook = temp_dir / "test.ipynb"
        notebook.write_text('{"cells": []}')

        result = await edit_file(context_with_temp_dir, str(notebook), "cells", "modified")
        assert "Error: For Jupyter notebooks (.ipynb files), please use the NotebookEdit tool instead" in result

    async def test_edit_file_outside_cwd(self, mock_context):
        """Test that files outside CWD are rejected."""
        result = await edit_file(mock_context, "/etc/passwd", "root", "modified")
        assert (
            "Error: Path" in result and "outside the allowed director" in result
        )  # Matches both directory/directories

    async def test_edit_with_newlines(self, temp_dir, context_with_temp_dir):
        """Test editing multi-line content."""
        file_path = temp_dir / "multiline.txt"
        file_path.write_text("def foo():\n    return 1\n\ndef bar():\n    return 2")

        result = await edit_file(
            context_with_temp_dir, str(file_path), "def foo():\n    return 1", "def foo():\n    return 42"
        )
        assert "Successfully replaced 1 occurrence(s)" in result

        content = file_path.read_text()
        assert "return 42" in content

    async def test_edit_unicode_content(self, temp_dir, context_with_temp_dir):
        """Test editing files with unicode content."""
        unicode_file = temp_dir / "unicode.txt"
        unicode_file.write_text("Hello 世界\n🎉 Emoji test\n", encoding="utf-8")

        result = await edit_file(context_with_temp_dir, str(unicode_file), "世界", "world")
        assert "Successfully replaced 1 occurrence(s)" in result

        content = unicode_file.read_text()
        assert "Hello world" in content
        assert "🎉 Emoji test" in content


class TestEditToolAttributes:
    """Test the edit tool's FunctionTool attributes."""

    def test_edit_tool_is_function_tool(self):
        """Test that edit_tool is a FunctionTool."""
        assert isinstance(edit_tool, FunctionTool)

    def test_edit_tool_name(self):
        """Test the tool's name."""
        assert edit_tool.name == "edit"

    def test_edit_tool_description(self):
        """Test the tool's description."""
        assert edit_tool.description
        assert "string replacements" in edit_tool.description

    def test_edit_tool_schema(self):
        """Test the tool's parameter schema."""
        schema = edit_tool.params_json_schema
        assert schema is not None

        # Check properties
        assert "properties" in schema
        props = schema["properties"]
        assert "file_path" in props
        assert "old_string" in props
        assert "new_string" in props
        assert "replace_all" in props

        # Check required parameters
        assert "required" in schema
        assert "file_path" in schema["required"]
        assert "old_string" in schema["required"]
        assert "new_string" in schema["required"]


@pytest.mark.asyncio
class TestMultiEditTool:
    """Test the multi_edit tool functionality."""

    async def test_multi_edit_simple(self, test_file, context_with_temp_dir):
        """Test multiple edits in sequence."""
        edits = [
            {"old_string": "Line 1", "new_string": "First line"},
            {"old_string": "Line 3", "new_string": "Third line"},
        ]

        result = await multi_edit_file(context_with_temp_dir, str(test_file), edits)
        assert "Successfully applied 2 edits with 2 total replacements" in result

        content = test_file.read_text()
        assert "First line" in content
        assert "Third line" in content

    async def test_multi_edit_with_replace_all(self, temp_dir, context_with_temp_dir):
        """Test multiple edits with replace_all."""
        file_path = temp_dir / "multi.txt"
        file_path.write_text("foo bar foo\nbaz foo qux")

        edits = [
            {"old_string": "foo", "new_string": "FOO", "replace_all": True},
            {"old_string": "bar", "new_string": "BAR"},
        ]

        result = await multi_edit_file(context_with_temp_dir, str(file_path), edits)
        assert "Successfully applied 2 edits with 4 total replacements" in result

        content = file_path.read_text()
        assert content == "FOO BAR FOO\nbaz FOO qux"

    async def test_multi_edit_sequential_dependency(self, temp_dir, context_with_temp_dir):
        """Test that edits are applied sequentially."""
        file_path = temp_dir / "seq.txt"
        file_path.write_text("hello world")

        edits = [
            {"old_string": "hello", "new_string": "hi"},
            {"old_string": "hi world", "new_string": "hi universe"},
        ]

        result = await multi_edit_file(context_with_temp_dir, str(file_path), edits)
        assert "Successfully applied 2 edits with 2 total replacements" in result

        content = file_path.read_text()
        assert content == "hi universe"

    async def test_multi_edit_string_not_found(self, test_file, context_with_temp_dir):
        """Test error when a string is not found in multi-edit."""
        edits = [
            {"old_string": "Line 1", "new_string": "First"},
            {"old_string": "Not found", "new_string": "Something"},
        ]

        result = await multi_edit_file(context_with_temp_dir, str(test_file), edits)
        assert "Error: Edit 2: String not found:" in result

        # Verify no changes were made (atomic operation)
        content = test_file.read_text()
        assert "Line 1" in content
        assert "First" not in content

    async def test_multi_edit_same_old_new_string(self, test_file, context_with_temp_dir):
        """Test error when old_string equals new_string in multi-edit."""
        edits = [
            {"old_string": "Line 1", "new_string": "Line 1"},
        ]

        result = await multi_edit_file(context_with_temp_dir, str(test_file), edits)
        assert "Error: Edit 1: old_string and new_string cannot be the same" in result

    async def test_multi_edit_empty_edits(self, test_file, context_with_temp_dir):
        """Test multi-edit with empty edits list."""
        result = await multi_edit_file(context_with_temp_dir, str(test_file), [])
        assert "Successfully applied 0 edits with 0 total replacements" in result


class TestMultiEditToolAttributes:
    """Test the multi_edit tool's FunctionTool attributes."""

    def test_multi_edit_tool_is_function_tool(self):
        """Test that multi_edit_tool is a FunctionTool."""
        assert isinstance(multi_edit_tool, FunctionTool)

    def test_multi_edit_tool_name(self):
        """Test the tool's name."""
        assert multi_edit_tool.name == "multi_edit"

    def test_multi_edit_tool_description(self):
        """Test the tool's description."""
        assert multi_edit_tool.description
        assert "multiple edits" in multi_edit_tool.description

    def test_multi_edit_tool_schema(self):
        """Test the tool's parameter schema."""
        schema = multi_edit_tool.params_json_schema
        assert schema is not None

        # Check properties
        assert "properties" in schema
        props = schema["properties"]
        assert "file_path" in props
        assert "edits" in props

        # Check required parameters
        assert "required" in schema
        assert "file_path" in schema["required"]
        assert "edits" in schema["required"]


@pytest.mark.asyncio
class TestWriteTool:
    """Test the write tool functionality."""

    async def test_write_new_file(self, temp_dir, context_with_temp_dir):
        """Test writing a new file."""
        file_path = temp_dir / "new_file.txt"
        content = "Hello, world!\nThis is a test."

        result = await write_file(context_with_temp_dir, str(file_path), content)
        assert f"Successfully wrote {len(content)} bytes" in result

        assert file_path.exists()
        assert file_path.read_text() == content

    async def test_write_overwrite_file(self, test_file, context_with_temp_dir):
        """Test overwriting an existing file."""
        new_content = "Completely new content"

        result = await write_file(context_with_temp_dir, str(test_file), new_content)
        assert f"Successfully wrote {len(new_content)} bytes" in result

        assert test_file.read_text() == new_content

    async def test_write_to_directory(self, temp_dir, context_with_temp_dir):
        """Test error when trying to write to a directory."""
        result = await write_file(context_with_temp_dir, str(temp_dir), "content")
        assert "Error: Path is a directory:" in result

    async def test_write_create_parent_dirs(self, temp_dir, context_with_temp_dir):
        """Test that parent directories are created."""
        file_path = temp_dir / "sub" / "dir" / "file.txt"
        content = "test content"

        result = await write_file(context_with_temp_dir, str(file_path), content)
        assert f"Successfully wrote {len(content)} bytes" in result

        assert file_path.exists()
        assert file_path.read_text() == content

    async def test_write_jupyter_notebook(self, temp_dir, context_with_temp_dir):
        """Test that Jupyter notebooks are rejected."""
        notebook = temp_dir / "test.ipynb"

        result = await write_file(context_with_temp_dir, str(notebook), '{"cells": []}')
        assert "Error: For Jupyter notebooks (.ipynb files), please use the NotebookEdit tool instead" in result

    async def test_write_file_outside_cwd(self, mock_context):
        """Test that files outside CWD are rejected."""
        result = await write_file(mock_context, "/etc/test.txt", "content")
        assert (
            "Error: Path" in result and "outside the allowed director" in result
        )  # Matches both directory/directories

    async def test_write_unicode_content(self, temp_dir, context_with_temp_dir):
        """Test writing unicode content."""
        file_path = temp_dir / "unicode.txt"
        content = "Hello 世界\n🎉 Emoji test\nÄöü German umlauts"

        result = await write_file(context_with_temp_dir, str(file_path), content)
        assert f"Successfully wrote {len(content)} bytes" in result

        assert file_path.read_text(encoding="utf-8") == content

    async def test_write_empty_file(self, temp_dir, context_with_temp_dir):
        """Test writing an empty file."""
        file_path = temp_dir / "empty.txt"

        result = await write_file(context_with_temp_dir, str(file_path), "")
        assert "Successfully wrote 0 bytes" in result

        assert file_path.exists()
        assert file_path.read_text() == ""


class TestWriteToolAttributes:
    """Test the write tool's FunctionTool attributes."""

    def test_write_tool_is_function_tool(self):
        """Test that write_tool is a FunctionTool."""
        assert isinstance(write_tool, FunctionTool)

    def test_write_tool_name(self):
        """Test the tool's name."""
        assert write_tool.name == "write"

    def test_write_tool_description(self):
        """Test the tool's description."""
        assert write_tool.description
        assert "filesystem" in write_tool.description

    def test_write_tool_schema(self):
        """Test the tool's parameter schema."""
        schema = write_tool.params_json_schema
        assert schema is not None

        # Check properties
        assert "properties" in schema
        props = schema["properties"]
        assert "file_path" in props
        assert "content" in props

        # Check required parameters
        assert "required" in schema
        assert "file_path" in schema["required"]
        assert "content" in schema["required"]
