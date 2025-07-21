"""Settings configuration for Vibecore application."""

from agents.extensions.models.litellm_model import LitellmModel
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
        # default="gpt-4.1",
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
    def model(self) -> str | LitellmModel:
        """Get the configured model.

        Returns an AnthropicModel instance if the model name starts with 'anthropic/',
        returns a LitellmModel instance if the model name contains '/',
        otherwise returns the model name as a plain string (for OpenAI models).
        """
        if self.default_model.startswith("anthropic/"):
            return AnthropicModel(self.default_model)
        elif "/" in self.default_model:
            return LitellmModel(self.default_model)
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
