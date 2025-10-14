from typing import TYPE_CHECKING

from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions

from vibecore.context import FullVibecoreContext
from vibecore.settings import settings
from vibecore.tools.file.tools import edit, multi_edit, read, write
from vibecore.tools.python.tools import execute_python
from vibecore.tools.shell.tools import bash, glob, grep, ls
from vibecore.tools.task.tools import task
from vibecore.tools.todo.tools import todo_read, todo_write
from vibecore.tools.webfetch.tools import webfetch
from vibecore.tools.websearch.tools import websearch

from .prompts import COMMON_PROMPT

if TYPE_CHECKING:
    from agents.mcp import MCPServer

INSTRUCTIONS = (
    COMMON_PROMPT + "\n\n"
    "You are a versatile AI assistant capable of helping with a wide range of tasks. "
    "You have access to various tools including file operations, shell commands, "
    "Python execution, and task management. "
    "Use the appropriate tools to accomplish any task the user requests. "
    "You can handle programming, system administration, file manipulation, "
    "automation, and general problem-solving tasks."
)


def create_default_agent(mcp_servers: list["MCPServer"] | None = None) -> Agent[FullVibecoreContext]:
    """Create the general-purpose agent with appropriate tools.

    Args:
        mcp_servers: Optional list of MCP servers to connect to.

    Returns:
        Configured general-purpose agent.
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
        task,
        websearch,
        webfetch,
    ]
    instructions = INSTRUCTIONS

    instructions = prompt_with_handoff_instructions(instructions)

    return Agent[FullVibecoreContext](
        name="Vibecore Agent",
        handoff_description="A versatile general-purpose assistant",
        instructions=instructions,
        tools=tools,
        model=settings.model,
        model_settings=settings.default_model_settings,
        handoffs=[],
        mcp_servers=mcp_servers or [],
    )


# Create default agent without MCP servers for backward compatibility
default_agent = create_default_agent()
