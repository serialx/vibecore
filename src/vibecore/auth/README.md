# Anthropic Pro/Max Authentication Module

This module implements OAuth-based authentication for Anthropic Pro/Max subscribers.

## Features

- **OAuth 2.0 + PKCE Authentication**: Secure authentication flow for Pro/Max subscribers
- **Automatic Token Refresh**: Seamlessly refreshes OAuth tokens before expiry
- **Fallback Support**: Falls back to standard API key authentication when needed

## Usage

### CLI Commands

```bash
# Authenticate with Pro/Max (OAuth)
vibecore auth login anthropic

# Authenticate with API key
vibecore auth login anthropic --api-key sk-ant-xxx

# Check authentication status
vibecore auth status

# Test authentication
vibecore auth test

# Logout
vibecore auth logout anthropic
```

### Programmatic Usage

```python
from vibecore.auth import AnthropicAuthManager

# Initialize auth manager
auth_manager = AnthropicAuthManager()

# Authenticate with Pro/Max
await auth_manager.authenticate_pro_max()

# Or authenticate with API key
await auth_manager.authenticate_with_api_key("sk-ant-xxx")

# Check if authenticated
if await auth_manager.is_authenticated():
    auth_type = await auth_manager.get_auth_type()
    print(f"Authenticated with {auth_type}")
```

### Configuration

Enable Pro/Max authentication in your `config.yaml`:

```yaml
auth:
  use_pro_max: true
  auto_refresh: true
```

Or via environment variables:

```bash
export VIBECORE_AUTH_USE_PRO_MAX=true
export VIBECORE_AUTH_AUTO_REFRESH=true
```

## Architecture

### Core Components

1. **PKCEGenerator**: Generates cryptographically secure PKCE challenge pairs
2. **AnthropicOAuthFlow**: Handles the OAuth authorization flow
3. **SecureAuthStorage**: Stores credentials securely in local storage
4. **TokenRefreshManager**: Manages automatic token refresh
5. **AnthropicRequestInterceptor**: Intercepts requests to add Claude Code headers
6. **AnthropicAuthManager**: Main manager coordinating all auth operations

### Authentication Flow

1. User initiates OAuth flow via CLI or programmatically
2. Browser opens for user authorization on claude.ai
3. User authorizes and receives authorization code
4. Code is exchanged for access and refresh tokens
5. Tokens are stored securely in `~/.local/share/vibecore/auth.json`
6. Requests automatically use OAuth tokens and Claude Code headers
7. Tokens are refreshed automatically before expiry

### Security

- Credentials stored with 0600 permissions (owner read/write only)
- PKCE used for OAuth flow security
- Tokens never logged or exposed
- Automatic token refresh prevents expiry

## Implementation Details

### Claude Code Spoofing

The module adds critical headers to make requests appear as Claude Code:

```python
headers["anthropic-beta"] = "oauth-2025-04-20,claude-code-20250219,..."
```

### Token Refresh

Tokens are automatically refreshed 5 minutes before expiry:

```python
buffer_ms = 300 * 1000  # 5 minutes
if token.expires <= now + buffer_ms:
    # Refresh token
```

## Testing

Run the auth tests:

```bash
uv run pytest tests/auth/
```

## Troubleshooting

### Authentication Fails

1. Ensure you have a valid Pro/Max subscription
2. Check that the browser opens correctly
3. Copy the complete authorization code including the part after `#`

### Token Refresh Issues

1. Check network connectivity
2. Verify stored credentials aren't corrupted
3. Try re-authenticating

### Import Errors

The pyright errors about unresolved imports are false positives. The module works correctly at runtime.