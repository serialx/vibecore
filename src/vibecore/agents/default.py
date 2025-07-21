from pathlib import Path

from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from vibecore.context import VibecoreContext
from vibecore.settings import settings
from vibecore.tools.file.tools import edit, multi_edit, read, write
from vibecore.tools.python.tools import execute_python
from vibecore.tools.shell.tools import bash, glob, grep, ls
from vibecore.tools.todo.tools import todo_read, todo_write


def load_common_prompt() -> str:
    """Load the common system prompt from file."""
    prompt_file = Path(__file__).parent.parent / "prompts" / "common_system_prompt.txt"
    return prompt_file.read_text()


COMMON_PROMPT = load_common_prompt()

INSTRUCTIONS = (
    COMMON_PROMPT + "\n\n"
    "You provide assistance with data anlysis and processing. "
    "You can use the `execute_python` tool to run Python code for data analysis and processing. "
    "You can also use the `todo_read` and `todo_write` tools to manage tasks and track progress. "
    "ALWAYS prefer using SQL queries over Python code when you can. "
    "Use python for analysis that is not possible with SQL like plotting, correlation, regression, etc. "
    "NEVER use `execute_python` to output Markdown reports. Output in regular response."
)


def create_analysis_agent() -> Agent[VibecoreContext]:
    """Create the data analysis agent with appropriate tools.

    Args:
        include_databricks: Whether to include Databricks query tool.

    Returns:
        Configured data analysis agent.
    """
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
    instructions = INSTRUCTIONS

    instructions = prompt_with_handoff_instructions(instructions)

    return Agent[VibecoreContext](
        name="Vibecore Agent",
        handoff_description="An helpful agent",
        instructions=instructions,
        tools=tools,
        model=settings.model,
        handoffs=[],  # Will be set dynamically in main.py
    )


# Create default agent without Databricks for backward compatibility
default_agent = create_analysis_agent()
