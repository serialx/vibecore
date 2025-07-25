"""Path utilities for session file management."""

from pathlib import Path


def canonicalize_path(path: Path) -> str:
    """Convert a path to a safe directory name.

    Converts absolute paths to a safe format suitable for use as a directory name.
    Replaces path separators with hyphens to create a flat namespace.

    Args:
        path: The path to canonicalize

    Returns:
        A canonicalized string safe for use as a directory name

    Example:
        >>> canonicalize_path(Path("/Users/serialx/workspace/vibecore"))
        '-Users-serialx-workspace-vibecore'
    """
    # Resolve to absolute path and convert to string
    absolute_path = path.resolve()
    path_str = str(absolute_path)

    # Replace path separators with hyphens
    # This creates a flat namespace while preserving path uniqueness
    canonicalized = path_str.replace("/", "-")

    # Handle Windows paths (replace backslashes and colons)
    canonicalized = canonicalized.replace("\\", "-")
    canonicalized = canonicalized.replace(":", "")

    # Remove any leading/trailing hyphens that might occur
    canonicalized = canonicalized.strip("-")

    # Ensure we always have a non-empty result
    if not canonicalized:
        canonicalized = "root"

    return canonicalized


def get_session_file_path(
    session_id: str,
    project_path: Path,
    base_dir: Path,
) -> Path:
    """Construct the full path to a session file.

    Creates a path structure like:
    {base_dir}/projects/{canonicalized_project_path}/{session_id}.jsonl

    Args:
        session_id: Unique identifier for the session
        project_path: Project path to canonicalize
        base_dir: Base directory for sessions (e.g., ~/.vibecore)

    Returns:
        Full path to the session file

    Example:
        >>> get_session_file_path(
        ...     "chat-2024-01-15",
        ...     Path("/Users/serialx/workspace/vibecore"),
        ...     Path.home() / ".vibecore"
        ... )
        PosixPath('/Users/serialx/.vibecore/projects/-Users-serialx-workspace-vibecore/chat-2024-01-15.jsonl')
    """
    # Validate session_id to prevent directory traversal
    if "/" in session_id or "\\" in session_id or ".." in session_id:
        raise ValueError(f"Invalid session_id: {session_id}")

    # Canonicalize the project path
    canonicalized_project = canonicalize_path(project_path)

    # Build the full path
    session_dir = base_dir / "projects" / canonicalized_project
    session_file = session_dir / f"{session_id}.jsonl"

    return session_file
