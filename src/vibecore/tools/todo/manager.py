"""Todo list manager."""

from typing import Any

from .models import TodoItem, TodoPriority, TodoStatus


class TodoManager:
    """Manages a session-scoped todo list."""

    def __init__(self):
        self.todos: list[TodoItem] = []

    def read(self) -> list[dict[str, Any]]:
        """Read all todos."""
        return [
            {"id": todo.id, "content": todo.content, "status": todo.status.value, "priority": todo.priority.value}
            for todo in self.todos
        ]

    def write(self, todos: list[dict[str, Any]]) -> None:
        """Replace the entire todo list."""
        self.todos = [
            TodoItem(
                id=todo["id"],
                content=todo["content"],
                status=TodoStatus(todo["status"]),
                priority=TodoPriority(todo["priority"]),
            )
            for todo in todos
        ]
