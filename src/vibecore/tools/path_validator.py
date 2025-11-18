"""Path validation module for vibecore tools.

This module provides path validation functionality to confine file and shell
operations to a configurable list of allowed directories.
"""

import shlex
from contextlib import suppress
from pathlib import Path

from textual import log

from vibecore.tools.file.utils import PathValidationError


class PathValidator:
    """Validates paths against a list of allowed directories."""

    def __init__(self, allowed_directories: list[Path]):
        """Initialize with list of allowed directories.

        Args:
            allowed_directories: List of directories to allow access to.
                               Defaults to [CWD] if empty.
        """
        self.allowed_directories = (
            [d.resolve() for d in allowed_directories] if allowed_directories else [Path.cwd().resolve()]
        )

    def validate_path(self, path: str | Path, operation: str = "access") -> Path:
        """Validate a path against allowed directories.

        Args:
            path: The path to validate
            operation: Description of the operation (for error messages)

        Returns:
            The validated absolute Path object

        Raises:
            PathValidationError: If path is outside allowed directories
        """
        # Convert to Path object
        path_obj = Path(path) if isinstance(path, str) else path

        # Resolve to absolute path (follows symlinks)
        try:
            absolute_path = path_obj.resolve()
        except (OSError, RuntimeError) as e:
            # Handle cases where path resolution fails
            raise PathValidationError(f"Cannot resolve path '{path}': {e}") from e

        # Check if path is under any allowed directory
        if not self.is_path_allowed(absolute_path):
            allowed_dirs_str = ", ".join(f"'{d}'" for d in self.allowed_directories)
            raise PathValidationError(
                f"Path '{absolute_path}' is outside the allowed directories. "
                f"Access is restricted to {allowed_dirs_str} and their subdirectories."
            )

        return absolute_path

    def validate_command_paths(self, command: str) -> None:
        """Validate paths referenced in a shell command.

        Args:
            command: The shell command to validate

        Raises:
            PathValidationError: If command references paths outside allowed directories
        """
        # Parse the command to extract potential file paths
        try:
            # First, replace shell operators with spaces around them to ensure proper splitting
            # This handles cases like "cd /path;ls" which shlex doesn't split properly
            # Process longer operators first to avoid issues (e.g., "<<<" before "<<")
            for op in ["<<<", "<<", "&&", "||", ">>", ";", "|", "&"]:
                command = command.replace(op, f" {op} ")

            # Use shlex to properly parse the command
            tokens = shlex.split(command)
        except ValueError as e:
            # If shlex fails, the command might be malformed
            raise PathValidationError(f"Cannot parse command: {e}") from e

        # Commands that take path arguments
        path_commands = {
            "cat",
            "ls",
            "cd",
            "cp",
            "mv",
            "rm",
            "mkdir",
            "rmdir",
            "touch",
            "chmod",
            "chown",
            "head",
            "tail",
            "less",
            "more",
            "grep",
            "find",
            "sed",
            "awk",
            "wc",
            "du",
            "df",
            "tar",
            "zip",
            "unzip",
            "vim",
            "vi",
            "nano",
            "emacs",
            "code",
            "open",
        }

        # Check each token that might be a path
        current_command = None
        piped_command = False  # Track if command comes after a pipe
        skip_next = False  # Track if we should skip the next token (e.g., heredoc delimiter)
        for i, token in enumerate(tokens):
            # Skip token if marked by previous iteration (e.g., heredoc delimiter)
            if skip_next:
                skip_next = False
                continue

            # Skip shell operators (including heredoc operators)
            if token in ["&&", "||", ";", "|", "&", ">", ">>", "<", "<<", "<<<", "2>", "&>"]:
                if token == "|":
                    piped_command = True
                elif token in ["&&", "||", ";"]:
                    piped_command = False
                elif token in ["<<", "<<<"]:
                    # Heredoc operator - next token is the delimiter, not a path
                    skip_next = True
                continue

            # Skip flags and options
            if token.startswith("-"):
                continue

            # Check if this is a command
            if i == 0 or tokens[i - 1] in ["&&", "||", ";", "|"]:
                current_command = token.split("/")[-1]  # Get base command name
                # Don't validate grep/awk/sed arguments after pipes - they're patterns not paths
                if piped_command and current_command in ["grep", "awk", "sed", "sort", "uniq", "wc"]:
                    current_command = None
                if tokens[i - 1] in ["&&", "||", ";"]:
                    piped_command = False
                continue

            # Check for redirections (but not heredoc delimiters)
            if i > 0 and tokens[i - 1] in [">", ">>", "<", "2>", "&>"]:
                # This is a file path for redirection
                # Note: heredoc delimiters (after << or <<<) are handled above via skip_next
                self._validate_path_token(token, f"redirect to/from '{token}'")
                continue

            # Check if current command takes path arguments
            if current_command in path_commands:
                # Skip if it looks like an option value
                if i > 0 and tokens[i - 1].startswith("-"):
                    continue
                # This might be a path argument
                self._validate_path_token(token, f"access '{token}'")

            # Check for paths in other contexts (if they look like paths)
            elif "/" in token or token in [".", "..", "~"]:
                # This looks like a path, validate it
                with suppress(PathValidationError):
                    # It might not be a path, just a string with slash
                    # We'll be lenient here if it fails
                    self._validate_path_token(token, f"access '{token}'")

    def _validate_path_token(self, token: str, operation: str) -> None:
        """Validate a single path token from a command.

        Args:
            token: The token that might be a path
            operation: Description of the operation

        Raises:
            PathValidationError: If the path is not allowed
        """
        # Expand user home directory
        if token.startswith("~"):
            token = str(Path(token).expanduser())

        # Skip URLs and remote paths
        if (
            token.startswith("http://")
            or token.startswith("https://")
            or token.startswith("ftp://")
            or token.startswith("ssh://")
            or token.startswith("git@")
            or ":" in token.split("/")[0]
        ):  # user@host:path
            return

        # Try to validate as a path
        try:
            path = Path(token)
            # If it's a relative path, resolve it from CWD
            if not path.is_absolute():
                path = Path.cwd() / path
            self.validate_path(path, operation)
        except (ValueError, OSError):
            # Not a valid path, skip validation
            pass

    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed directories.

        Args:
            path: The path to check (should be absolute)

        Returns:
            True if path is allowed, False otherwise
        """
        # Ensure path is absolute
        path = path.resolve()
        log(f"Validating path: {path}")

        # Check if path is under any allowed directory
        for allowed_dir in self.allowed_directories:
            try:
                # Check if path is relative to allowed_dir
                path.relative_to(allowed_dir)
                return True
            except ValueError:
                # path is not relative to this allowed_dir
                continue

        return False

    def _is_parent_of(self, parent: Path, child: Path) -> bool:
        """Check if parent is a parent directory of child.

        Args:
            parent: Potential parent path
            child: Potential child path

        Returns:
            True if parent is a parent of child
        """
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def get_allowed_directories(self) -> list[Path]:
        """Get the list of allowed directories.

        Returns:
            List of allowed directory paths
        """
        return self.allowed_directories.copy()
