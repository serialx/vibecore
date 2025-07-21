from dataclasses import dataclass, field

from vibecore.tools.python.manager import PythonExecutionManager
from vibecore.tools.todo.manager import TodoManager


@dataclass
class VibecoreContext:
    todo_manager: TodoManager = field(default_factory=TodoManager)
    python_manager: PythonExecutionManager = field(default_factory=PythonExecutionManager)
