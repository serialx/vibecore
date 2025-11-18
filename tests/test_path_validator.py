"""Unit tests for PathValidator class."""

from pathlib import Path

import pytest

from vibecore.tools.file.utils import PathValidationError
from vibecore.tools.path_validator import PathValidator


class TestPathValidator:
    """Test suite for PathValidator."""

    def test_init_with_directories(self):
        """Test initialization with specific directories."""
        dirs = [Path("/tmp"), Path("/home")]
        validator = PathValidator(dirs)
        assert len(validator.allowed_directories) == 2
        assert all(d.is_absolute() for d in validator.allowed_directories)

    def test_init_empty_defaults_to_cwd(self):
        """Test that empty list defaults to CWD."""
        validator = PathValidator([])
        assert len(validator.allowed_directories) == 1
        assert validator.allowed_directories[0] == Path.cwd().resolve()

    def test_validate_allowed_path(self, tmp_path):
        """Test validating a path within allowed directories."""
        validator = PathValidator([tmp_path])
        test_file = tmp_path / "test.txt"
        test_file.touch()

        validated = validator.validate_path(test_file)
        assert validated == test_file.resolve()

    def test_validate_disallowed_path(self, tmp_path):
        """Test that paths outside allowed directories raise an error."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        validator = PathValidator([allowed_dir])

        disallowed_file = tmp_path / "disallowed.txt"
        disallowed_file.touch()

        with pytest.raises(PathValidationError) as excinfo:
            validator.validate_path(disallowed_file)
        assert "outside the allowed director" in str(excinfo.value)  # Matches both directory and directories

    def test_validate_relative_path(self, tmp_path, monkeypatch):
        """Test validating a relative path."""
        monkeypatch.chdir(tmp_path)
        validator = PathValidator([tmp_path])

        test_file = tmp_path / "test.txt"
        test_file.touch()

        # Use relative path
        validated = validator.validate_path("test.txt")
        assert validated == test_file.resolve()

    def test_validate_path_with_traversal(self, tmp_path):
        """Test that path traversal attempts are prevented."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        validator = PathValidator([allowed_dir])

        # Try to escape using ..
        with pytest.raises(PathValidationError):
            validator.validate_path(str(allowed_dir / ".." / "outside.txt"))

    def test_validate_symlink(self, tmp_path):
        """Test that symlinks are resolved before validation."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        validator = PathValidator([allowed_dir])

        # Create a file in allowed directory
        allowed_file = allowed_dir / "file.txt"
        allowed_file.touch()

        # Create a symlink in allowed directory
        symlink = allowed_dir / "link.txt"
        symlink.symlink_to(allowed_file)

        # Should validate successfully
        validated = validator.validate_path(symlink)
        assert validated == allowed_file.resolve()

    def test_validate_symlink_escape(self, tmp_path):
        """Test that symlinks pointing outside are caught."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        validator = PathValidator([allowed_dir])

        # Create a file outside allowed directory
        outside_file = tmp_path / "outside.txt"
        outside_file.touch()

        # Create a symlink in allowed directory pointing outside
        symlink = allowed_dir / "link.txt"
        symlink.symlink_to(outside_file)

        # Should fail validation
        with pytest.raises(PathValidationError):
            validator.validate_path(symlink)

    def test_is_path_allowed(self, tmp_path):
        """Test the is_path_allowed method."""
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        validator = PathValidator([allowed_dir])

        # Test allowed path
        allowed_file = allowed_dir / "file.txt"
        assert validator.is_path_allowed(allowed_file)

        # Test disallowed path
        disallowed_file = tmp_path / "disallowed.txt"
        assert not validator.is_path_allowed(disallowed_file)

    def test_validate_command_paths_basic(self, tmp_path):
        """Test command path validation with basic commands."""
        validator = PathValidator([tmp_path])

        # Should pass - no paths
        validator.validate_command_paths("echo hello")

        # Should pass - path within allowed
        test_file = tmp_path / "test.txt"
        test_file.touch()
        validator.validate_command_paths(f"cat {test_file}")

        # Should fail - path outside allowed
        with pytest.raises(PathValidationError):
            validator.validate_command_paths("cat /etc/passwd")

    def test_validate_command_paths_with_redirection(self, tmp_path):
        """Test command validation with redirections."""
        validator = PathValidator([tmp_path])

        output_file = tmp_path / "output.txt"

        # Should pass - redirect to allowed path
        validator.validate_command_paths(f"echo hello > {output_file}")

        # Should fail - redirect to disallowed path
        with pytest.raises(PathValidationError):
            validator.validate_command_paths("echo hello > /etc/output.txt")

    def test_validate_command_paths_with_pipes(self, tmp_path):
        """Test command validation with pipes and complex commands."""
        validator = PathValidator([tmp_path])

        test_file = tmp_path / "test.txt"
        test_file.touch()

        # Should pass - piped commands with allowed paths
        validator.validate_command_paths(f"cat {test_file} | grep pattern")

        # Should pass - multiple commands with semicolon
        validator.validate_command_paths(f"cd {tmp_path}; ls")

    def test_validate_command_paths_skips_urls(self):
        """Test that URLs are not validated as paths."""
        validator = PathValidator([Path.cwd()])

        # Should not raise for URLs
        validator.validate_command_paths("curl https://example.com")
        validator.validate_command_paths("wget ftp://example.com/file.txt")
        validator.validate_command_paths("git clone git@github.com:user/repo.git")

    def test_validate_command_paths_home_expansion(self, tmp_path, monkeypatch):
        """Test that ~ is expanded in command validation."""
        # Set HOME to tmp_path for testing
        monkeypatch.setenv("HOME", str(tmp_path))
        validator = PathValidator([tmp_path])

        # Should pass - home directory is allowed
        validator.validate_command_paths("cat ~/test.txt")

        # Create a different directory that's not allowed
        other_dir = tmp_path.parent / "other"
        other_dir.mkdir(exist_ok=True)

        # Validator with different allowed directory
        validator2 = PathValidator([other_dir])

        # Should fail - home directory is not in allowed
        with pytest.raises(PathValidationError):
            validator2.validate_command_paths("cat ~/test.txt")

    def test_get_allowed_directories(self):
        """Test getting the list of allowed directories."""
        dirs = [Path("/tmp"), Path("/home")]
        validator = PathValidator(dirs)
        allowed = validator.get_allowed_directories()

        # Should return a copy
        assert allowed is not validator.allowed_directories
        assert len(allowed) == 2

    def test_malformed_command(self):
        """Test handling of malformed shell commands."""
        validator = PathValidator([Path.cwd()])

        # Unclosed quote should raise
        with pytest.raises(PathValidationError) as excinfo:
            validator.validate_command_paths('echo "unclosed')
        assert "Cannot parse command" in str(excinfo.value)

    def test_path_resolution_error(self, tmp_path):
        """Test handling of path resolution errors."""
        validator = PathValidator([tmp_path])

        # Non-existent path with complex traversal that might fail resolution
        complex_path = str(tmp_path / "nonexistent" / ".." / ".." / "nowhere")

        # Should handle gracefully
        with pytest.raises(PathValidationError):
            validator.validate_path(complex_path)

    def test_validate_command_paths_with_heredoc(self, tmp_path):
        """Test command validation with heredoc syntax."""
        validator = PathValidator([tmp_path])

        output_file = tmp_path / "output.txt"

        # Should pass - heredoc with allowed path
        validator.validate_command_paths(f"cat > {output_file} << 'EOF'")
        validator.validate_command_paths(f"cat > {output_file} <<EOF")
        validator.validate_command_paths(f"cat > {output_file} << EOF")
        validator.validate_command_paths(f"cat >> {output_file} <<'DELIMITER'")

        # Should fail - heredoc with disallowed path
        with pytest.raises(PathValidationError):
            validator.validate_command_paths("cat > /etc/output.txt << 'EOF'")
