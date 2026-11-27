from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# "anthropic": Claude through the Anthropic SDK.
# "openai": any OpenAI-compatible chat API (Meta Model API, Gemini, DeepSeek...).
Provider = Literal["openai", "anthropic"]

DEFAULT_MODELS: dict[Provider, str] = {
    "openai": "muse-spark-1.3",
    "anthropic": "claude-haiku-5-5",
}
DEFAULT_BASE_URLS: dict[Provider, str | None] = {
    "openai": "https://api.meta.ai/v1",
    "anthropic": None,  # the SDK's own endpoint
}


class Settings(BaseSettings):
    """Backend configuration, read from environment variables and back/.env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Provider = "openai"
    # The key of the provider above. Required; the SDKs' own key variables are never read.
    llm_api_key: SecretStr | None = None
    # Empty means the provider's default (DEFAULT_MODELS, DEFAULT_BASE_URLS).
    llm_model: str | None = None
    llm_base_url: str | None = None
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    request_timeout_seconds: float = 60.0

    @property
    def model(self) -> str:
        return self.llm_model or DEFAULT_MODELS[self.llm_provider]

    @property
    def base_url(self) -> str | None:
        return self.llm_base_url or DEFAULT_BASE_URLS[self.llm_provider]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value
