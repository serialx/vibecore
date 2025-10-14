"""File reading execution logic."""

from typing import Any

from agents import RunContextWrapper

from vibecore.context import PathValidatorContext
from vibecore.settings import settings
from vibecore.tools.file.utils import PathValidationError

from .utils import format_line_with_number


async def read_file(
    ctx: RunContextWrapper[PathValidatorContext], file_path: str, offset: int | None = None, limit: int | None = None
) -> str:
    """Read a file and return its contents in cat -n format.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        file_path: The path to the file to read
        offset: The line number to start reading from (1-based)
        limit: The maximum number of lines to read

    Returns:
        The file contents with line numbers, or an error message
    """
    try:
        # Validate the file path using context if path confinement is enabled
        if settings.path_confinement.enabled:
            validated_path = ctx.context.path_validator.validate_path(file_path, operation="read")
        else:
            # Fall back to simple validation against CWD
            from .utils import validate_file_path

            validated_path = validate_file_path(file_path)

        # Check if file exists
        if not validated_path.exists():
            return f"Error: File does not exist: {file_path}"

        # Check if it's a file (not a directory)
        if not validated_path.is_file():
            return f"Error: Path is not a file: {file_path}"

        # Check for Jupyter notebooks
        if validated_path.suffix == ".ipynb":
            return "Error: For Jupyter notebooks (.ipynb files), please use the NotebookRead tool instead"

        # Set defaults
        if offset is None:
            offset = 1  # Line numbers start at 1
        if limit is None:
            limit = 2000

        # Validate offset and limit
        if offset < 1:
            return "Error: Offset must be 1 or greater (line numbers start at 1)"
        if limit < 1:
            return "Error: Limit must be 1 or greater"

        # Read the file
        try:
            with validated_path.open("r", encoding="utf-8", errors="replace") as f:
                # Skip to the offset
                for _ in range(offset - 1):
                    line = f.readline()
                    if not line:
                        return f"Error: Offset {offset} is beyond the end of file"

                # Read the requested lines
                lines = []
                line_num = offset
                for _ in range(limit):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(format_line_with_number(line_num, line))
                    line_num += 1

                # Handle empty file or no content in range
                if not lines:
                    if offset == 1:
                        # Empty file
                        return "<system-reminder>Warning: The file exists but has empty contents</system-reminder>"
                    else:
                        return f"Error: No content found starting from line {offset}"

                return "\n".join(lines)

        except PermissionError:
            return f"Error: Permission denied reading file: {file_path}"
        except Exception as e:
            return f"Error reading file: {e}"

    except PathValidationError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: Unexpected error reading file: {e}"


async def edit_file(
    ctx: RunContextWrapper[PathValidatorContext],
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    """Edit a file by replacing strings.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        file_path: The path to the file to edit
        old_string: The text to replace
        new_string: The text to replace it with
        replace_all: Replace all occurrences (default: False)

    Returns:
        Success message or error message
    """
    try:
        # Validate the file path using context if path confinement is enabled
        if settings.path_confinement.enabled:
            validated_path = ctx.context.path_validator.validate_path(file_path, operation="edit")
        else:
            # Fall back to simple validation against CWD
            from .utils import validate_file_path

            validated_path = validate_file_path(file_path)

        # Check if file exists
        if not validated_path.exists():
            return f"Error: File does not exist: {file_path}"

        # Check if it's a file (not a directory)
        if not validated_path.is_file():
            return f"Error: Path is not a file: {file_path}"

        # Check for Jupyter notebooks
        if validated_path.suffix == ".ipynb":
            return "Error: For Jupyter notebooks (.ipynb files), please use the NotebookEdit tool instead"

        # Validate old_string != new_string
        if old_string == new_string:
            return "Error: old_string and new_string cannot be the same"

        # Read the file
        try:
            with validated_path.open("r", encoding="utf-8") as f:
                content = f.read()

            # Check if old_string exists in the file
            occurrences = content.count(old_string)
            if occurrences == 0:
                return f"Error: String not found in file: {old_string!r}"

            # Check uniqueness if not replace_all
            if not replace_all and occurrences > 1:
                return (
                    f"Error: Multiple occurrences ({occurrences}) of old_string found. "
                    f"Use replace_all=True or provide more context to make the string unique"
                )

            # Perform the replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replaced = occurrences
            else:
                new_content = content.replace(old_string, new_string, 1)
                replaced = 1

            # Write the file back
            with validated_path.open("w", encoding="utf-8") as f:
                f.write(new_content)

            return f"Successfully replaced {replaced} occurrence(s) in {file_path}"

        except PermissionError:
            return f"Error: Permission denied accessing file: {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"

    except PathValidationError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: Unexpected error editing file: {e}"


async def multi_edit_file(
    ctx: RunContextWrapper[PathValidatorContext],
    file_path: str,
    edits: list[dict[str, Any]],
) -> str:
    """Edit a file by applying multiple replacements sequentially.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        file_path: The path to the file to edit
        edits: List of edit operations, each containing old_string, new_string, and optional replace_all

    Returns:
        Success message or error message
    """
    try:
        # Validate the file path using context if path confinement is enabled
        if settings.path_confinement.enabled:
            validated_path = ctx.context.path_validator.validate_path(file_path, operation="multi_edit")
        else:
            # Fall back to simple validation against CWD
            from .utils import validate_file_path

            validated_path = validate_file_path(file_path)

        # Check if file exists
        if not validated_path.exists():
            return f"Error: File does not exist: {file_path}"

        # Check if it's a file (not a directory)
        if not validated_path.is_file():
            return f"Error: Path is not a file: {file_path}"

        # Check for Jupyter notebooks
        if validated_path.suffix == ".ipynb":
            return "Error: For Jupyter notebooks (.ipynb files), please use the NotebookEdit tool instead"

        # Read the file
        try:
            with validated_path.open("r", encoding="utf-8") as f:
                content = f.read()

            # Apply each edit sequentially
            total_replacements = 0
            for i, edit in enumerate(edits):
                old_string = str(edit["old_string"])
                new_string = str(edit["new_string"])
                replace_all = bool(edit.get("replace_all", False))

                # Validate old_string != new_string
                if old_string == new_string:
                    return f"Error: Edit {i + 1}: old_string and new_string cannot be the same"

                # Check if old_string exists in the current content
                occurrences = content.count(old_string)
                if occurrences == 0:
                    return f"Error: Edit {i + 1}: String not found: {old_string!r}"

                # Check uniqueness if not replace_all
                if not replace_all and occurrences > 1:
                    return (
                        f"Error: Edit {i + 1}: Multiple occurrences ({occurrences}) of old_string found. "
                        f"Use replace_all=True or provide more context to make the string unique"
                    )

                # Perform the replacement
                if replace_all:
                    content = content.replace(old_string, new_string)
                    total_replacements += occurrences
                else:
                    content = content.replace(old_string, new_string, 1)
                    total_replacements += 1

            # Write the file back
            with validated_path.open("w", encoding="utf-8") as f:
                f.write(content)

            return (
                f"Successfully applied {len(edits)} edits with {total_replacements} total replacements in {file_path}"
            )

        except PermissionError:
            return f"Error: Permission denied accessing file: {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"

    except PathValidationError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: Unexpected error editing file: {e}"


async def write_file(ctx: RunContextWrapper[PathValidatorContext], file_path: str, content: str) -> str:
    """Write content to a file.

    Args:
        ctx: The context wrapper containing the VibecoreContext
        file_path: The path to the file to write
        content: The content to write to the file

    Returns:
        Success message or error message
    """
    try:
        # Validate the file path using context if path confinement is enabled
        if settings.path_confinement.enabled:
            validated_path = ctx.context.path_validator.validate_path(file_path, operation="write")
        else:
            # Fall back to simple validation against CWD
            from .utils import validate_file_path

            validated_path = validate_file_path(file_path)

        # Check if it's a directory
        if validated_path.exists() and validated_path.is_dir():
            return f"Error: Path is a directory: {file_path}"

        # Check for Jupyter notebooks
        if validated_path.suffix == ".ipynb":
            return "Error: For Jupyter notebooks (.ipynb files), please use the NotebookEdit tool instead"

        # Create parent directories if they don't exist
        validated_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        try:
            with validated_path.open("w", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully wrote {len(content)} bytes to {file_path}"

        except PermissionError:
            return f"Error: Permission denied writing file: {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    except PathValidationError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: Unexpected error writing file: {e}"
