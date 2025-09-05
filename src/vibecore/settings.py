"""Settings configuration for Vibecore application."""

import os
from pathlib import Path
from typing import Literal

from agents import Model, ModelSettings, OpenAIChatCompletionsModel
from agents.models.multi_provider import MultiProvider
from openai.types import Reasoning
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource

from vibecore.models import AnthropicModel


class AuthSettings(BaseModel):
    """Configuration for authentication."""

    use_pro_max: bool = Field(
        default=False,
        description="Use Anthropic Pro/Max authentication if available",
    )
    auto_refresh: bool = Field(
        default=True,
        description="Automatically refresh OAuth tokens",
    )


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


class PathConfinementSettings(BaseModel):
    """Configuration for path confinement."""

    enabled: bool = Field(
        default=True,
        description="Enable path confinement for file and shell tools",
    )

    allowed_directories: list[Path] = Field(
        default_factory=lambda: [Path.cwd()],
        description="List of directories that tools can access",
    )

    allow_home: bool = Field(
        default=False,
        description="Allow access to user's home directory",
    )

    allow_temp: bool = Field(
        default=True,
        description="Allow access to system temp directories",
    )

    strict_mode: bool = Field(
        default=False,
        description="Strict mode prevents any path traversal attempts",
    )

    @field_validator("allowed_directories", mode="before")
    @classmethod
    def resolve_paths(cls, v: list[str | Path]) -> list[Path]:
        """Resolve and validate directory paths."""
        paths = []
        for p in v:
            path = Path(p).expanduser().resolve()
            if not path.exists():
                # Create directory if it doesn't exist
                path.mkdir(parents=True, exist_ok=True)
            paths.append(path)
        return paths


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
        default="gpt-5",
        # default="qwen3-30b-a3b-mlx@8bit",
        # default="mistralai/devstral-small-2507",
        # default="anthropic/claude-sonnet-4-20250514",
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
    reasoning_summary: Literal["auto", "concise", "detailed"] | None = Field(
        default="auto",
        description="Reasoning summary mode ('auto', 'concise', 'detailed', or 'off')",
    )

    @field_validator("reasoning_summary", mode="before")
    @classmethod
    def validate_reasoning_summary(cls, v):
        """Convert string 'null' to None for reasoning_summary field."""
        if v == "off" or v == "":
            return None
        return v

    # Authentication configuration
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description="Authentication configuration",
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

    # Path confinement configuration
    path_confinement: PathConfinementSettings = Field(
        default_factory=PathConfinementSettings,
        description="Path confinement configuration",
    )

    rich_tool_names: list[str] = Field(
        default_factory=list,
        description="List of tools to render with RichToolMessage (temporary settings)",
    )

    @property
    def model(self) -> str | Model:
        """Get the configured model.

        Returns an AnthropicProMaxModel instance if auth is enabled and model is Anthropic,
        returns an AnthropicModel instance if the model name starts with 'anthropic/',
        returns a OpenAIChatCompletionsModel instance if there is a custom base URL set,
        otherwise returns the model name as a plain string (for OpenAI/LiteLLM models).
        """
        custom_base = "OPENAI_BASE_URL" in os.environ
        if self.default_model.startswith("anthropic/"):
            # Check if Pro/Max auth should be used
            if self.auth.use_pro_max:
                from vibecore.models.anthropic_auth import AnthropicProMaxModel

                return AnthropicProMaxModel(self.default_model, use_auth=True)
            else:
                return AnthropicModel(self.default_model)
        elif custom_base:
            openai_provider = MultiProvider().openai_provider
            return OpenAIChatCompletionsModel(self.default_model, openai_provider._get_client())
        return self.default_model

    @property
    def default_model_settings(self) -> ModelSettings:
        """Get the default model settings."""
        return ModelSettings(
            include_usage=True,
            reasoning=Reasoning(
                summary=self.reasoning_summary,
                effort=self.reasoning_effort,
            ),
        )

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
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


# Create a singleton settings instance
settings = Settings()
