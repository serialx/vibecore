"""File reading tool for Vibecore agents."""

from agents import RunContextWrapper, function_tool
from pydantic import BaseModel

from vibecore.context import PathValidatorContext

from .executor import edit_file, multi_edit_file, read_file, write_file


class EditOperation(BaseModel):
    """Represents a single edit operation."""

    old_string: str
    new_string: str
    replace_all: bool = False


@function_tool
async def read(
    ctx: RunContextWrapper[PathValidatorContext],
    file_path: str,
    offset: int | None = None,
    limit: int | None = None,
) -> str:
    """Reads a file from the local filesystem. You can access any file directly by using this tool.
    Assume this tool is able to read all files on the machine. If the User provides a path to a file assume
    that path is valid. It is okay to read a file that does not exist; an error will be returned.

    Usage:
    - The file_path parameter must be an absolute path, not a relative path
    - By default, it reads up to 2000 lines starting from the beginning of the file
    - You can optionally specify a line offset and limit (especially handy for long files), but it's
      recommended to read the whole file by not providing these parameters
    - Any lines longer than 2000 characters will be truncated
    - Results are returned using cat -n format, with line numbers starting at 1
    - For Jupyter notebooks (.ipynb files), use the NotebookRead instead
    - You have the capability to call multiple tools in a single response. It is always better to
      speculatively read multiple files as a batch that are potentially useful.
    - If you read a file that exists but has empty contents you will receive a system reminder warning
      in place of file contents.

    Args:
        ctx: The run context wrapper
        file_path: The absolute path to the file to read
        offset: The line number to start reading from. Only provide if the file is too large to read at once
        limit: The number of lines to read. Only provide if the file is too large to read at once.

    Returns:
        The file contents with line numbers in cat -n format, or an error message
    """
    return await read_file(ctx, file_path, offset, limit)


@function_tool
async def edit(
    ctx: RunContextWrapper[PathValidatorContext],
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> str:
    """Performs exact string replacements in files.

    Usage:
    - You must use your `Read` tool at least once in the conversation before editing. This tool will error if you
      attempt an edit without reading the file.
    - When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears
      AFTER the line number prefix. The line number prefix format is: spaces + line number + tab. Everything after
      that tab is the actual file content to match. Never include any part of the line number prefix in the
      old_string or new_string.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - The edit will FAIL if `old_string` is not unique in the file. Either provide a larger string with more
      surrounding context to make it unique or use `replace_all` to change every instance of `old_string`.
    - Use `replace_all` for replacing and renaming strings across the file. This parameter is useful if you want to
      rename a variable for instance.

    Args:
        ctx: The run context wrapper
        file_path: The absolute path to the file to modify
        old_string: The text to replace
        new_string: The text to replace it with (must be different from old_string)
        replace_all: Replace all occurences of old_string (default false)

    Returns:
        Success message or error message
    """
    return await edit_file(ctx, file_path, old_string, new_string, replace_all)


@function_tool
async def multi_edit(
    ctx: RunContextWrapper[PathValidatorContext],
    file_path: str,
    edits: list[EditOperation],
) -> str:
    """This is a tool for making multiple edits to a single file in one operation. It is built on top of the Edit
    tool and allows you to perform multiple find-and-replace operations efficiently. Prefer this tool over the Edit
    tool when you need to make multiple edits to the same file.

    Before using this tool:

    1. Use the Read tool to understand the file's contents and context
    2. Verify the directory path is correct

    To make multiple file edits, provide the following:
    1. file_path: The absolute path to the file to modify (must be absolute, not relative)
    2. edits: An array of edit operations to perform, where each edit contains:
       - old_string: The text to replace (must match the file contents exactly, including all whitespace and
         indentation)
       - new_string: The edited text to replace the old_string
       - replace_all: Replace all occurences of old_string. This parameter is optional and defaults to false.

    IMPORTANT:
    - All edits are applied in sequence, in the order they are provided
    - Each edit operates on the result of the previous edit
    - All edits must be valid for the operation to succeed - if any edit fails, none will be applied
    - This tool is ideal when you need to make several changes to different parts of the same file
    - For Jupyter notebooks (.ipynb files), use the NotebookEdit instead

    CRITICAL REQUIREMENTS:
    1. All edits follow the same requirements as the single Edit tool
    2. The edits are atomic - either all succeed or none are applied
    3. Plan your edits carefully to avoid conflicts between sequential operations

    WARNING:
    - The tool will fail if edits.old_string doesn't match the file contents exactly (including whitespace)
    - The tool will fail if edits.old_string and edits.new_string are the same
    - Since edits are applied in sequence, ensure that earlier edits don't affect the text that later edits are
      trying to find

    When making edits:
    - Ensure all edits result in idiomatic, correct code
    - Do not leave the code in a broken state
    - Always use absolute file paths (starting with /)
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - Use replace_all for replacing and renaming strings across the file. This parameter is useful if you want to
      rename a variable for instance.

    If you want to create a new file, use:
    - A new file path, including dir name if needed
    - First edit: empty old_string and the new file's contents as new_string
    - Subsequent edits: normal edit operations on the created content

    Args:
        ctx: The run context wrapper
        file_path: The absolute path to the file to modify
        edits: Array of edit operations to perform sequentially on the file

    Returns:
        Success message or error message
    """
    # Convert EditOperation objects to dictionaries
    edit_dicts = [edit.model_dump() for edit in edits]
    return await multi_edit_file(ctx, file_path, edit_dicts)


@function_tool
async def write(
    ctx: RunContextWrapper[PathValidatorContext],
    file_path: str,
    content: str,
) -> str:
    """Writes a file to the local filesystem.

    Usage:
    - This tool will overwrite the existing file if there is one at the provided path.
    - If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail
      if you did not read the file first.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - NEVER proactively create documentation files (*.md) or README files. Only create documentation files if
      explicitly requested by the User.
    - Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked.

    Args:
        ctx: The run context wrapper
        file_path: The absolute path to the file to write (must be absolute, not relative)
        content: The content to write to the file

    Returns:
        Success message or error message
    """
    return await write_file(ctx, file_path, content)
