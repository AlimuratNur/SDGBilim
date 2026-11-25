from typing import Annotated

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration, read from environment variables and back/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Any OpenAI-compatible chat API. Defaults: Meta Model API (https://dev.meta.ai/docs).
    llm_api_key: SecretStr | None = None
    llm_model: str = "muse-spark-1.3"
    llm_base_url: str = "https://api.meta.ai/v1"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    request_timeout_seconds: float = 60.0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value
