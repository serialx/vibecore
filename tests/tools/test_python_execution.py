"""Tests for Python code execution tool."""

import pytest

from vibecore.tools.python.manager import PythonExecutionManager


@pytest.mark.asyncio
async def test_basic_execution():
    """Test basic Python code execution."""
    manager = PythonExecutionManager()
    result = await manager.execute("print('Hello, World!')")

    assert result.success is True
    assert result.output == "Hello, World!\n"
    assert result.error == ""


@pytest.mark.asyncio
async def test_persistent_context():
    """Test that context persists between executions."""
    manager = PythonExecutionManager()

    # Define a variable
    result1 = await manager.execute("x = 42")
    assert result1.success is True

    # Use the variable in next execution
    result2 = await manager.execute("print(x)")
    assert result2.success is True
    assert result2.output == "42\n"

    # Modify the variable
    result3 = await manager.execute("x = x * 2")
    assert result3.success is True

    # Check the modified value
    result4 = await manager.execute("print(x)")
    assert result4.success is True
    assert result4.output == "84\n"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in code execution."""
    manager = PythonExecutionManager()

    # Syntax error
    result = await manager.execute("print('missing parenthesis'")
    assert result.success is False
    assert "SyntaxError" in result.error
    assert result.output == ""

    # Runtime error
    result = await manager.execute("1 / 0")
    assert result.success is False
    assert "ZeroDivisionError" in result.error


@pytest.mark.asyncio
async def test_output_capture():
    """Test stdout and stderr capture."""
    manager = PythonExecutionManager()

    # Multiple print statements
    code = """
print("Line 1")
print("Line 2")
print("Line 3")
"""
    result = await manager.execute(code)
    assert result.success is True
    assert result.output == "Line 1\nLine 2\nLine 3\n"

    # Test stderr capture with warnings
    code = """
import warnings
warnings.warn("This is a warning")
print("Regular output")
"""
    result = await manager.execute(code)
    assert result.success is True
    assert "Regular output" in result.output
    assert "This is a warning" in result.error


@pytest.mark.asyncio
async def test_complex_operations():
    """Test complex Python operations."""
    manager = PythonExecutionManager()

    # Define a function
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""
    result = await manager.execute(code)
    assert result.success is True
    assert result.output == "120\n"

    # Use the function again
    result = await manager.execute("print(factorial(6))")
    assert result.success is True
    assert result.output == "720\n"

    # Define a class
    code = """
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1
        return self.count

counter = Counter()
print(counter.increment())
print(counter.increment())
"""
    result = await manager.execute(code)
    assert result.success is True
    assert result.output == "1\n2\n"


@pytest.mark.asyncio
async def test_imports():
    """Test import statements."""
    manager = PythonExecutionManager()

    # Standard library imports
    code = """
import math
print(math.pi)
print(math.sqrt(16))
"""
    result = await manager.execute(code)
    assert result.success is True
    assert "3.14159" in result.output
    assert "4.0" in result.output

    # Import persists
    result = await manager.execute("print(math.e)")
    assert result.success is True
    assert "2.71828" in result.output


@pytest.mark.asyncio
async def test_return_values():
    """Test that expressions return values."""
    manager = PythonExecutionManager()

    # Expression without print
    result = await manager.execute("2 + 2")
    assert result.success is True
    assert result.value == 4

    # Last expression value
    code = """
x = 10
y = 20
x + y
"""
    result = await manager.execute(code)
    assert result.success is True
    assert result.value == 30


@pytest.mark.asyncio
async def test_context_isolation():
    """Test that separate managers have isolated contexts."""
    manager1 = PythonExecutionManager()
    manager2 = PythonExecutionManager()

    # Set variable in manager1
    result1 = await manager1.execute("isolated_var = 'manager1'")
    assert result1.success is True

    # Try to access in manager2 (should fail)
    result2 = await manager2.execute("print(isolated_var)")
    assert result2.success is False
    assert "NameError" in result2.error

    # Set different value in manager2
    result3 = await manager2.execute("isolated_var = 'manager2'")
    assert result3.success is True

    # Verify values are different
    result4 = await manager1.execute("print(isolated_var)")
    assert result4.success is True
    assert result4.output == "manager1\n"

    result5 = await manager2.execute("print(isolated_var)")
    assert result5.success is True
    assert result5.output == "manager2\n"


@pytest.mark.asyncio
async def test_multiline_strings():
    """Test handling of multiline strings."""
    manager = PythonExecutionManager()

    code = '''
text = """This is a
multiline
string"""
print(text)
'''
    result = await manager.execute(code)
    assert result.success is True
    assert result.output == "This is a\nmultiline\nstring\n"


@pytest.mark.asyncio
async def test_async_code_execution():
    """Test that async code can be executed."""
    manager = PythonExecutionManager()

    code = """
import asyncio

async def async_function():
    await asyncio.sleep(0.01)
    return "Async result"

# Run async function
result = await async_function()
print(result)
"""
    result = await manager.execute(code)
    assert result.success is True
    assert result.output == "Async result\n"
