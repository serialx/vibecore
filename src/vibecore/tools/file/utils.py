"""Path validation utilities for file tools."""

from pathlib import Path


class PathValidationError(Exception):
    """Raised when a path validation fails."""

    pass


def validate_file_path(file_path: str, base_dir: Path | None = None) -> Path:
    """Validate and resolve a file path, ensuring it's within the allowed directory.

    Args:
        file_path: The file path to validate (can be relative or absolute)
        base_dir: The base directory to restrict access to (defaults to CWD)

    Returns:
        The validated absolute Path object

    Raises:
        PathValidationError: If the path is invalid or outside the allowed directory
    """
    if base_dir is None:
        base_dir = Path.cwd()

    base_dir = base_dir.resolve()

    try:
        # Convert to Path object
        path = Path(file_path)

        # If relative, make it absolute relative to base_dir
        if not path.is_absolute():
            path = base_dir / path

        # Resolve to get the canonical path (resolves symlinks, .., etc)
        resolved_path = path.resolve()

        # Check if the resolved path is within the base directory
        # This prevents directory traversal attacks
        try:
            resolved_path.relative_to(base_dir)
        except ValueError:
            raise PathValidationError(
                f"Path '{file_path}' is outside the allowed directory. "
                f"Access is restricted to '{base_dir}' and its subdirectories."
            ) from None

        return resolved_path

    except Exception as e:
        if isinstance(e, PathValidationError):
            raise
        raise PathValidationError(f"Invalid path '{file_path}': {e}") from e


def format_line_with_number(line_num: int, line: str, max_length: int = 2000) -> str:
    """Format a line with line number in cat -n style.

    Args:
        line_num: The line number (1-based)
        line: The line content
        max_length: Maximum length for the line content

    Returns:
        Formatted line with line number
    """
    # Truncate line if too long
    if len(line) > max_length:
        line = line[:max_length] + "... (truncated)"

    # Remove trailing newline for consistent formatting
    line = line.rstrip("\n")

    # Format with right-aligned line number (6 spaces wide) followed by tab
    return f"{line_num:6d}\t{line}"
