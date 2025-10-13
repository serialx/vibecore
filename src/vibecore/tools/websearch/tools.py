"""Websearch tool for Vibecore agents."""

from agents import function_tool

from .executor import perform_websearch
from .models import SearchParams


@function_tool
async def websearch(
    query: str,
    max_results: int = 5,
    region: str | None = None,
    safesearch: str = "moderate",
) -> str:
    """Search the web for information using DuckDuckGo.

    This tool allows you to search the web for current information, news, and general knowledge.
    It supports advanced search operators like quotes for exact phrases, minus for exclusions,
    site: for specific domains, and filetype: for specific file types.

    Args:
        ctx: The run context wrapper
        query: The search query (supports advanced operators like "exact phrase", -exclude, site:example.com)
        max_results: Maximum number of results to return (default: 5)
        region: Optional region code for localized results (e.g., 'us-en' for US English)
        safesearch: SafeSearch filter level ('on', 'moderate', or 'off', default: 'moderate')

    Returns:
        JSON string containing search results with title, URL, and snippet for each result

    Examples:
        - Basic search: query="python programming"
        - Exact phrase: query='"machine learning algorithms"'
        - Exclude terms: query="python -javascript"
        - Site-specific: query="AI site:github.com"
        - File type: query="climate change filetype:pdf"
    """
    params = SearchParams(
        query=query,
        max_results=max_results,
        region=region,
        safesearch=safesearch,
    )

    return await perform_websearch(params)
