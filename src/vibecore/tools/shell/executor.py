"""Shell command execution logic."""

import asyncio
import glob as glob_module
import re
import subprocess
from pathlib import Path

from agents import RunContextWrapper

from vibecore.context import PathValidatorContext
from vibecore.settings import settings
from vibecore.tools.file.utils import PathValidationError, validate_file_path


async def bash_executor(
    ctx: RunContextWrapper[PathValidatorContext], command: str, timeout: int | None = None
) -> tuple[str, int]:
    """Execute a bash command asynchronously.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        command: The bash command to execute
        timeout: Optional timeout in milliseconds (max 600000)

    Returns:
        Tuple of (output, exit_code)
    """
    # Set default timeout if not provided
    if timeout is None:
        timeout = 120000  # 2 minutes default

    # Validate timeout
    if timeout < 0:
        return "Error: Timeout must be positive", 1
    if timeout > 600000:
        return "Error: Timeout cannot exceed 600000ms (10 minutes)", 1

    # Convert timeout to seconds
    timeout_seconds = timeout / 1000.0

    # Validate command paths if path confinement is enabled
    if settings.path_confinement.enabled:
        try:
            ctx.context.path_validator.validate_command_paths(command)
        except PathValidationError as e:
            return f"Error: {e}", 1

    process = None
    try:
        # Create subprocess
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            executable="/bin/bash",
        )

        # Wait for completion with timeout
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout_seconds)

        # Decode output
        output = stdout.decode("utf-8", errors="replace")

        # Truncate if too long
        if len(output) > 30000:
            output = output[:30000] + "\n... (output truncated)"

        return output, process.returncode or 0

    except TimeoutError:
        # Kill the process if it times out
        if process and process.returncode is None:
            process.kill()
            await process.wait()
        return f"Error: Command timed out after {timeout}ms", 124

    except Exception as e:
        return f"Error executing command: {e}", 1


async def glob_files(ctx: RunContextWrapper[PathValidatorContext], pattern: str, path: str | None = None) -> list[str]:
    """Find files matching a glob pattern.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        pattern: The glob pattern to match
        path: Optional directory to search in (defaults to CWD)

    Returns:
        List of matching file paths sorted by modification time
    """
    try:
        # Validate and resolve the path
        if path is None:
            search_path = Path.cwd()
            # Validate CWD is in allowed directories if path confinement is enabled
            if settings.path_confinement.enabled:
                try:
                    ctx.context.path_validator.validate_path(search_path, operation="glob")
                except PathValidationError as e:
                    return [f"Error: {e}"]
        else:
            # Validate the provided path
            if settings.path_confinement.enabled:
                try:
                    search_path = ctx.context.path_validator.validate_path(path, operation="glob")
                except PathValidationError as e:
                    return [f"Error: {e}"]
            else:
                search_path = validate_file_path(path)

        # Validate path is a directory
        if not search_path.is_dir():
            return [f"Error: Path is not a directory: {search_path}"]
    except PathValidationError as e:
        return [f"Error: {e}"]

    try:
        # Convert to absolute path
        search_path = search_path.resolve()

        # Perform glob search
        full_pattern = str(search_path / pattern)
        matches = list(glob_module.glob(full_pattern, recursive=True))

        # Filter to only files (not directories)
        file_matches = [m for m in matches if Path(m).is_file()]

        # Sort by modification time (newest first)
        file_matches.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)

        # Return relative paths if searching in CWD, absolute otherwise
        if path is None:
            file_matches = [str(Path(m).relative_to(Path.cwd())) for m in file_matches]

        return file_matches

    except Exception as e:
        return [f"Error: {e}"]


async def grep_files(
    ctx: RunContextWrapper[PathValidatorContext], pattern: str, path: str | None = None, include: str | None = None
) -> list[str]:
    """Search file contents using regular expressions.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        pattern: The regex pattern to search for
        path: Directory to search in (defaults to CWD)
        include: File pattern to include (e.g. "*.js")

    Returns:
        List of file paths containing matches, sorted by modification time
    """
    try:
        # Validate and resolve the path
        if path is None:
            search_path = Path.cwd()
            # Validate CWD is in allowed directories if path confinement is enabled
            if settings.path_confinement.enabled:
                try:
                    ctx.context.path_validator.validate_path(search_path, operation="grep")
                except PathValidationError as e:
                    return [f"Error: {e}"]
        else:
            # Validate the provided path
            if settings.path_confinement.enabled:
                try:
                    search_path = ctx.context.path_validator.validate_path(path, operation="grep")
                except PathValidationError as e:
                    return [f"Error: {e}"]
            else:
                search_path = validate_file_path(path)

        # Validate path is a directory
        if not search_path.is_dir():
            return [f"Error: Path is not a directory: {search_path}"]
    except PathValidationError as e:
        return [f"Error: {e}"]

    try:
        # Compile regex pattern
        regex = re.compile(pattern)
    except re.error as e:
        return [f"Error: Invalid regex pattern: {e}"]

    try:
        # Get all files to search
        if include:
            # Use glob to find files matching the include pattern
            search_pattern = "**/" + include
            all_files = list(search_path.glob(search_pattern))
        else:
            # Search all files recursively
            all_files = [f for f in search_path.rglob("*") if f.is_file()]

        # Search for pattern in each file
        matching_files = []
        for file_path in all_files:
            try:
                # Skip binary files
                with file_path.open("r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    if regex.search(content):
                        matching_files.append(file_path)
            except Exception:
                # Skip files that can't be read
                continue

        # Sort by modification time (newest first)
        matching_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Return relative paths if searching in CWD, absolute otherwise
        if path is None:
            result = [str(f.relative_to(Path.cwd())) for f in matching_files]
        else:
            result = [str(f) for f in matching_files]

        return result

    except Exception as e:
        return [f"Error: {e}"]


async def list_directory(
    ctx: RunContextWrapper[PathValidatorContext], path: str, ignore: list[str] | None = None
) -> list[str]:
    """List files and directories in a given path.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        path: The absolute path to list
        ignore: Optional list of glob patterns to ignore

    Returns:
        List of entries in the directory
    """
    try:
        # Validate and resolve the path
        if settings.path_confinement.enabled:
            dir_path = ctx.context.path_validator.validate_path(path, operation="list")
        else:
            dir_path = validate_file_path(path)

        # Validate path is a directory
        if not dir_path.is_dir():
            return [f"Error: Path is not a directory: {dir_path}"]
    except PathValidationError as e:
        return [f"Error: {e}"]

    try:
        # Get all entries
        entries = []
        for entry in sorted(dir_path.iterdir()):
            # Skip if matches ignore pattern
            if ignore:
                skip = False
                for pattern in ignore:
                    if entry.match(pattern):
                        skip = True
                        break
                if skip:
                    continue

            # Format entry
            if entry.is_dir():
                entries.append(f"{entry.name}/")
            else:
                entries.append(entry.name)

        return entries

    except PermissionError:
        return [f"Error: Permission denied accessing directory: {path}"]
    except Exception as e:
        return [f"Error: {e}"]
