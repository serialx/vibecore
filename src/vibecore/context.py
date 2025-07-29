from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from vibecore.tools.python.manager import PythonExecutionManager
from vibecore.tools.todo.manager import TodoManager

if TYPE_CHECKING:
    from vibecore.main import VibecoreApp


@dataclass
class VibecoreContext:
    todo_manager: TodoManager = field(default_factory=TodoManager)
    python_manager: PythonExecutionManager = field(default_factory=PythonExecutionManager)
    app: Optional["VibecoreApp"] = None
