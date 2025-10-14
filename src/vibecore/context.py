from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

from vibecore.tools.python.manager import PythonExecutionManager
from vibecore.tools.todo.manager import TodoManager

if TYPE_CHECKING:
    from vibecore.main import VibecoreApp
    from vibecore.tools.path_validator import PathValidator


@runtime_checkable
class TodoToolContext(Protocol):
    """Context required by todo tools."""

    todo_manager: TodoManager


@runtime_checkable
class PythonToolContext(Protocol):
    """Context required by Python execution tools."""

    python_manager: PythonExecutionManager


@runtime_checkable
class PathValidatorContext(Protocol):
    """Context that provides a path validator for file-system tools."""

    path_validator: "PathValidator"


@runtime_checkable
class AppAwareContext(Protocol):
    """Context that exposes the optional Textual app for streaming updates."""

    app: Optional["VibecoreApp"]


@runtime_checkable
class FullVibecoreContext(TodoToolContext, PythonToolContext, PathValidatorContext, AppAwareContext, Protocol):
    """Protocol describing the full context required by Vibecore agents."""

    ...


@dataclass
class DefaultVibecoreContext:
    todo_manager: TodoManager = field(default_factory=TodoManager)
    python_manager: PythonExecutionManager = field(default_factory=PythonExecutionManager)
    app: Optional["VibecoreApp"] = None

    # Path confinement configuration
    allowed_directories: list[Path] = field(default_factory=list)
    path_validator: "PathValidator" = field(init=False)  # Always initialized, never None

    def __post_init__(self) -> None:
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


if TYPE_CHECKING:
    # Ensure DefaultVibecoreContext conforms to the VibecoreContext protocol for static analyzers
    _default_context: FullVibecoreContext = DefaultVibecoreContext()
