"""Web search tools for Vibecore agents."""

import json

from agents import RunContextWrapper, function_tool

from vibecore.context import VibecoreContext

from .executor import web_search_executor


@function_tool
async def web_search(
    ctx: RunContextWrapper[VibecoreContext],
    query: str,
    num_results: int = 10,
) -> str:
    """Search the web for information using DuckDuckGo search engine.

    This tool performs web searches to find current information, research topics,
    look up documentation, find code examples, and answer questions that require
    up-to-date information from the internet.

    Args:
        ctx: The run context wrapper
        query: The search query string (required)
        num_results: Maximum number of results to return (1-50, default: 10)

    Returns:
        JSON string containing search results with title, URL, and snippet for each result.
        On error, returns an error message string.

    Usage examples:
        - "latest Python 3.12 features"
        - "how to use async await in JavaScript"
        - "best practices for REST API design 2024"
        - "Textual TUI library documentation"

    Note: This tool uses DuckDuckGo search which respects privacy and doesn't track users.
    """
    if not query or not query.strip():
        return "Error: Search query cannot be empty"

    # Validate num_results
    if not isinstance(num_results, int) or num_results < 1 or num_results > 50:
        num_results = 10

    try:
        results, error = await web_search_executor(query.strip(), num_results)

        if error:
            return error

        if not results:
            return "No search results found for the query"

        # Format results as JSON for structured output
        formatted_results = {"query": query.strip(), "num_results": len(results), "results": results}

        return json.dumps(formatted_results, indent=2, ensure_ascii=False)

    except Exception as e:
        return f"Error: Failed to perform web search - {e!s}"
