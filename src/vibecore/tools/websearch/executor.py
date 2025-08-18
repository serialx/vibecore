"""Websearch execution logic with backend selection."""

from .base import WebSearchBackend
from .ddgs import DDGSBackend
from .models import SearchParams

# Default backend
_default_backend: WebSearchBackend = DDGSBackend()


def set_default_backend(backend: WebSearchBackend) -> None:
    """Set the default search backend.

    Args:
        backend: The backend to use for searches
    """
    global _default_backend
    _default_backend = backend


def get_default_backend() -> WebSearchBackend:
    """Get the current default search backend.

    Returns:
        The current default backend
    """
    return _default_backend


async def perform_websearch(params: SearchParams, backend: WebSearchBackend | None = None) -> str:
    """Perform a web search using the specified or default backend.

    Args:
        params: Search parameters
        backend: Optional specific backend to use (defaults to default backend)

    Returns:
        JSON string containing search results or error message
    """
    if backend is None:
        backend = _default_backend

    return await backend.search(params)
