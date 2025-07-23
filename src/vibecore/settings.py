"""Settings configuration for Vibecore application."""

import os

from agents import Model, OpenAIChatCompletionsModel
from agents.models.multi_provider import MultiProvider
from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource

from vibecore.models import AnthropicModel


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
        description="Default model to use for agents (e.g., 'gpt-4.1', 'o3-mini', 'anthropic/claude-sonnet-4')",
    )

    # Agent configuration
    max_turns: int = Field(
        default=200,
        description="Maximum number of turns for agent conversation",
    )

    # Session persistence configuration
    session_dir: str = Field(
        default="~/.vibecore",
        description="Base directory for session storage",
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
