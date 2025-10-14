"""Shell and system tools for Vibecore agents."""

from agents import RunContextWrapper, function_tool

from vibecore.context import PathValidatorContext

from .executor import bash_executor, glob_files, grep_files, list_directory


@function_tool
async def bash(
    ctx: RunContextWrapper[PathValidatorContext],
    command: str,
    timeout: int | None = None,
    description: str | None = None,
) -> str:
    """Executes a given bash command in a persistent shell session with optional timeout, ensuring proper handling
    and security measures.

    Before executing the command, please follow these steps:

    1. Directory Verification:
       - If the command will create new directories or files, first use the LS tool to verify the parent directory
         exists and is the correct location
       - For example, before running "mkdir foo/bar", first use LS to check that "foo" exists and is the intended
         parent directory

    2. Command Execution:
       - Always quote file paths that contain spaces with double quotes (e.g., cd "path with spaces/file.txt")
       - Examples of proper quoting:
         - cd "/Users/name/My Documents" (correct)
         - cd /Users/name/My Documents (incorrect - will fail)
         - python "/path/with spaces/script.py" (correct)
         - python /path/with spaces/script.py (incorrect - will fail)
       - After ensuring proper quoting, execute the command.
       - Capture the output of the command.

    Usage notes:
      - The command argument is required.
      - You can specify an optional timeout in milliseconds (up to 600000ms / 10 minutes). If not specified, commands
        will timeout after 120000ms (2 minutes).
      - It is very helpful if you write a clear, concise description of what this command does in 5-10 words.
      - If the output exceeds 30000 characters, output will be truncated before being returned to you.
      - VERY IMPORTANT: You MUST avoid using search commands like `find` and `grep`. Instead use Grep, Glob, or Task
        to search. You MUST avoid read tools like `cat`, `head`, `tail`, and `ls`, and use Read and LS to read files.
      - If you _still_ need to run `grep`, STOP. ALWAYS USE ripgrep at `rg` first, which all users have pre-installed.
      - When issuing multiple commands, use the ';' or '&&' operator to separate them. DO NOT use newlines (newlines
        are ok in quoted strings).
      - Try to maintain your current working directory throughout the session by using absolute paths and avoiding
        usage of `cd`. You may use `cd` if the User explicitly requests it.

    Args:
        ctx: The run context wrapper
        command: The command to execute
        timeout: Optional timeout in milliseconds (max 600000)
        description: Clear, concise description of what this command does in 5-10 words

    Returns:
        The command output or error message
    """
    output, exit_code = await bash_executor(ctx, command, timeout)
    if exit_code != 0:
        return f"{output}\nExit code: {exit_code}"
    return output


@function_tool
async def glob(
    ctx: RunContextWrapper[PathValidatorContext],
    pattern: str,
    path: str | None = None,
) -> str:
    """Fast file pattern matching tool that works with any codebase size.

    - Supports glob patterns like "**/*.js" or "src/**/*.ts"
    - Returns matching file paths sorted by modification time
    - Use this tool when you need to find files by name patterns
    - When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the
      Agent tool instead
    - You have the capability to call multiple tools in a single response. It is always better to speculatively
      perform multiple searches as a batch that are potentially useful.

    Args:
        ctx: The run context wrapper
        pattern: The glob pattern to match files against
        path: The directory to search in. If not specified, the current working directory will be used.
              IMPORTANT: Omit this field to use the default directory. DO NOT enter "undefined" or "null" -
              simply omit it for the default behavior. Must be a valid directory path if provided.

    Returns:
        List of matching file paths, one per line
    """
    files = await glob_files(ctx, pattern, path)
    if files and files[0].startswith("Error:"):
        return files[0]
    return "\n".join(files) if files else "No files found matching pattern"


@function_tool
async def grep(
    ctx: RunContextWrapper[PathValidatorContext],
    pattern: str,
    path: str | None = None,
    include: str | None = None,
) -> str:
    """Fast content search tool that works with any codebase size.

    - Searches file contents using regular expressions
    - Supports full regex syntax (eg. "log.*Error", "function\\s+\\w+", etc.)
    - Filter files by pattern with the include parameter (eg. "*.js", "*.{ts,tsx}")
    - Returns file paths with at least one match sorted by modification time
    - Use this tool when you need to find files containing specific patterns
    - If you need to identify/count the number of matches within files, use the Bash tool with `rg` (ripgrep)
      directly. Do NOT use `grep`.
    - When you are doing an open ended search that may require multiple rounds of globbing and grepping, use the
      Agent tool instead

    Args:
        ctx: The run context wrapper
        pattern: The regular expression pattern to search for in file contents
        path: The directory to search in. Defaults to the current working directory.
        include: File pattern to include in the search (e.g. "*.js", "*.{ts,tsx}")

    Returns:
        List of file paths containing matches, one per line
    """
    files = await grep_files(ctx, pattern, path, include)
    if files and files[0].startswith("Error:"):
        return files[0]
    return "\n".join(files) if files else "No files found containing pattern"


@function_tool
async def ls(
    ctx: RunContextWrapper[PathValidatorContext],
    path: str,
    ignore: list[str] | None = None,
) -> str:
    """Lists files and directories in a given path.

    The path parameter must be an absolute path, not a relative path. You can optionally provide an array of glob
    patterns to ignore with the ignore parameter. You should generally prefer the Glob and Grep tools, if you know
    which directories to search.

    Args:
        ctx: The run context wrapper
        path: The absolute path to the directory to list (must be absolute, not relative)
        ignore: List of glob patterns to ignore

    Returns:
        List of entries in the directory, one per line
    """
    entries = await list_directory(ctx, path, ignore)
    if entries and entries[0].startswith("Error:"):
        return entries[0]
    return "\n".join(entries) if entries else "Empty directory"
