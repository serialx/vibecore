"""Web search executor implementation."""

import re
from urllib.parse import quote_plus

import httpx


async def web_search_executor(query: str, num_results: int = 10) -> tuple[list[dict], str | None]:
    """Execute a web search using DuckDuckGo's Instant Answer API.

    Args:
        query: The search query
        num_results: Maximum number of results to return (1-50)

    Returns:
        Tuple of (results_list, error_message)
        Results list contains dicts with keys: title, url, snippet
    """
    try:
        # Validate inputs
        num_results = max(1, min(50, num_results))

        if not query.strip():
            return [], "Error: Search query cannot be empty"

        # Use DuckDuckGo's instant answer API - it's free and doesn't require API keys
        encoded_query = quote_plus(query.strip())

        # DuckDuckGo HTML search endpoint (more reliable than instant answer API)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {"User-Agent": "Mozilla/5.0 (compatible; VibeCore/1.0; +https://github.com/serialx/vibecore)"}

        timeout = httpx.Timeout(10.0, connect=5.0)

        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.get(search_url)
            response.raise_for_status()

            html_content = response.text

            # Parse DuckDuckGo HTML results
            results = parse_duckduckgo_html(html_content, num_results)

            if not results:
                return [], "No search results found"

            return results, None

    except httpx.TimeoutException:
        return [], "Error: Search request timed out"
    except httpx.HTTPError as e:
        return [], f"Error: HTTP request failed - {e!s}"
    except Exception as e:
        return [], f"Error: Unexpected error during web search - {e!s}"


def parse_duckduckgo_html(html_content: str, max_results: int) -> list[dict]:
    """Parse DuckDuckGo HTML search results.

    Args:
        html_content: Raw HTML from DuckDuckGo search
        max_results: Maximum number of results to extract

    Returns:
        List of result dictionaries with title, url, snippet keys
    """
    results = []

    # DuckDuckGo result pattern - matches individual search results
    result_pattern = re.compile(
        r'<div class="result__body">.*?'
        r'<a rel="nofollow" href="([^"]+)".*?>'
        r'<h2 class="result__title">.*?</h2>.*?</a>.*?'
        r'<a class="result__snippet" href="[^"]+">([^<]+)</a>',
        re.DOTALL | re.IGNORECASE,
    )

    matches = result_pattern.findall(html_content)

    for i, (url, snippet) in enumerate(matches[:max_results]):
        if not url or not snippet:
            continue

        # Clean up URL (DuckDuckGo uses redirect URLs)
        clean_url = clean_duckduckgo_url(url)

        # Extract title from the area near this result
        title = extract_title_for_result(html_content, url, i)

        # Clean up snippet
        clean_snippet = clean_html_text(snippet)

        if clean_url and title and clean_snippet:
            results.append({"title": title, "url": clean_url, "snippet": clean_snippet})

    return results


def clean_duckduckgo_url(url: str) -> str:
    """Clean DuckDuckGo redirect URL to get actual destination."""
    # DuckDuckGo uses /uddg/redirect.php?u=<encoded_url>
    if "/uddg/redirect.php?u=" in url:
        try:
            from urllib.parse import unquote

            # Extract the u parameter value and decode it
            encoded_part = url.split("/uddg/redirect.php?u=")[1]
            # Remove any additional parameters
            encoded_part = encoded_part.split("&")[0]
            return unquote(encoded_part)
        except Exception:
            pass

    # If it's already a clean URL or cleaning failed, return as-is
    return url


def extract_title_for_result(html_content: str, url: str, result_index: int) -> str:
    """Extract the title for a specific search result."""
    # Find all title elements
    title_matches = re.findall(
        r'<h2 class="result__title">.*?<span[^>]*>([^<]+)</span>.*?</h2>', html_content, re.DOTALL | re.IGNORECASE
    )

    if result_index < len(title_matches):
        return clean_html_text(title_matches[result_index])

    # Fallback: try to extract domain from URL as title
    try:
        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        return domain or "Unknown"
    except Exception:
        return "Unknown"


def clean_html_text(text: str) -> str:
    """Clean HTML entities and tags from text."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode common HTML entities
    html_entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&nbsp;": " ",
    }

    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
