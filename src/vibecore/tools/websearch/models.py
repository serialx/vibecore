"""Models for websearch tool."""

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result."""

    title: str = Field(description="Title of the search result")
    href: str = Field(description="URL of the search result")
    body: str = Field(description="Description/snippet of the result")


class SearchParams(BaseModel):
    """Parameters for web search."""

    query: str = Field(description="Search query")
    max_results: int = Field(default=5, description="Maximum number of results to return")
    region: str | None = Field(default=None, description="Region code (e.g., 'us-en')")
    safesearch: str = Field(default="moderate", description="SafeSearch setting: 'on', 'moderate', or 'off'")
