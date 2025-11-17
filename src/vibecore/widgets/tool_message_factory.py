"""Factory for creating tool-specific message widgets.

This module provides a centralized way to create the appropriate message widget
based on tool name and arguments, avoiding duplication between stream handling
and session loading.
"""

import contextlib
import json
from typing import Any

from vibecore.settings import settings
from vibecore.widgets.messages import MessageStatus
from vibecore.widgets.tool_messages import (
    BaseToolMessage,
    BashToolMessage,
    MCPToolMessage,
    PythonToolMessage,
    ReadToolMessage,
    RichToolMessage,
    TaskToolMessage,
    TodoWriteToolMessage,
    ToolMessage,
    WebFetchToolMessage,
    WebSearchToolMessage,
    WriteToolMessage,
)


def create_tool_message(
    tool_name: str,
    arguments: str,
    output: str | None = None,
    status: MessageStatus = MessageStatus.EXECUTING,
) -> BaseToolMessage:
    """Create the appropriate tool message widget based on tool name.

    This factory function centralizes the logic for creating tool-specific
    message widgets, ensuring consistency between streaming and session loading.

    Args:
        tool_name: Name of the tool being called
        arguments: JSON string of tool arguments
        output: Optional output from tool execution
        status: Status of the tool execution

    Returns:
        The appropriate tool message widget for the given tool
    """
    # Try to parse arguments for specific tool types
    args_dict: dict[str, Any] = {}
    with contextlib.suppress(json.JSONDecodeError, KeyError):
        args_dict = json.loads(arguments)

    # Check if this is an MCP tool based on the naming pattern
    if tool_name.startswith("mcp__"):
        # Extract server name and original tool name from the pattern: mcp__servername__toolname
        parts = tool_name.split("__", 2)  # Split into at most 3 parts
        if len(parts) == 3:
            _, server_name, original_tool_name = parts
            if output is not None:
                return MCPToolMessage(
                    server_name=server_name,
                    tool_name=original_tool_name,
                    arguments=arguments,
                    output=output,
                    status=status,
                )
            else:
                return MCPToolMessage(
                    server_name=server_name,
                    tool_name=original_tool_name,
                    arguments=arguments,
                    status=status,
                )
        else:
            # Malformed MCP tool name, fall back to generic tool message
            if output is not None:
                return ToolMessage(tool_name=tool_name, command=arguments, output=output, status=status)
            else:
                return ToolMessage(tool_name=tool_name, command=arguments, status=status)

    # Create tool-specific messages based on tool name
    elif tool_name == "execute_python":
        code = args_dict.get("code", "") if args_dict else ""
        if output is not None:
            return PythonToolMessage(code=code, output=output, status=status)
        else:
            return PythonToolMessage(code=code, status=status)

    elif tool_name == "bash":
        command = args_dict.get("command", "") if args_dict else ""
        if output is not None:
            return BashToolMessage(command=command, output=output, status=status)
        else:
            return BashToolMessage(command=command, status=status)

    elif tool_name == "todo_write":
        todos = args_dict.get("todos", []) if args_dict else []
        if output is not None:
            return TodoWriteToolMessage(todos=todos, output=output, status=status)
        else:
            return TodoWriteToolMessage(todos=todos, status=status)

    elif tool_name == "read":
        file_path = args_dict.get("file_path", "") if args_dict else ""
        if output is not None:
            return ReadToolMessage(file_path=file_path, output=output, status=status)
        else:
            return ReadToolMessage(file_path=file_path, status=status)

    elif tool_name == "task":
        description = args_dict.get("description", "") if args_dict else ""
        prompt = args_dict.get("prompt", "") if args_dict else ""
        if output is not None:
            return TaskToolMessage(description=description, prompt=prompt, output=output, status=status)
        else:
            return TaskToolMessage(description=description, prompt=prompt, status=status)

    elif tool_name == "write":
        file_path = args_dict.get("file_path", "") if args_dict else ""
        content = args_dict.get("content", "") if args_dict else ""
        if output is not None:
            return WriteToolMessage(file_path=file_path, content=content, output=output, status=status)
        else:
            return WriteToolMessage(file_path=file_path, content=content, status=status)

    elif tool_name == "websearch":
        query = args_dict.get("query", "") if args_dict else ""
        if output is not None:
            return WebSearchToolMessage(query=query, output=output, status=status)
        else:
            return WebSearchToolMessage(query=query, status=status)

    elif tool_name == "webfetch":
        url = args_dict.get("url", "") if args_dict else ""
        if output is not None:
            return WebFetchToolMessage(url=url, output=output, status=status)
        else:
            return WebFetchToolMessage(url=url, status=status)

    elif tool_name in settings.rich_tool_names:
        if output is not None:
            return RichToolMessage(tool_name=tool_name, arguments=arguments, output=output, status=status)
        else:
            return RichToolMessage(tool_name=tool_name, arguments=arguments, status=status)

    # Default to generic ToolMessage for all other tools
    else:
        if output is not None:
            return ToolMessage(tool_name=tool_name, command=arguments, output=output, status=status)
        else:
            return ToolMessage(tool_name=tool_name, command=arguments, status=status)
