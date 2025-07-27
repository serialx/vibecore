"""Task execution logic for spawning sub-agents."""

from agents import Runner

from vibecore.agents.task_agent import create_task_agent
from vibecore.context import VibecoreContext
from vibecore.settings import settings


async def execute_task(
    context: VibecoreContext,
    description: str,
    prompt: str,
) -> str:
    """Execute a task using a sub-agent.

    Args:
        context: The vibecore context to pass to the task agent
        description: Short task description (for logging/display)
        prompt: Full task instructions

    Returns:
        Task execution results as a string
    """
    try:
        # Create the task agent
        task_agent = create_task_agent(prompt)

        # Run the task agent
        result = await Runner.run(task_agent, prompt, context=context, max_turns=settings.max_turns)

        # Extract and format the response
        if result.final_output:
            return f"Task '{description}' completed:\n\n{result.final_output}"
        elif result.new_items:
            # Collect all text content from the response
            output_parts = []

            for item in result.new_items:
                # Handle message output items
                if hasattr(item, "type") and item.type == "message_output_item":
                    if hasattr(item.raw_item, "content"):
                        content = item.raw_item.content
                        if isinstance(content, list):
                            for part in content:
                                if hasattr(part, "type") and part.type == "text" and hasattr(part, "text"):
                                    output_parts.append(part.text)
                        elif isinstance(content, str):
                            output_parts.append(content)

                # Handle tool outputs
                elif hasattr(item, "type") and item.type == "tool_call_output_item":
                    # Just collect the string representation
                    output_parts.append(f"[Tool output: {item!s}]")

            if output_parts:
                return f"Task '{description}' completed:\n\n{''.join(output_parts)}"
            else:
                return f"Task '{description}' completed with no readable output."
        else:
            return f"Task '{description}' completed with no output."

    except Exception as e:
        return f"Task '{description}' failed with error: {e!s}"
