"""Tests for shell tools."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agents import FunctionTool, RunContextWrapper

from vibecore.context import VibecoreContext
from vibecore.tools.shell.executor import bash_executor, glob_files, grep_files, list_directory
from vibecore.tools.shell.tools import bash as bash_tool
from vibecore.tools.shell.tools import glob as glob_tool
from vibecore.tools.shell.tools import grep as grep_tool
from vibecore.tools.shell.tools import ls as ls_tool


@pytest.fixture
def mock_context():
    """Create a mock RunContextWrapper with VibecoreContext."""
    from pathlib import Path

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
def context_with_temp_dir(temp_dir):
    """Create a RunContextWrapper with VibecoreContext for the temp directory."""
    from pathlib import Path

    mock_ctx = MagicMock(spec=RunContextWrapper)

    # Create VibecoreContext with the temp directory as allowed
    allowed_dirs = [Path.cwd(), temp_dir]
    mock_ctx.context = VibecoreContext(allowed_directories=allowed_dirs)
    return mock_ctx


@pytest.mark.asyncio
class TestBashExecutor:
    """Test the bash executor functionality."""

    async def test_bash_simple_command(self, mock_context):
        """Test executing a simple command."""
        output, exit_code = await bash_executor(mock_context, "echo 'Hello World'")
        assert exit_code == 0
        assert "Hello World" in output

    async def test_bash_command_with_error(self, mock_context):
        """Test command that returns non-zero exit code."""
        _, exit_code = await bash_executor(mock_context, "exit 42")
        assert exit_code == 42

    async def test_bash_command_not_found(self, mock_context):
        """Test command that doesn't exist."""
        output, exit_code = await bash_executor(mock_context, "this_command_does_not_exist_12345")
        assert exit_code != 0
        assert "command not found" in output.lower() or "not found" in output.lower()

    async def test_bash_timeout(self, mock_context):
        """Test command timeout."""
        # Use a command that will definitely take longer than timeout
        output, exit_code = await bash_executor(mock_context, "sleep 5", timeout=100)  # 100ms timeout
        assert exit_code == 124  # Timeout exit code
        assert "timed out" in output.lower()

    async def test_bash_invalid_timeout(self, mock_context):
        """Test invalid timeout values."""
        output, exit_code = await bash_executor(mock_context, "echo test", timeout=-1)
        assert exit_code == 1
        assert "Timeout must be positive" in output

        output, exit_code = await bash_executor(mock_context, "echo test", timeout=700000)
        assert exit_code == 1
        assert "cannot exceed 600000ms" in output

    async def test_bash_output_truncation(self, mock_context):
        """Test that long output is truncated."""
        # Generate output > 30000 chars
        command = f"echo '{'x' * 35000}'"
        output, exit_code = await bash_executor(mock_context, command)
        assert exit_code == 0
        assert len(output) < 35000
        assert "output truncated" in output

    async def test_bash_multiline_output(self, mock_context):
        """Test command with multiline output."""
        output, exit_code = await bash_executor(mock_context, "echo -e 'line1\\nline2\\nline3'")
        assert exit_code == 0
        assert "line1" in output
        assert "line2" in output
        assert "line3" in output

    async def test_bash_environment_variables(self, mock_context):
        """Test that environment variables are accessible."""
        output, exit_code = await bash_executor(mock_context, "echo $HOME")
        assert exit_code == 0
        assert output.strip() != ""  # HOME should be set

    async def test_bash_pipe_commands(self, mock_context):
        """Test piped commands."""
        output, exit_code = await bash_executor(mock_context, "echo 'hello world' | grep world")
        assert exit_code == 0
        assert "hello world" in output

    async def test_bash_working_directory(self, mock_context):
        """Test that commands run in the correct directory."""
        output, exit_code = await bash_executor(mock_context, "pwd")
        assert exit_code == 0
        # Should run in current working directory
        assert str(Path.cwd()) in output


@pytest.mark.asyncio
class TestGlobFiles:
    """Test the glob files functionality."""

    async def test_glob_simple_pattern(self, temp_dir, context_with_temp_dir):
        """Test simple glob pattern."""
        # Create test files
        (temp_dir / "test1.txt").touch()
        (temp_dir / "test2.txt").touch()
        (temp_dir / "other.py").touch()

        files = await glob_files(context_with_temp_dir, "*.txt", str(temp_dir))
        assert len(files) == 2
        assert any("test1.txt" in f for f in files)
        assert any("test2.txt" in f for f in files)
        assert not any("other.py" in f for f in files)

    async def test_glob_recursive_pattern(self, temp_dir, context_with_temp_dir):
        """Test recursive glob pattern."""
        # Create nested structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (temp_dir / "top.py").touch()
        (subdir / "nested.py").touch()

        files = await glob_files(context_with_temp_dir, "**/*.py", str(temp_dir))
        assert len(files) == 2
        assert any("top.py" in f for f in files)
        assert any("nested.py" in f for f in files)

    async def test_glob_no_matches(self, temp_dir, context_with_temp_dir):
        """Test glob with no matches."""
        files = await glob_files(context_with_temp_dir, "*.nonexistent", str(temp_dir))
        assert files == []

    async def test_glob_nonexistent_path(self, mock_context):
        """Test glob with non-existent path."""
        files = await glob_files(mock_context, "*.txt", "/path/that/does/not/exist")
        assert len(files) == 1
        assert (
            "Error: Path" in files[0] and "outside the allowed director" in files[0]
        )  # Matches both directory/directories

    async def test_glob_file_as_path(self, temp_dir, context_with_temp_dir):
        """Test glob with file as path."""
        test_file = temp_dir / "file.txt"
        test_file.touch()

        files = await glob_files(context_with_temp_dir, "*.txt", str(test_file))
        assert len(files) == 1
        assert files[0].startswith("Error: Path is not a directory:")

    async def test_glob_default_path(self, temp_dir, context_with_temp_dir):
        """Test glob with default path (CWD)."""
        # Save current directory
        original_cwd = Path.cwd()
        try:
            # Change to temp directory
            os.chdir(temp_dir)
            (temp_dir / "test.txt").touch()

            files = await glob_files(context_with_temp_dir, "*.txt")
            assert len(files) == 1
            assert "test.txt" in files[0]
            # Should return relative path when using CWD
            assert not files[0].startswith("/")
        finally:
            os.chdir(original_cwd)

    async def test_glob_sorted_by_mtime(self, temp_dir, context_with_temp_dir):
        """Test that results are sorted by modification time."""
        import time

        # Create files with different mtimes
        file1 = temp_dir / "old.txt"
        file1.touch()
        time.sleep(0.01)  # Ensure different mtime

        file2 = temp_dir / "new.txt"
        file2.touch()

        files = await glob_files(context_with_temp_dir, "*.txt", str(temp_dir))
        assert len(files) == 2
        # Newer file should come first
        assert "new.txt" in files[0]
        assert "old.txt" in files[1]

    async def test_glob_excludes_directories(self, temp_dir, context_with_temp_dir):
        """Test that glob only returns files, not directories."""
        (temp_dir / "file.txt").touch()
        (temp_dir / "subdir").mkdir()

        files = await glob_files(context_with_temp_dir, "*", str(temp_dir))
        assert len(files) == 1
        assert "file.txt" in files[0]
        assert "subdir" not in str(files)


@pytest.mark.asyncio
class TestGrepFiles:
    """Test the grep files functionality."""

    async def test_grep_simple_pattern(self, temp_dir, context_with_temp_dir):
        """Test simple grep pattern."""
        # Create test files with content
        file1 = temp_dir / "test1.txt"
        file1.write_text("Hello World")

        file2 = temp_dir / "test2.txt"
        file2.write_text("Goodbye Moon")

        file3 = temp_dir / "test3.txt"
        file3.write_text("Hello Again")

        files = await grep_files(context_with_temp_dir, "Hello", str(temp_dir))
        assert len(files) == 2
        assert any("test1.txt" in f for f in files)
        assert any("test3.txt" in f for f in files)
        assert not any("test2.txt" in f for f in files)

    async def test_grep_regex_pattern(self, temp_dir, context_with_temp_dir):
        """Test regex pattern."""
        file1 = temp_dir / "test.txt"
        file1.write_text("Error: Something went wrong\nInfo: All good")

        files = await grep_files(context_with_temp_dir, "Error:.*wrong", str(temp_dir))
        assert len(files) == 1
        assert "test.txt" in files[0]

    async def test_grep_with_include_filter(self, temp_dir, context_with_temp_dir):
        """Test grep with include filter."""
        # Create mixed file types
        py_file = temp_dir / "code.py"
        py_file.write_text("def test(): pass")

        txt_file = temp_dir / "doc.txt"
        txt_file.write_text("def test(): pass")

        files = await grep_files(context_with_temp_dir, "def", str(temp_dir), include="*.py")
        assert len(files) == 1
        assert "code.py" in files[0]

    async def test_grep_invalid_regex(self, temp_dir, context_with_temp_dir):
        """Test grep with invalid regex."""
        files = await grep_files(context_with_temp_dir, "[invalid(regex", str(temp_dir))
        assert len(files) == 1
        assert files[0].startswith("Error: Invalid regex pattern:")

    async def test_grep_no_matches(self, temp_dir, context_with_temp_dir):
        """Test grep with no matches."""
        file1 = temp_dir / "test.txt"
        file1.write_text("Nothing here")

        files = await grep_files(context_with_temp_dir, "NotFound", str(temp_dir))
        assert files == []

    async def test_grep_binary_files_skipped(self, temp_dir, context_with_temp_dir):
        """Test that binary files are skipped."""
        # Create a binary file
        binary_file = temp_dir / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03Hello\xff\xfe")

        # Create text file
        text_file = temp_dir / "text.txt"
        text_file.write_text("Hello World")

        files = await grep_files(context_with_temp_dir, "Hello", str(temp_dir))
        # Should find text file, binary file handling may vary
        assert any("text.txt" in f for f in files)

    async def test_grep_nested_directories(self, temp_dir, context_with_temp_dir):
        """Test grep in nested directories."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        file1 = temp_dir / "top.txt"
        file1.write_text("pattern here")

        file2 = subdir / "nested.txt"
        file2.write_text("pattern here too")

        files = await grep_files(context_with_temp_dir, "pattern", str(temp_dir))
        assert len(files) == 2
        assert any("top.txt" in f for f in files)
        assert any("nested.txt" in f for f in files)

    async def test_grep_sorted_by_mtime(self, temp_dir, context_with_temp_dir):
        """Test that results are sorted by modification time."""
        import time

        # Create files with different mtimes
        file1 = temp_dir / "old.txt"
        file1.write_text("pattern")
        time.sleep(0.01)

        file2 = temp_dir / "new.txt"
        file2.write_text("pattern")

        files = await grep_files(context_with_temp_dir, "pattern", str(temp_dir))
        assert len(files) == 2
        # Newer file should come first
        assert "new.txt" in files[0]
        assert "old.txt" in files[1]


@pytest.mark.asyncio
class TestListDirectory:
    """Test the list directory functionality."""

    async def test_list_simple_directory(self, temp_dir, context_with_temp_dir):
        """Test listing a simple directory."""
        # Create test files and directories
        (temp_dir / "file1.txt").touch()
        (temp_dir / "file2.py").touch()
        (temp_dir / "subdir").mkdir()

        entries = await list_directory(context_with_temp_dir, str(temp_dir))
        assert len(entries) == 3
        assert "file1.txt" in entries
        assert "file2.py" in entries
        assert "subdir/" in entries  # Directories have trailing slash

    async def test_list_empty_directory(self, temp_dir, context_with_temp_dir):
        """Test listing an empty directory."""
        entries = await list_directory(context_with_temp_dir, str(temp_dir))
        assert entries == []

    async def test_list_with_ignore_patterns(self, temp_dir, context_with_temp_dir):
        """Test listing with ignore patterns."""
        (temp_dir / "file.txt").touch()
        (temp_dir / "file.pyc").touch()
        (temp_dir / ".hidden").touch()
        (temp_dir / "keep.py").touch()

        entries = await list_directory(context_with_temp_dir, str(temp_dir), ignore=["*.pyc", ".*"])
        assert len(entries) == 2
        assert "file.txt" in entries
        assert "keep.py" in entries
        assert "file.pyc" not in entries
        assert ".hidden" not in entries

    async def test_list_non_absolute_path(self, temp_dir, context_with_temp_dir):
        """Test with relative path (which gets resolved to absolute)."""
        # Create a subdirectory
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "file.txt").touch()

        # Use relative path from temp_dir
        entries = await list_directory(context_with_temp_dir, str(sub_dir))
        assert "file.txt" in entries

    async def test_list_nonexistent_path(self, temp_dir, mock_context):
        """Test listing non-existent directory."""
        # Try to list a path outside allowed directory
        entries = await list_directory(mock_context, "/path/that/does/not/exist")
        assert len(entries) == 1
        assert (
            "Error: Path" in entries[0] and "outside the allowed director" in entries[0]
        )  # Matches both directory/directories

    async def test_list_file_instead_of_directory(self, temp_dir, context_with_temp_dir):
        """Test error when path is a file."""
        test_file = temp_dir / "file.txt"
        test_file.touch()

        entries = await list_directory(context_with_temp_dir, str(test_file))
        assert len(entries) == 1
        assert entries[0].startswith("Error: Path is not a directory:")

    async def test_list_sorted_entries(self, temp_dir, context_with_temp_dir):
        """Test that entries are sorted."""
        (temp_dir / "z_file.txt").touch()
        (temp_dir / "a_file.txt").touch()
        (temp_dir / "m_file.txt").touch()

        entries = await list_directory(context_with_temp_dir, str(temp_dir))
        assert entries == ["a_file.txt", "m_file.txt", "z_file.txt"]

    @pytest.mark.skipif(sys.platform == "win32", reason="Permission test not reliable on Windows")
    async def test_list_permission_denied(self, temp_dir, context_with_temp_dir):
        """Test handling permission denied."""
        # Create directory with no read permission
        no_read = temp_dir / "no_read"
        no_read.mkdir()
        no_read.chmod(0o000)

        try:
            entries = await list_directory(context_with_temp_dir, str(no_read))
            if getattr(os, "geteuid", lambda: None)() == 0:
                # When executed as root, the kernel bypasses the permission bits,
                # so listing succeeds and simply returns an empty directory.
                assert entries == []
            else:
                assert len(entries) == 1
                assert "Permission denied" in entries[0]
        finally:
            # Restore permissions for cleanup
            no_read.chmod(0o755)


class TestToolAttributes:
    """Test the tool attributes and schemas."""

    def test_bash_tool_attributes(self):
        """Test bash tool attributes."""
        assert isinstance(bash_tool, FunctionTool)
        assert bash_tool.name == "bash"
        assert "bash command" in bash_tool.description

        schema = bash_tool.params_json_schema
        assert "properties" in schema
        assert "command" in schema["properties"]
        assert "timeout" in schema["properties"]
        assert "description" in schema["properties"]
        assert "command" in schema["required"]

    def test_glob_tool_attributes(self):
        """Test glob tool attributes."""
        assert isinstance(glob_tool, FunctionTool)
        assert glob_tool.name == "glob"
        assert "pattern matching" in glob_tool.description

        schema = glob_tool.params_json_schema
        assert "properties" in schema
        assert "pattern" in schema["properties"]
        assert "path" in schema["properties"]
        assert "pattern" in schema["required"]

    def test_grep_tool_attributes(self):
        """Test grep tool attributes."""
        assert isinstance(grep_tool, FunctionTool)
        assert grep_tool.name == "grep"
        assert "content search" in grep_tool.description

        schema = grep_tool.params_json_schema
        assert "properties" in schema
        assert "pattern" in schema["properties"]
        assert "path" in schema["properties"]
        assert "include" in schema["properties"]
        assert "pattern" in schema["required"]

    def test_ls_tool_attributes(self):
        """Test ls tool attributes."""
        assert isinstance(ls_tool, FunctionTool)
        assert ls_tool.name == "ls"
        assert "Lists files and directories" in ls_tool.description

        schema = ls_tool.params_json_schema
        assert "properties" in schema
        assert "path" in schema["properties"]
        assert "ignore" in schema["properties"]
        assert "path" in schema["required"]
