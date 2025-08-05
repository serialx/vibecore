"""Integration tests for Python execution tool with agents."""

import pytest
from agents import RunContextWrapper

from vibecore.context import VibecoreContext
from vibecore.tools.python.helpers import execute_python_helper


@pytest.mark.asyncio
async def test_execute_python_helper_tool_basic():
    """Test the execute_python_helper tool with basic code."""
    # Create a mock context
    context = VibecoreContext()
    run_context = RunContextWrapper(context=context)

    # Execute simple code
    result = await execute_python_helper(run_context, "print('Hello from tool!')")

    assert "Hello from tool!" in result
    assert "Output:" in result


@pytest.mark.asyncio
async def test_execute_python_helper_tool_persistent_state():
    """Test that state persists across tool calls."""
    context = VibecoreContext()
    run_context = RunContextWrapper(context=context)

    # Define a variable
    result1 = await execute_python_helper(run_context, "test_var = 123")
    assert "successfully" in result1

    # Use the variable
    result2 = await execute_python_helper(run_context, "print(f'Value is: {test_var}')")
    assert "Value is: 123" in result2


@pytest.mark.asyncio
async def test_execute_python_helper_tool_error_handling():
    """Test error handling in the tool."""
    context = VibecoreContext()  # type: ignore
    run_context = RunContextWrapper(context=context)

    # Syntax error
    result = await execute_python_helper(run_context, "print('unclosed")
    assert "Error:" in result
    assert "SyntaxError" in result

    # Runtime error
    result = await execute_python_helper(run_context, "undefined_variable")
    assert "Error:" in result
    assert "NameError" in result


@pytest.mark.asyncio
async def test_execute_python_helper_tool_return_values():
    """Test that return values are shown."""
    context = VibecoreContext()  # type: ignore
    run_context = RunContextWrapper(context=context)

    # Expression that returns a value
    result = await execute_python_helper(run_context, "2 + 2")
    assert "Result: `4`" in result

    # Expression with print (should not show result)
    result = await execute_python_helper(run_context, "print(3 + 3)")
    assert "6" in result
    assert "Result:" not in result  # Should not show result when there's output


@pytest.mark.asyncio
async def test_execute_python_helper_tool_complex_code():
    """Test complex code execution."""
    context = VibecoreContext()  # type: ignore
    run_context = RunContextWrapper(context=context)

    # Define and use a function
    code = """
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
"""
    result = await execute_python_helper(run_context, code)
    assert "Hello, World!" in result

    # Use the function again
    result = await execute_python_helper(run_context, "print(greet('Python'))")
    assert "Hello, Python!" in result


@pytest.mark.asyncio
async def test_execute_python_helper_tool_imports():
    """Test that imports work correctly."""
    context = VibecoreContext()  # type: ignore
    run_context = RunContextWrapper(context=context)

    # Import a module
    result = await execute_python_helper(run_context, "import json")
    assert "successfully" in result

    # Use the imported module
    result = await execute_python_helper(run_context, 'print(json.dumps({"key": "value"}))')
    assert '{"key": "value"}' in result


@pytest.mark.asyncio
async def test_execute_python_helper_tool_multiline_output():
    """Test multiline output formatting."""
    context = VibecoreContext()  # type: ignore
    run_context = RunContextWrapper(context=context)

    code = """
for i in range(3):
    print(f"Line {i + 1}")
"""
    result = await execute_python_helper(run_context, code)
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result
    assert "```" in result  # Should use code blocks
