"""Task tool for spawning sub-agents to execute specific tasks."""

from agents import function_tool
from agents.tool_context import ToolContext

from vibecore.context import FullVibecoreContext

from .executor import execute_task


@function_tool
async def task(
    ctx: ToolContext[FullVibecoreContext],
    description: str,
    prompt: str,
) -> str:
    """Launch a new agent to execute a specific task with access to all tools except the Task tool itself.

    The task agent has access to: bash, glob, grep, ls, read, edit, multi_edit, write, execute_python,
    todo_read, and todo_write. Use this tool when you need to delegate complex, multi-step operations
    or searches to a sub-agent.

    When to use the Task tool:
    - When searching for a keyword like "config" or "logger" across many files
    - For questions like "which file does X?" where you're not sure of the location
    - When you need to perform complex multi-step operations autonomously
    - When the task requires extensive file exploration or analysis

    When NOT to use the Task tool:
    - If you want to read a specific file path (use Read instead)
    - If searching for a specific class definition like "class Foo" (use Grep instead)
    - If searching within a specific file or set of 2-3 files (use Read instead)
    - For simple, single-step operations (use the appropriate tool directly)

    Usage notes:
    1. Launch multiple tasks concurrently when possible by using multiple tool calls
    2. The task agent returns a single final message - you should summarize results for the user
    3. Each task invocation is stateless - provide complete instructions in the prompt
    4. Clearly specify whether the agent should write code or just research/analyze
    5. The agent is not aware of the user's original request - be explicit in instructions

    Args:
        ctx: The run context wrapper
        description: A short task description (3-5 words)
        prompt: Full task instructions for the agent - be highly detailed and specify
                exactly what information should be returned

    Returns:
        The task execution results as a string
    """
    return await execute_task(ctx.context, description, prompt, ctx.tool_name, ctx.tool_call_id)
