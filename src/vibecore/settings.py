"""Settings configuration for Vibecore application."""

import os
from pathlib import Path
from typing import Literal

from agents import Model, OpenAIChatCompletionsModel
from agents.models.multi_provider import MultiProvider
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource

from vibecore.models import AnthropicModel


class SessionSettings(BaseModel):
    """Configuration for session storage."""

    storage_type: Literal["jsonl", "sqlite"] = Field(
        default="jsonl",
        description="Type of storage backend for sessions",
    )
    base_dir: Path = Field(
        default=Path.home() / ".vibecore",
        description="Base directory for session storage",
    )


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    name: str = Field(
        description="Unique name for this MCP server",
    )
    type: Literal["stdio", "sse", "http"] = Field(
        description="Type of MCP server connection",
    )

    # For stdio servers
    command: str | None = Field(
        default=None,
        description="Command to run for stdio servers (e.g., 'node /path/to/server.js')",
    )
    args: list[str] = Field(
        default_factory=list,
        description="Arguments for the stdio command",
    )
    env: dict[str, str] = Field(
        default_factory=dict,
        description="Environment variables for stdio servers",
    )

    # For SSE/HTTP servers
    url: str | None = Field(
        default=None,
        description="URL for SSE or HTTP servers",
    )

    # Tool filtering
    allowed_tools: list[str] | None = Field(
        default=None,
        description="List of allowed tool names (whitelist)",
    )
    blocked_tools: list[str] | None = Field(
        default=None,
        description="List of blocked tool names (blacklist)",
    )

    # Other options
    cache_tools: bool = Field(
        default=True,
        description="Whether to cache the tool list",
    )
    timeout_seconds: float | None = Field(
        default=30.0,
        description="Timeout for server operations",
    )


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="VIBECORE_",
        yaml_file=["config.yaml"],
        yaml_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Model configuration
    default_model: str = Field(
        # default="o3",
        # default="gpt-4.1",
        # default="qwen3-30b-a3b-mlx@8bit",
        # default="mistralai/devstral-small-2507",
        default="anthropic/claude-sonnet-4-20250514",
        # default="anthropic/claude-3-5-haiku-20241022",
        # default="litellm/deepseek/deepseek-chat",
        description="Default model to use for agents (e.g., 'gpt-4.1', 'o3-mini', 'anthropic/claude-sonnet-4')",
    )

    # Agent configuration
    max_turns: int = Field(
        default=200,
        description="Maximum number of turns for agent conversation",
    )
    reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = Field(
        default=None,
        description="Default reasoning effort level for agents (null, 'minimal', 'low', 'medium', 'high')",
    )

    # Session configuration
    session: SessionSettings = Field(
        default_factory=SessionSettings,
        description="Session storage configuration",
    )

    # MCP server configuration
    mcp_servers: list[MCPServerConfig] = Field(
        default_factory=list,
        description="List of MCP servers to connect to",
    )

    @property
    def model(self) -> str | Model:
        """Get the configured model.

        Returns an AnthropicModel instance if the model name starts with 'anthropic/',
        returns a OpenAIChatCompletionsModel instance if there is a custom base URL set,
        otherwise returns the model name as a plain string (for OpenAI/LiteLLM models).
        """
        custom_base = "OPENAI_BASE_URL" in os.environ
        if self.default_model.startswith("anthropic/"):
            return AnthropicModel(self.default_model)
        elif custom_base:
            openai_provider = MultiProvider().openai_provider
            return OpenAIChatCompletionsModel(self.default_model, openai_provider._get_client())
        return self.default_model

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configure settings sources to include YAML support."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


# Create a singleton settings instance
settings = Settings()
