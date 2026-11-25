from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration, read from environment variables and back/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # When empty, the Anthropic SDK resolves credentials itself
    # (ANTHROPIC_API_KEY in the process env, or an `ant auth login` profile).
    anthropic_api_key: SecretStr | None = None
    claude_model: str = "claude-haiku-5-5"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    request_timeout_seconds: float = 60.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value
