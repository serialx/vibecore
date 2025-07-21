"""Base utilities for tools."""

from typing import Any, Protocol

from rich.console import Console


class ToolRenderer(Protocol):
    """Protocol for tool-specific renderers."""

    def render_call(self, tool_name: str, args: dict[str, Any]) -> None:
        """Render a tool call."""
        ...

    def render_output(self, tool_name: str, output: Any) -> None:
        """Render tool output."""
        ...


def create_console() -> Console:
    """Create a configured console instance."""
    return Console()


def render_error(console: Console, error: str) -> None:
    """Render an error message."""
    console.print(f"[red]Error:[/red] {error}")
