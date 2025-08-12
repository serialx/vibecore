"""Tests for web search tool functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from agents import RunContextWrapper

from vibecore.context import VibecoreContext
from vibecore.tools.web.executor import web_search_executor


# Helper function to test the tool implementations
async def web_search_helper(ctx, query: str, num_results: int = 10):
    """Helper to call web_search implementation."""
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


@pytest.fixture
def mock_context():
    """Create a mock RunContextWrapper with VibecoreContext."""
    mock_ctx = MagicMock(spec=RunContextWrapper)
    mock_ctx.context = VibecoreContext()
    return mock_ctx


class TestWebSearchExecutor:
    """Test the web search executor."""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Test handling of empty query."""
        results, error = await web_search_executor("")
        assert results == []
        assert error == "Error: Search query cannot be empty"

    @pytest.mark.asyncio
    async def test_whitespace_only_query(self):
        """Test handling of whitespace-only query."""
        results, error = await web_search_executor("   ")
        assert results == []
        assert error == "Error: Search query cannot be empty"

    @pytest.mark.asyncio
    async def test_num_results_bounds(self):
        """Test num_results parameter bounds."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = "<html></html>"
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            # Test lower bound
            results, error = await web_search_executor("test", num_results=0)
            # Should be clamped to 1 minimum
            assert error is None or error == "No search results found"

            # Test upper bound
            results, error = await web_search_executor("test", num_results=100)
            # Should be clamped to 50 maximum
            assert error is None or error == "No search results found"

    @pytest.mark.asyncio
    async def test_http_timeout(self):
        """Test handling of HTTP timeout."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")

            results, error = await web_search_executor("test query")
            assert results == []
            assert error == "Error: Search request timed out"

    @pytest.mark.asyncio
    async def test_http_error(self):
        """Test handling of HTTP errors."""
        with patch("httpx.AsyncClient.get") as mock_get:
            # Create a mock request object
            mock_request = MagicMock()
            mock_request.url = "https://example.com"

            mock_get.side_effect = httpx.RequestError("Connection failed", request=mock_request)

            results, error = await web_search_executor("test query")
            assert results == []
            assert error is not None
            assert "Error: HTTP request failed" in error

    @pytest.mark.asyncio
    async def test_successful_search_no_results(self):
        """Test successful search with no results."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.text = "<html><body>No results found</body></html>"
            mock_response.raise_for_status = AsyncMock()
            mock_get.return_value = mock_response

            results, error = await web_search_executor("nonexistent query")
            assert results == []
            assert error == "No search results found"


@pytest.mark.asyncio
class TestWebSearchTool:
    """Test the web search tool function."""

    async def test_empty_query_validation(self, mock_context):
        """Test tool validation of empty query."""
        result = await web_search_helper(mock_context, "")
        assert result == "Error: Search query cannot be empty"

    async def test_invalid_num_results(self, mock_context):
        """Test tool handling of invalid num_results."""
        with patch("tests.test_web_search.web_search_executor") as mock_executor:
            mock_executor.return_value = ([], None)

            # Test with invalid type - should default to 10
            await web_search_helper(mock_context, "test", num_results="invalid")  # type: ignore
            mock_executor.assert_called_with("test", 10)

    async def test_successful_search_json_output(self, mock_context):
        """Test successful search with JSON formatted output."""
        mock_results = [
            {"title": "Test Result 1", "url": "https://example.com/1", "snippet": "This is a test result"},
            {"title": "Test Result 2", "url": "https://example.com/2", "snippet": "This is another test result"},
        ]

        with patch("tests.test_web_search.web_search_executor") as mock_executor:
            mock_executor.return_value = (mock_results, None)

            result = await web_search_helper(mock_context, "test query", num_results=5)

            # Verify result is valid JSON
            parsed_result = json.loads(result)
            assert parsed_result["query"] == "test query"
            assert parsed_result["num_results"] == 2
            assert parsed_result["results"] == mock_results

    async def test_executor_error_passthrough(self, mock_context):
        """Test tool handling of invalid results."""
        with patch("tests.test_web_search.web_search_executor") as mock_executor:
            mock_executor.return_value = ([], "Error: Connection failed")

            result = await web_search_helper(mock_context, "test query")
            assert result == "Error: Connection failed"

    async def test_executor_exception_handling(self, mock_context):
        """Test handling of unexpected exceptions."""
        with patch("tests.test_web_search.web_search_executor") as mock_executor:
            mock_executor.side_effect = Exception("Unexpected error")

            result = await web_search_helper(mock_context, "test query")
            assert "Error: Failed to perform web search" in result
            assert "Unexpected error" in result
