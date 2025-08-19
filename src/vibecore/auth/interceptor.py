"""HTTP request interceptor for Claude Code spoofing."""

from typing import Any

import httpx
from httpx import URL

from vibecore.auth.config import ANTHROPIC_CONFIG
from vibecore.auth.storage import SecureAuthStorage
from vibecore.auth.token_manager import TokenRefreshManager


class AnthropicRequestInterceptor:
    """Intercepts and modifies Anthropic API requests."""

    def __init__(self, storage: SecureAuthStorage):
        """
        Initialize request interceptor.

        Args:
            storage: Secure storage for credentials.
        """
        self.storage = storage
        self.token_manager = TokenRefreshManager(storage)

    async def intercept_request(self, url: str, headers: dict[str, str] | None = None, **kwargs: Any) -> dict[str, Any]:
        """
        Intercept and modify request for Anthropic API.

        Args:
            url: Request URL.
            headers: Request headers.
            **kwargs: Additional request parameters.

        Returns:
            Modified request parameters.
        """
        auth = await self.storage.load("anthropic")

        if not auth:
            raise ValueError("Not authenticated with Anthropic")

        # Prepare headers
        headers = {} if headers is None else headers.copy()

        if auth.type == "oauth":  # OAuth auth
            await self._configure_oauth_headers(headers)
        else:  # API key auth
            self._configure_api_key_headers(headers, auth.key)  # type: ignore

        # Apply Claude Code spoofing headers
        self._apply_claude_code_headers(headers)

        # Return modified request parameters
        return {**kwargs, "headers": headers}

    async def _configure_oauth_headers(self, headers: dict[str, str]) -> None:
        """Configure headers for OAuth authentication."""
        # Get valid access token (handles refresh automatically)
        access_token = await self.token_manager.get_valid_token()

        # Remove any API key headers (OAuth takes precedence)
        headers.pop("x-api-key", None)
        headers.pop("X-Api-Key", None)
        headers.pop("anthropic-api-key", None)

        # Set OAuth bearer token
        headers["Authorization"] = f"Bearer {access_token}"

    def _configure_api_key_headers(self, headers: dict[str, str], api_key: str) -> None:
        """Configure headers for API key authentication."""
        # Remove OAuth headers if present
        headers.pop("Authorization", None)

        # Set API key
        headers["x-api-key"] = api_key

    def _apply_claude_code_headers(self, headers: dict[str, str]) -> None:
        """Apply Claude Code spoofing headers."""
        # Build beta features header
        beta_features = [
            ANTHROPIC_CONFIG.BETA_OAUTH,
            ANTHROPIC_CONFIG.BETA_CLAUDE_CODE,  # Critical for spoofing
            ANTHROPIC_CONFIG.BETA_INTERLEAVED_THINKING,
            # ANTHROPIC_CONFIG.BETA_FINE_GRAINED_STREAMING,
        ]

        # Set the beta header (this is what makes Anthropic think we're Claude Code)
        headers["anthropic-beta"] = ",".join(beta_features)

        # Set additional headers that Claude Code uses
        headers["anthropic-version"] = "2023-06-01"
        headers.setdefault("accept", "application/json")

        # Add Claude Code specific headers
        headers["user-agent"] = "Claude-Code/1.0"
        headers["x-client-id"] = ANTHROPIC_CONFIG.OAUTH_CLIENT_ID

        # Ensure content-type is set for POST requests
        headers.setdefault("content-type", "application/json")


class GlobalAnthropicInterceptor:
    """Global interceptor for automatic Anthropic request modification."""

    def __init__(self, storage: SecureAuthStorage):
        """
        Initialize global interceptor.

        Args:
            storage: Secure storage for credentials.
        """
        self.interceptor = AnthropicRequestInterceptor(storage)
        self.original_client_class = httpx.AsyncClient

    def install(self) -> None:
        """Install global request interception."""
        interceptor = self.interceptor

        class InterceptedAsyncClient(httpx.AsyncClient):
            """Custom AsyncClient that intercepts Anthropic requests."""

            async def request(self, method: str, url: URL | str, **kwargs: Any) -> httpx.Response:
                """Override request method to intercept Anthropic API calls."""
                # Convert URL to string if needed
                url_str = str(url)

                # Check if this is an Anthropic API request
                if "anthropic.com" in url_str or "claude.ai" in url_str:
                    # Intercept and modify request
                    kwargs = await interceptor.intercept_request(url_str, **kwargs)

                # Call original request method
                return await super().request(method, url, **kwargs)

        # Replace httpx.AsyncClient globally
        httpx.AsyncClient = InterceptedAsyncClient  # type: ignore

    def uninstall(self) -> None:
        """Uninstall global request interception."""
        httpx.AsyncClient = self.original_client_class  # type: ignore
