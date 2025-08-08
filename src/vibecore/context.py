from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from vibecore.tools.python.manager import PythonExecutionManager
from vibecore.tools.todo.manager import TodoManager

if TYPE_CHECKING:
    from vibecore.main import VibecoreApp
    from vibecore.mcp import MCPManager


@dataclass
class VibecoreContext:
    todo_manager: TodoManager = field(default_factory=TodoManager)
    python_manager: PythonExecutionManager = field(default_factory=PythonExecutionManager)
    app: Optional["VibecoreApp"] = None
    context_fullness: float = 0.0
    mcp_manager: Optional["MCPManager"] = None

    def reset_state(self) -> None:
        """Reset all context state for a new session."""
        self.todo_manager = TodoManager()
        self.python_manager = PythonExecutionManager()
        self.context_fullness = 0.0
