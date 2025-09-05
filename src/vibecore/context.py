from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from vibecore.tools.python.manager import PythonExecutionManager
from vibecore.tools.todo.manager import TodoManager

if TYPE_CHECKING:
    from vibecore.main import VibecoreApp
    from vibecore.mcp import MCPManager
    from vibecore.tools.path_validator import PathValidator


@dataclass
class VibecoreContext:
    todo_manager: TodoManager = field(default_factory=TodoManager)
    python_manager: PythonExecutionManager = field(default_factory=PythonExecutionManager)
    app: Optional["VibecoreApp"] = None
    context_fullness: float = 0.0
    mcp_manager: Optional["MCPManager"] = None

    # Path confinement configuration
    allowed_directories: list[Path] = field(default_factory=list)
    path_validator: "PathValidator" = field(init=False)  # Always initialized, never None

    def __post_init__(self):
        """Initialize path validator with allowed directories."""
        from vibecore.tools.path_validator import PathValidator

        if not self.allowed_directories:
            # Load from settings if not explicitly provided
            from vibecore.settings import settings

            if settings.path_confinement.enabled:
                self.allowed_directories = settings.path_confinement.allowed_directories
                # Add home directory if configured
                if settings.path_confinement.allow_home:
                    self.allowed_directories.append(Path.home())
                # Add temp directories if configured
                if settings.path_confinement.allow_temp:
                    import tempfile

                    temp_dir = Path(tempfile.gettempdir())
                    if temp_dir not in self.allowed_directories:
                        self.allowed_directories.append(temp_dir)
            else:
                # If path confinement is disabled, allow CWD only (but validator won't be used)
                self.allowed_directories = [Path.cwd()]

        self.path_validator = PathValidator(self.allowed_directories)

    def reset_state(self) -> None:
        """Reset all context state for a new session."""
        self.todo_manager = TodoManager()
        self.python_manager = PythonExecutionManager()
        self.context_fullness = 0.0
        # Preserve allowed_directories across resets
        # Re-initialize validator in case directories changed
        from vibecore.tools.path_validator import PathValidator

        self.path_validator = PathValidator(self.allowed_directories)
