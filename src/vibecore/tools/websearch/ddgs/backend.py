"""DuckDuckGo search backend implementation."""

import json

from ddgs import DDGS

from ..base import WebSearchBackend
from ..models import SearchParams, SearchResult


class DDGSBackend(WebSearchBackend):
    """DuckDuckGo search backend using ddgs library."""

    @property
    def name(self) -> str:
        """Return the name of this backend."""
        return "DuckDuckGo"

    async def search(self, params: SearchParams) -> str:
        """Perform a web search using ddgs.

        Args:
            params: Search parameters

        Returns:
            JSON string containing search results or error message
        """
        try:
            # Create DDGS instance
            ddgs = DDGS()

            # Perform search (synchronous call)
            # ddgs.text() expects 'query' as first positional argument
            raw_results = ddgs.text(  # type: ignore
                query=params.query,
                region=params.region,
                safesearch=params.safesearch,
                max_results=params.max_results,
            )

            # Convert to our model format
            results = []
            for r in raw_results:
                result = SearchResult(
                    title=r.get("title", ""),
                    href=r.get("href", ""),
                    body=r.get("body", ""),
                )
                results.append(result.model_dump())

            if not results:
                return json.dumps({"success": False, "message": "No search results found", "results": []})

            return json.dumps(
                {
                    "success": True,
                    "message": f"Found {len(results)} result{'s' if len(results) != 1 else ''}",
                    "query": params.query,
                    "results": results,
                }
            )

        except Exception as e:
            return json.dumps({"success": False, "message": f"Search failed: {e!s}", "results": []})
