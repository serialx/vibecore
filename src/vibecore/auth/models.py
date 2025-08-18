"""Data models for Anthropic authentication."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class OAuthCredentials:
    """OAuth credentials for Pro/Max users."""

    type: Literal["oauth"] = "oauth"
    refresh: str = ""  # Refresh token (long-lived)
    access: str = ""  # Access token (short-lived)
    expires: int = 0  # Unix timestamp in milliseconds


@dataclass
class ApiKeyCredentials:
    """API key credentials for standard users."""

    type: Literal["api"] = "api"
    key: str = ""  # API key


# Union type for both authentication methods
AnthropicAuth = OAuthCredentials | ApiKeyCredentials


@dataclass
class PKCEChallenge:
    """PKCE challenge pair for OAuth flow."""

    verifier: str
    challenge: str


@dataclass
class AuthorizationRequest:
    """OAuth authorization request details."""

    url: str
    verifier: str
    state: str = ""


@dataclass
class TokenResponse:
    """OAuth token response from server."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: str = ""
