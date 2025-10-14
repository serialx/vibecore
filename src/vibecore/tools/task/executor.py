"""Task execution logic for spawning sub-agents."""

import traceback

from agents import (
    Runner,
)
from textual import log

from vibecore.agents.task import create_task_agent
from vibecore.context import FullVibecoreContext
from vibecore.settings import settings


async def execute_task(
    context: FullVibecoreContext,
    description: str,
    prompt: str,
    tool_name: str,
    tool_call_id: str,
) -> str:
    """Execute a task using a sub-agent with streaming support.

    Args:
        context: The vibecore context to pass to the task agent
        description: Short task description (for logging/display)
        prompt: Full task instructions
        tool_name: Name of the tool being invoked (e.g., "task")
        tool_call_id: Unique identifier for this tool call

    Returns:
        Task execution results as a string with formatted sub-agent activity
    """
    try:
        # Create the task agent
        task_agent = create_task_agent(prompt)

        # Run the task agent with streaming
        result = Runner.run_streamed(task_agent, prompt, context=context, max_turns=settings.max_turns)

        # Check if app is available for streaming
        if context.app:
            # Stream events to app handler
            async for event in result.stream_events():
                await context.app.handle_task_tool_event(tool_name, tool_call_id, event)

        return result.final_output

    except Exception as e:
        log.error(f"Task execution error: {type(e).__name__}: {e!s}\n%s", traceback.format_exc())
        return f"Task '{description}' failed with error: {e!s}"
