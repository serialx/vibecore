"""Task-specific agent configuration for executing delegated tasks."""

from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from vibecore.context import FullVibecoreContext
from vibecore.settings import settings
from vibecore.tools.file.tools import edit, multi_edit, read, write
from vibecore.tools.python.tools import execute_python
from vibecore.tools.shell.tools import bash, glob, grep, ls
from vibecore.tools.todo.tools import todo_read, todo_write

from .prompts import COMMON_PROMPT


def create_task_agent(prompt: str) -> Agent[FullVibecoreContext]:
    """Create a task agent with all tools except the Task tool.

    This agent is used by the Task tool to execute specific tasks.
    It has access to all tools except the Task tool itself to prevent
    infinite recursion.

    Args:
        prompt: The task-specific instructions to add to the agent

    Returns:
        Configured task agent
    """
    # Same tools as default agent, but excluding task tool
    tools: list = [
        todo_read,
        todo_write,
        execute_python,
        read,
        edit,
        multi_edit,
        write,
        bash,
        glob,
        grep,
        ls,
    ]

    instructions = (
        COMMON_PROMPT + "\n\n"
        "You are a task-specific AI agent. Your purpose is to complete the following task:\n\n"
        f"{prompt}\n\n"
        "Focus on completing this specific task using the tools available to you. "
        "Provide clear results and any relevant findings."
    )

    instructions = prompt_with_handoff_instructions(instructions)

    return Agent[FullVibecoreContext](
        name="Task Agent",
        handoff_description="A task-specific agent",
        instructions=instructions,
        tools=tools,
        model=settings.model,
        model_settings=settings.default_model_settings,
        handoffs=[],
    )
