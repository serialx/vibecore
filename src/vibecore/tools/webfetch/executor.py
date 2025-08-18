"""Webfetch execution logic for fetching and converting web content."""

import json
from urllib.parse import urlparse

import html2text
import httpx

from .models import WebFetchParams


async def fetch_url(params: WebFetchParams) -> str:
    """Fetch a URL and convert its content to Markdown.

    Args:
        params: WebFetch parameters including URL and options

    Returns:
        Markdown-formatted content or error message
    """
    try:
        # Validate URL
        parsed = urlparse(params.url)
        if not parsed.scheme:
            return f"Error: Invalid URL - missing scheme (http:// or https://): {params.url}"
        if not parsed.netloc:
            return f"Error: Invalid URL - missing domain: {params.url}"
        if parsed.scheme not in ["http", "https"]:
            return f"Error: Unsupported URL scheme: {parsed.scheme}"

        # Configure headers
        headers = {
            "User-Agent": params.user_agent
            or "Mozilla/5.0 (compatible; Vibecore/1.0; +https://github.com/serialx/vibecore)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "text/plain;q=0.8,application/json;q=0.7,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        }

        # Fetch the URL
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(params.timeout),
            follow_redirects=params.follow_redirects,
        ) as client:
            response = await client.get(params.url, headers=headers)
            response.raise_for_status()

            # Get content type
            content_type = response.headers.get("content-type", "").lower()

            # Handle different content types
            if "application/json" in content_type:
                # Pretty-print JSON as Markdown code block
                try:
                    json_data = response.json()
                    content = f"```json\n{json.dumps(json_data, indent=2)}\n```"
                except json.JSONDecodeError:
                    content = response.text[: params.max_length]

            elif "text/html" in content_type or "application/xhtml" in content_type:
                # Convert HTML to Markdown
                html_content = response.text[: params.max_length]

                # Configure html2text
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = False
                h.ignore_emphasis = False
                h.body_width = 0  # Don't wrap lines
                h.skip_internal_links = False
                h.inline_links = True
                h.wrap_links = False
                h.wrap_list_items = False
                h.ul_item_mark = "-"
                h.emphasis_mark = "*"
                h.strong_mark = "**"

                content = h.handle(html_content)

                # Clean up excessive newlines
                while "\n\n\n" in content:
                    content = content.replace("\n\n\n", "\n\n")
                content = content.strip()

            elif "text/plain" in content_type or "text/" in content_type:
                # Plain text - return as is
                content = response.text[: params.max_length]

            else:
                # Unknown content type - try to handle as text
                content = response.text[: params.max_length]
                if not content:
                    return f"Error: Unable to extract text content from {content_type}"

            # Add metadata
            metadata = [
                f"# Content from {params.url}",
                f"**Status Code:** {response.status_code}",
                f"**Content Type:** {content_type.split(';')[0] if content_type else 'unknown'}",
            ]

            # Add redirect info if applicable
            if response.history:
                metadata.append(f"**Redirected:** {len(response.history)} time(s)")
                metadata.append(f"**Final URL:** {response.url}")

            metadata.append("")  # Empty line before content

            # Check if content was truncated
            if len(response.text) > params.max_length:
                metadata.append(f"*Note: Content truncated to {params.max_length} characters*")
                metadata.append("")

            # Combine metadata and content
            full_content = "\n".join(metadata) + "\n" + content

            return full_content

    except httpx.TimeoutException:
        return f"Error: Request timed out after {params.timeout} seconds"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.reason_phrase}"
    except httpx.RequestError as e:
        return f"Error: Failed to connect to {params.url}: {e!s}"
    except Exception as e:
        return f"Error: Unexpected error while fetching {params.url}: {e!s}"
