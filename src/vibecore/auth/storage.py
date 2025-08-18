"""Secure storage for authentication credentials."""

import json
import os
from pathlib import Path
from typing import Any

from vibecore.auth.models import AnthropicAuth, ApiKeyCredentials, OAuthCredentials


class SecureAuthStorage:
    """Secure storage for authentication credentials."""

    def __init__(self, app_name: str = "vibecore"):
        """
        Initialize secure storage.

        Args:
            app_name: Application name for storage directory.
        """
        # Store in user's local data directory
        self.storage_path = Path.home() / ".local" / "share" / app_name / "auth.json"

    async def save(self, provider: str, credentials: AnthropicAuth) -> None:
        """
        Save credentials securely.

        Args:
            provider: Provider name (e.g., "anthropic").
            credentials: Authentication credentials.
        """
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        data = await self._load_all()

        # Convert credentials to dict
        if isinstance(credentials, OAuthCredentials):
            cred_dict = {
                "type": "oauth",
                "refresh": credentials.refresh,
                "access": credentials.access,
                "expires": credentials.expires,
            }
        elif isinstance(credentials, ApiKeyCredentials):
            cred_dict = {"type": "api", "key": credentials.key}
        else:
            raise ValueError(f"Unknown credential type: {type(credentials)}")

        # Update credentials
        data[provider] = cred_dict

        # Write with secure permissions (owner read/write only)
        self.storage_path.write_text(json.dumps(data, indent=2))
        os.chmod(self.storage_path, 0o600)

    async def load(self, provider: str) -> AnthropicAuth | None:
        """
        Load credentials for a provider.

        Args:
            provider: Provider name.

        Returns:
            Authentication credentials or None if not found.
        """
        data = await self._load_all()
        cred_dict = data.get(provider)

        if not cred_dict:
            return None

        # Convert dict back to credentials object
        if cred_dict.get("type") == "oauth":
            return OAuthCredentials(
                type="oauth",
                refresh=cred_dict.get("refresh", ""),
                access=cred_dict.get("access", ""),
                expires=cred_dict.get("expires", 0),
            )
        elif cred_dict.get("type") == "api":
            return ApiKeyCredentials(type="api", key=cred_dict.get("key", ""))

        return None

    async def remove(self, provider: str) -> None:
        """
        Remove credentials for a provider.

        Args:
            provider: Provider name.
        """
        data = await self._load_all()
        data.pop(provider, None)
        self.storage_path.write_text(json.dumps(data, indent=2))
        os.chmod(self.storage_path, 0o600)

    async def _load_all(self) -> dict[str, Any]:
        """Load all stored credentials."""
        if not self.storage_path.exists():
            return {}

        try:
            return json.loads(self.storage_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def exists(self) -> bool:
        """Check if any credentials are stored."""
        return self.storage_path.exists() and self.storage_path.stat().st_size > 2
