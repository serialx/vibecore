"""OAuth flow implementation for Anthropic Pro/Max authentication."""

import time
import webbrowser
from urllib.parse import urlencode

import httpx

from vibecore.auth.config import ANTHROPIC_CONFIG
from vibecore.auth.models import AuthorizationRequest, OAuthCredentials, PKCEChallenge
from vibecore.auth.pkce import PKCEGenerator


class AnthropicOAuthFlow:
    """Handles OAuth flow for Pro/Max authentication."""

    def __init__(self):
        """Initialize OAuth flow handler."""
        self.pkce_challenge: PKCEChallenge | None = None

    async def initiate(self, mode: str = "max") -> AuthorizationRequest:
        """
        Initiate OAuth flow for Pro/Max authentication.

        Args:
            mode: "max" for claude.ai, "console" for console.anthropic.com.

        Returns:
            Authorization request with URL and PKCE verifier.
        """
        # Generate PKCE challenge
        self.pkce_challenge = PKCEGenerator.generate()

        # Select appropriate authorization endpoint
        base_url = ANTHROPIC_CONFIG.CLAUDE_AI_AUTHORIZE if mode == "max" else ANTHROPIC_CONFIG.CONSOLE_AUTHORIZE

        # Build authorization URL with all required parameters
        params = {
            "code": "true",
            "client_id": ANTHROPIC_CONFIG.OAUTH_CLIENT_ID,
            "response_type": ANTHROPIC_CONFIG.OAUTH_RESPONSE_TYPE,
            "redirect_uri": ANTHROPIC_CONFIG.OAUTH_REDIRECT_URI,
            "scope": ANTHROPIC_CONFIG.OAUTH_SCOPES,
            "code_challenge": self.pkce_challenge.challenge,
            "code_challenge_method": ANTHROPIC_CONFIG.OAUTH_CODE_CHALLENGE_METHOD,
            "state": self.pkce_challenge.verifier,  # Using verifier as state
        }

        # Create full URL
        auth_url = f"{base_url}?{urlencode(params)}"

        return AuthorizationRequest(
            url=auth_url,
            verifier=self.pkce_challenge.verifier,
            state=self.pkce_challenge.verifier,
        )

    async def exchange(self, auth_code: str) -> OAuthCredentials:
        """
        Exchange authorization code for tokens.

        Args:
            auth_code: Format: "code#state" from callback.

        Returns:
            OAuth credentials with access and refresh tokens.

        Raises:
            ValueError: If OAuth flow not initiated or invalid code format.
            httpx.HTTPError: If token exchange fails.
        """
        if not self.pkce_challenge:
            raise ValueError("OAuth flow not initiated")

        # Parse the authorization code
        parts = auth_code.split("#")
        if len(parts) != 2:
            raise ValueError("Invalid authorization code format. Expected: code#state")

        code, state = parts

        # Prepare token exchange request
        request_body = {
            "code": code,
            "state": state,
            "grant_type": "authorization_code",
            "client_id": ANTHROPIC_CONFIG.OAUTH_CLIENT_ID,
            "redirect_uri": ANTHROPIC_CONFIG.OAUTH_REDIRECT_URI,
            "code_verifier": self.pkce_challenge.verifier,
        }

        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                ANTHROPIC_CONFIG.TOKEN_EXCHANGE,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=request_body,
            )

            if response.status_code != 200:
                error_text = response.text
                raise httpx.HTTPError(f"Token exchange failed: {response.status_code} - {error_text}")

            tokens_data = response.json()

        # Create credentials object
        credentials = OAuthCredentials(
            type="oauth",
            refresh=tokens_data["refresh_token"],
            access=tokens_data["access_token"],
            expires=int(time.time() * 1000) + tokens_data["expires_in"] * 1000,
        )

        # Clear PKCE challenge
        self.pkce_challenge = None

        return credentials

    def open_browser(self, url: str) -> None:
        """
        Open browser for user authorization.

        Args:
            url: Authorization URL.
        """
        webbrowser.open(url)
