"""Token management for OAuth authentication."""

import asyncio
import time

import httpx

from vibecore.auth.config import ANTHROPIC_CONFIG
from vibecore.auth.models import OAuthCredentials
from vibecore.auth.storage import SecureAuthStorage


class TokenRefreshManager:
    """Manages OAuth token refresh with automatic renewal."""

    def __init__(self, storage: SecureAuthStorage):
        """
        Initialize token refresh manager.

        Args:
            storage: Secure storage for credentials.
        """
        self.storage = storage
        self.refresh_lock = asyncio.Lock()
        self.refresh_task: asyncio.Task | None = None

    async def get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.

        Returns:
            Valid access token.

        Raises:
            ValueError: If not authenticated or refresh fails.
        """
        auth = await self.storage.load("anthropic")

        if not auth:
            raise ValueError("Not authenticated")

        if auth.type == "api":  # API key auth
            return auth.key  # type: ignore

        # OAuth auth - check if token needs refresh
        now = int(time.time() * 1000)
        buffer_ms = ANTHROPIC_CONFIG.TOKEN_REFRESH_BUFFER_SECONDS * 1000
        needs_refresh = not auth.access or auth.expires <= now + buffer_ms  # type: ignore

        if not needs_refresh:
            return auth.access  # type: ignore

        # Refresh token with lock to prevent concurrent refreshes
        async with self.refresh_lock:
            # Re-check after acquiring lock
            auth = await self.storage.load("anthropic")
            if auth and auth.type == "oauth":
                now = int(time.time() * 1000)
                if auth.access and auth.expires > now + buffer_ms:  # type: ignore
                    return auth.access  # type: ignore

            # Perform refresh
            if auth and auth.type == "oauth":
                return await self._refresh_token(auth.refresh)  # type: ignore
            else:
                raise ValueError("Cannot refresh non-OAuth credentials")

    async def _refresh_token(self, refresh_token: str) -> str:
        """
        Refresh the access token.

        Args:
            refresh_token: Refresh token.

        Returns:
            New access token.

        Raises:
            httpx.HTTPError: If refresh fails after retries.
        """
        last_error: Exception | None = None

        # Retry logic
        for attempt in range(ANTHROPIC_CONFIG.TOKEN_MAX_RETRY_ATTEMPTS):
            try:
                # Exponential backoff for retries
                if attempt > 0:
                    delay = ANTHROPIC_CONFIG.TOKEN_RETRY_DELAY_MS * (2 ** (attempt - 1)) / 1000
                    await asyncio.sleep(delay)

                # Make refresh request
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        ANTHROPIC_CONFIG.TOKEN_EXCHANGE,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                        },
                        json={
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": ANTHROPIC_CONFIG.OAUTH_CLIENT_ID,
                        },
                        timeout=30.0,
                    )

                    if response.status_code != 200:
                        error_text = response.text
                        raise httpx.HTTPError(f"Token refresh failed: {response.status_code} - {error_text}")

                    tokens_data = response.json()

                # Update stored credentials
                new_credentials = OAuthCredentials(
                    type="oauth",
                    refresh=tokens_data.get("refresh_token", refresh_token),
                    access=tokens_data["access_token"],
                    expires=int(time.time() * 1000) + tokens_data["expires_in"] * 1000,
                )

                await self.storage.save("anthropic", new_credentials)
                return tokens_data["access_token"]

            except Exception as error:
                last_error = error
                print(f"Token refresh attempt {attempt + 1} failed: {error}")

        # All retries failed
        raise ValueError(
            f"Token refresh failed after {ANTHROPIC_CONFIG.TOKEN_MAX_RETRY_ATTEMPTS} attempts: {last_error}"
        )
