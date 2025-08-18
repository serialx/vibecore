"""Configuration constants for Anthropic authentication."""

from typing import Final


class AnthropicConfig:
    """Configuration for Anthropic OAuth and API."""

    # OAuth Client Configuration
    OAUTH_CLIENT_ID: Final[str] = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
    OAUTH_SCOPES: Final[str] = "org:create_api_key user:profile user:inference"
    OAUTH_REDIRECT_URI: Final[str] = "https://console.anthropic.com/oauth/code/callback"
    OAUTH_RESPONSE_TYPE: Final[str] = "code"
    OAUTH_CODE_CHALLENGE_METHOD: Final[str] = "S256"

    # API Endpoints
    CLAUDE_AI_AUTHORIZE: Final[str] = "https://claude.ai/oauth/authorize"
    CONSOLE_AUTHORIZE: Final[str] = "https://console.anthropic.com/oauth/authorize"
    TOKEN_EXCHANGE: Final[str] = "https://console.anthropic.com/v1/oauth/token"
    API_BASE: Final[str] = "https://api.anthropic.com"
    MESSAGES: Final[str] = "https://api.anthropic.com/v1/messages"

    # Beta Headers (Critical for Claude Code spoofing)
    BETA_OAUTH: Final[str] = "oauth-2025-04-20"
    BETA_CLAUDE_CODE: Final[str] = "claude-code-20250219"  # CRITICAL: Identifies as Claude Code
    BETA_INTERLEAVED_THINKING: Final[str] = "interleaved-thinking-2025-05-14"
    BETA_FINE_GRAINED_STREAMING: Final[str] = "fine-grained-tool-streaming-2025-05-14"

    # Token Management
    TOKEN_REFRESH_BUFFER_SECONDS: Final[int] = 300  # Refresh 5 minutes before expiry
    TOKEN_MAX_RETRY_ATTEMPTS: Final[int] = 3
    TOKEN_RETRY_DELAY_MS: Final[int] = 1000

    # Claude Code Identity
    CLAUDE_CODE_IDENTITY: Final[str] = "You are Claude Code, Anthropic's official CLI for Claude."


ANTHROPIC_CONFIG = AnthropicConfig()
