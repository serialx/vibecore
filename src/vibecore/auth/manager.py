"""Main authentication manager for Anthropic Pro/Max."""

from vibecore.auth.config import ANTHROPIC_CONFIG
from vibecore.auth.interceptor import GlobalAnthropicInterceptor
from vibecore.auth.models import ApiKeyCredentials
from vibecore.auth.oauth_flow import AnthropicOAuthFlow
from vibecore.auth.storage import SecureAuthStorage
from vibecore.auth.token_manager import TokenRefreshManager


class AnthropicAuthManager:
    """Main manager for Anthropic authentication."""

    def __init__(self, app_name: str = "vibecore"):
        """
        Initialize authentication manager.

        Args:
            app_name: Application name for storage.
        """
        self.storage = SecureAuthStorage(app_name)
        self.oauth_flow = AnthropicOAuthFlow()
        self.token_manager = TokenRefreshManager(self.storage)
        self.interceptor = GlobalAnthropicInterceptor(self.storage)

    async def authenticate_pro_max(self, mode: str = "max") -> bool:
        """
        Authenticate with Pro/Max subscription via OAuth.

        Args:
            mode: "max" for claude.ai, "console" for console.anthropic.com.

        Returns:
            True if authentication successful.
        """
        try:
            # Step 1: Initiate OAuth flow
            auth_request = await self.oauth_flow.initiate(mode)

            # Step 2: Open browser for user authorization
            print("\n🌐 Opening browser for authentication...")
            print(f"   If browser doesn't open, visit: {auth_request.url}\n")
            self.oauth_flow.open_browser(auth_request.url)

            # Step 3: Wait for user to provide authorization code
            print("After authorizing, you'll be redirected to a page showing an authorization code.")
            print("Copy the entire code (including the part after #) and paste it below.\n")
            auth_code = input("Authorization code: ").strip()

            if not auth_code:
                print("❌ No authorization code provided")
                return False

            # Step 4: Exchange code for tokens
            print("🔄 Exchanging authorization code for tokens...")
            credentials = await self.oauth_flow.exchange(auth_code)

            # Step 5: Save credentials securely
            await self.storage.save("anthropic", credentials)

            print("✅ Authentication successful! You're now using Claude Pro/Max.\n")
            return True

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False

    async def authenticate_with_api_key(self, api_key: str) -> bool:
        """
        Authenticate with API key.

        Args:
            api_key: Anthropic API key.

        Returns:
            True if authentication successful.
        """
        try:
            # Validate API key format
            if not api_key.startswith("sk-ant-"):
                print("❌ Invalid API key format. Anthropic keys start with 'sk-ant-'")
                return False

            credentials = ApiKeyCredentials(type="api", key=api_key)
            await self.storage.save("anthropic", credentials)

            print("✅ API key saved successfully!")
            return True

        except Exception as e:
            print(f"❌ Failed to save API key: {e}")
            return False

    async def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        auth = await self.storage.load("anthropic")
        return auth is not None

    async def get_auth_type(self) -> str | None:
        """
        Get current authentication type.

        Returns:
            "oauth" for Pro/Max, "api" for API key, None if not authenticated.
        """
        auth = await self.storage.load("anthropic")
        if auth:
            return auth.type
        return None

    async def logout(self) -> None:
        """Remove stored authentication."""
        await self.storage.remove("anthropic")
        print("✅ Logged out successfully")

    def install_interceptor(self) -> None:
        """Install global request interceptor for Claude Code spoofing."""
        self.interceptor.install()

    def uninstall_interceptor(self) -> None:
        """Uninstall global request interceptor."""
        self.interceptor.uninstall()

    async def test_connection(self) -> bool:
        """
        Test the authentication by making a simple API call.

        Returns:
            True if connection successful.
        """
        try:
            import httpx

            # Get auth headers
            auth = await self.storage.load("anthropic")
            if not auth:
                print("❌ Not authenticated")
                return False

            headers = {}
            if auth.type == "oauth":  # OAuth
                token = await self.token_manager.get_valid_token()
                headers["Authorization"] = f"Bearer {token}"
            else:  # API key
                headers["x-api-key"] = auth.key  # type: ignore

            # Add Claude Code headers
            headers["anthropic-beta"] = ",".join(
                [
                    ANTHROPIC_CONFIG.BETA_OAUTH,
                    ANTHROPIC_CONFIG.BETA_CLAUDE_CODE,
                ]
            )
            headers["anthropic-version"] = "2023-06-01"

            # Make test request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    print("✅ Connection test successful!")
                    return True
                else:
                    print(f"❌ Connection test failed: {response.status_code}")
                    return False

        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False
