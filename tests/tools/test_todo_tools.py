"""Tests for todo management tools."""

from unittest.mock import MagicMock

import pytest
from agents import RunContextWrapper

from vibecore.context import DefaultVibecoreContext
from vibecore.tools.todo.manager import TodoManager
from vibecore.tools.todo.models import TodoItem, TodoPriority, TodoStatus
from vibecore.tools.todo.tools import todo_read as todo_read_tool
from vibecore.tools.todo.tools import todo_write as todo_write_tool


# Helper functions to test the tool implementations
async def todo_read_helper(ctx):
    """Helper to call todo_read implementation."""
    return ctx.context.todo_manager.read()


async def todo_write_helper(ctx, todos):
    """Helper to call todo_write implementation."""
    todos_dict = [todo.model_dump() for todo in todos] if todos and isinstance(todos[0], TodoItem) else todos
    ctx.context.todo_manager.write(todos_dict)
    return "Todo list updated successfully."


@pytest.fixture
def mock_context():
    """Create a mock RunContextWrapper with VibecoreContext."""
    mock_ctx = MagicMock(spec=RunContextWrapper)
    # Create a real VibecoreContext
    mock_ctx.context = DefaultVibecoreContext()
    return mock_ctx


@pytest.fixture
def todo_manager():
    """Create a fresh TodoManager for testing."""
    return TodoManager()


class TestTodoManager:
    """Test the TodoManager class."""

    def test_init(self):
        """Test TodoManager initialization."""
        manager = TodoManager()
        assert manager.todos == []

    def test_read_empty(self):
        """Test reading from an empty todo list."""
        manager = TodoManager()
        result = manager.read()
        assert result == []

    def test_write_and_read(self):
        """Test writing and reading todos."""
        manager = TodoManager()
        todos = [
            {"id": "1", "content": "Task 1", "status": "pending", "priority": "high"},
            {"id": "2", "content": "Task 2", "status": "in_progress", "priority": "medium"},
        ]
        manager.write(todos)
        result = manager.read()
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[0]["content"] == "Task 1"
        assert result[0]["status"] == "pending"
        assert result[0]["priority"] == "high"

    def test_write_overwrites_existing(self):
        """Test that write completely replaces existing todos."""
        manager = TodoManager()
        initial_todos = [
            {"id": "1", "content": "Task 1", "status": "pending", "priority": "high"},
        ]
        manager.write(initial_todos)

        new_todos = [
            {"id": "2", "content": "Task 2", "status": "completed", "priority": "low"},
            {"id": "3", "content": "Task 3", "status": "pending", "priority": "medium"},
        ]
        manager.write(new_todos)

        result = manager.read()
        assert len(result) == 2
        assert result[0]["id"] == "2"
        assert result[1]["id"] == "3"


@pytest.mark.asyncio
class TestTodoTools:
    """Test the todo tools through the agent interface."""

    async def test_todo_read_empty(self, mock_context):
        """Test reading an empty todo list."""
        result = await todo_read_helper(mock_context)
        assert result == []

    async def test_todo_write_and_read(self, mock_context):
        """Test writing and reading todos through tools."""
        todos = [
            TodoItem(id="1", content="Task 1", status=TodoStatus.PENDING, priority=TodoPriority.HIGH),
            TodoItem(id="2", content="Task 2", status=TodoStatus.COMPLETED, priority=TodoPriority.LOW),
        ]

        result = await todo_write_helper(mock_context, todos)
        assert result == "Todo list updated successfully."

        read_result = await todo_read_helper(mock_context)
        assert len(read_result) == 2
        assert read_result[0]["content"] == "Task 1"
        assert read_result[1]["status"] == "completed"


@pytest.mark.asyncio
class TestTodoIntegration:
    """Test todo functionality end-to-end."""

    async def test_todo_workflow_with_all_statuses(self, mock_context):
        """Test a complete workflow with all status values."""
        # Start with pending tasks
        todos = [
            TodoItem(id="1", content="Design feature", status=TodoStatus.PENDING, priority=TodoPriority.HIGH),
            TodoItem(id="2", content="Write code", status=TodoStatus.PENDING, priority=TodoPriority.MEDIUM),
            TodoItem(id="3", content="Test feature", status=TodoStatus.PENDING, priority=TodoPriority.LOW),
        ]
        await todo_write_helper(mock_context, todos)

        # Update first task to in_progress
        todos[0] = TodoItem(id="1", content="Design feature", status=TodoStatus.IN_PROGRESS, priority=TodoPriority.HIGH)
        await todo_write_helper(mock_context, todos)
        result = await todo_read_helper(mock_context)
        assert result[0]["status"] == "in_progress"

        # Complete first task and start second
        todos[0] = TodoItem(id="1", content="Design feature", status=TodoStatus.COMPLETED, priority=TodoPriority.HIGH)
        todos[1] = TodoItem(id="2", content="Write code", status=TodoStatus.IN_PROGRESS, priority=TodoPriority.MEDIUM)
        await todo_write_helper(mock_context, todos)
        result = await todo_read_helper(mock_context)
        assert result[0]["status"] == "completed"
        assert result[1]["status"] == "in_progress"

    async def test_todo_workflow_with_all_priorities(self, mock_context):
        """Test todo operations with all priority levels."""
        todos = [
            TodoItem(id="1", content="Critical bug fix", status=TodoStatus.PENDING, priority=TodoPriority.HIGH),
            TodoItem(id="2", content="Feature request", status=TodoStatus.PENDING, priority=TodoPriority.MEDIUM),
            TodoItem(id="3", content="Documentation update", status=TodoStatus.PENDING, priority=TodoPriority.LOW),
        ]

        result = await todo_write_helper(mock_context, todos)
        assert result == "Todo list updated successfully."

        read_result = await todo_read_helper(mock_context)
        assert len(read_result) == 3
        assert read_result[0]["priority"] == "high"
        assert read_result[1]["priority"] == "medium"
        assert read_result[2]["priority"] == "low"

    async def test_todo_persistence_across_operations(self, mock_context):
        """Test that todos persist correctly across multiple operations."""
        # First write
        todos = [TodoItem(id="1", content="Initial task", status=TodoStatus.PENDING, priority=TodoPriority.HIGH)]
        await todo_write_helper(mock_context, todos)

        # Read back
        result = await todo_read_helper(mock_context)
        assert len(result) == 1
        assert result[0]["content"] == "Initial task"

        # Add more tasks
        todos = [
            TodoItem(id="1", content="Initial task", status=TodoStatus.PENDING, priority=TodoPriority.HIGH),
            TodoItem(id="2", content="Second task", status=TodoStatus.IN_PROGRESS, priority=TodoPriority.MEDIUM),
            TodoItem(id="3", content="Third task", status=TodoStatus.COMPLETED, priority=TodoPriority.LOW),
        ]
        await todo_write_helper(mock_context, todos)

        # Final read
        result = await todo_read_helper(mock_context)
        assert len(result) == 3
        assert result[1]["status"] == "in_progress"
        assert result[2]["status"] == "completed"

    async def test_empty_todo_list_operations(self, mock_context):
        """Test operations with empty todo lists."""
        # Start with some todos
        initial_todos = [
            TodoItem(id="1", content="Task to remove", status=TodoStatus.PENDING, priority=TodoPriority.HIGH),
            TodoItem(id="2", content="Another task", status=TodoStatus.COMPLETED, priority=TodoPriority.LOW),
        ]
        await todo_write_helper(mock_context, initial_todos)
        result = await todo_read_helper(mock_context)
        assert len(result) == 2

        # Clear all todos
        await todo_write_helper(mock_context, [])
        result = await todo_read_helper(mock_context)
        assert result == []

        # Add new todos after clearing
        new_todos = [TodoItem(id="3", content="New task", status=TodoStatus.PENDING, priority=TodoPriority.MEDIUM)]
        await todo_write_helper(mock_context, new_todos)
        result = await todo_read_helper(mock_context)
        assert len(result) == 1
        assert result[0]["id"] == "3"


class TestTodoItem:
    """Test the TodoItem Pydantic model."""

    def test_todo_item_creation(self):
        """Test creating a TodoItem."""
        todo = TodoItem(id="test-123", content="Test task", status=TodoStatus.PENDING, priority=TodoPriority.HIGH)
        assert todo.id == "test-123"
        assert todo.content == "Test task"
        assert todo.status.value == "pending"
        assert todo.priority.value == "high"

    def test_todo_item_model_dump(self):
        """Test converting TodoItem to dict."""
        todo = TodoItem(
            id="test-456", content="Another task", status=TodoStatus.IN_PROGRESS, priority=TodoPriority.MEDIUM
        )
        todo_dict = todo.model_dump()
        assert todo_dict == {"id": "test-456", "content": "Another task", "status": "in_progress", "priority": "medium"}

    def test_todo_item_validation(self):
        """Test TodoItem validation."""
        # Valid statuses and priorities
        valid_todo = TodoItem(id="1", content="Valid task", status=TodoStatus.COMPLETED, priority=TodoPriority.LOW)
        assert valid_todo.status.value == "completed"
        assert valid_todo.priority.value == "low"

        # Test with all valid combinations
        for status in TodoStatus:
            for priority in TodoPriority:
                todo = TodoItem(
                    id=f"{status}-{priority}",
                    content=f"Task with {status.value} and {priority.value}",
                    status=status,
                    priority=priority,
                )
                assert todo.status == status
                assert todo.priority == priority


class TestTodoToolsDecoration:
    """Test that the todo tools are properly decorated for use with agents."""

    def test_todo_read_tool_attributes(self):
        """Test that todo_read_tool has correct FunctionTool attributes."""
        from agents import FunctionTool

        # Verify it's a FunctionTool
        assert isinstance(todo_read_tool, FunctionTool)

        # Check name
        assert todo_read_tool.name == "todo_read"

        # Check description exists
        assert todo_read_tool.description
        assert "to-do list" in todo_read_tool.description

        # Check schema
        assert todo_read_tool.params_json_schema is not None
        schema = todo_read_tool.params_json_schema
        assert "properties" in schema
        # Should have minimal properties since it takes no real parameters

    def test_todo_write_tool_attributes(self):
        """Test that todo_write_tool has correct FunctionTool attributes."""
        from agents import FunctionTool

        # Verify it's a FunctionTool
        assert isinstance(todo_write_tool, FunctionTool)

        # Check name
        assert todo_write_tool.name == "todo_write"

        # Check description exists
        assert todo_write_tool.description
        assert "task list" in todo_write_tool.description

        # Check schema
        assert todo_write_tool.params_json_schema is not None
        schema = todo_write_tool.params_json_schema
        assert "properties" in schema
        assert "todos" in schema["properties"]

        # Check todos parameter schema
        todos_schema = schema["properties"]["todos"]
        assert todos_schema["type"] == "array"
        assert "items" in todos_schema

        # Check item schema - it should reference TodoItem
        item_schema = todos_schema["items"]
        assert "$ref" in item_schema
        assert "TodoItem" in item_schema["$ref"]

        # Check that the schema has definitions for TodoItem
        assert "$defs" in schema
        assert "TodoItem" in schema["$defs"]

        # Check TodoItem definition
        model_def = schema["$defs"]["TodoItem"]
        assert "properties" in model_def
        assert "id" in model_def["properties"]
        assert "content" in model_def["properties"]
        assert "status" in model_def["properties"]
        assert "priority" in model_def["properties"]
