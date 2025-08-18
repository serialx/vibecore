"""Data models for the webfetch tool."""

from pydantic import BaseModel, Field


class WebFetchParams(BaseModel):
    """Parameters for fetching web content."""

    url: str = Field(description="The URL to fetch content from")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    user_agent: str | None = Field(
        default=None,
        description="Optional custom User-Agent header",
    )
    follow_redirects: bool = Field(
        default=True,
        description="Whether to follow HTTP redirects",
    )
    max_length: int = Field(
        default=1000000,  # ~1MB of text
        description="Maximum content length to fetch in characters",
    )
