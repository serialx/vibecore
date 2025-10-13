"""Python code execution tool."""

from agents import RunContextWrapper, function_tool

from vibecore.context import PythonToolContext

from .helpers import execute_python_helper


@function_tool
async def execute_python(ctx: RunContextWrapper[PythonToolContext], code: str) -> str:
    """Execute Python code with persistent context across the session.

    The execution environment maintains state between calls, allowing you to:
    - Define variables and functions that persist
    - Import modules that remain available
    - Build up complex computations step by step
    - Make sure to define code as function so that we can use it later

    Args:
        ctx: The run context wrapper containing the Python execution manager.
        code: Python code to execute.

    Returns:
        A string containing the execution result, output, or error message.
    """
    return await execute_python_helper(ctx, code)
