"""Webfetch tool for Vibecore agents."""

from agents import function_tool

from .executor import fetch_url
from .models import WebFetchParams


@function_tool
async def webfetch(
    url: str,
    timeout: int = 30,
    follow_redirects: bool = True,
) -> str:
    """Fetch content from a URL and convert it to Markdown format.

    This tool fetches web content and converts it to clean, readable Markdown.
    It handles HTML pages, JSON APIs, and plain text content appropriately.

    Args:
        ctx: The run context wrapper
        url: The URL to fetch content from (must include http:// or https://)
        timeout: Request timeout in seconds (default: 30)
        follow_redirects: Whether to follow HTTP redirects (default: True)

    Returns:
        Markdown-formatted content from the URL, including metadata about the
        request (status code, content type, etc.) or an error message if the
        fetch fails.

    Examples:
        - Fetch a webpage: url="https://example.com"
        - Fetch JSON API: url="https://api.example.com/data"
        - Fetch with timeout: url="https://slow-site.com", timeout=60
        - Don't follow redirects: url="https://short.link/abc", follow_redirects=False
    """
    params = WebFetchParams(
        url=url,
        timeout=timeout,
        follow_redirects=follow_redirects,
    )

    return await fetch_url(params)
