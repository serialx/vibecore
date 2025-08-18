"""Base classes for websearch backends."""

from abc import ABC, abstractmethod

from .models import SearchParams


class WebSearchBackend(ABC):
    """Abstract base class for web search backends."""

    @abstractmethod
    async def search(self, params: SearchParams) -> str:
        """Perform a web search.

        Args:
            params: Search parameters

        Returns:
            JSON string containing search results or error message
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this backend."""
        pass
