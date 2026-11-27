import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.config import Provider, Settings
from app.llm import AnthropicLLM, OpenAICompatibleLLM, build_llm
from app.main import create_app
from tests.conftest import FRONTEND_ORIGIN

LLM_ENV_VARS = ["LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL"]


@pytest.fixture
def no_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in LLM_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.mark.usefixtures("no_llm_env")
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_startup_fails_clearly_without_llm_key(provider: Provider) -> None:
    app = create_app(Settings(_env_file=None, llm_provider=provider))

    with pytest.raises(RuntimeError, match="LLM_API_KEY"), TestClient(app):
        pass


@pytest.mark.usefixtures("no_llm_env")
@pytest.mark.parametrize(
    ("provider", "sdk_variable"),
    [("openai", "OPENAI_API_KEY"), ("anthropic", "ANTHROPIC_API_KEY")],
)
def test_startup_ignores_the_sdk_key_variables(
    monkeypatch: pytest.MonkeyPatch, provider: Provider, sdk_variable: str
) -> None:
    # The SDKs fall back to their own variables; the backend reads only LLM_API_KEY.
    monkeypatch.setenv(sdk_variable, "sdk-key-test")
    app = create_app(Settings(_env_file=None, llm_provider=provider))

    with pytest.raises(RuntimeError, match="LLM_API_KEY"), TestClient(app):
        pass


@pytest.mark.usefixtures("no_llm_env")
@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_startup_uses_api_key_from_settings(provider: Provider) -> None:
    settings = Settings(_env_file=None, llm_provider=provider, llm_api_key=SecretStr("test-key"))

    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health").status_code == 200


@pytest.mark.usefixtures("no_llm_env")
@pytest.mark.parametrize(
    ("provider", "client_type"),
    [("openai", OpenAICompatibleLLM), ("anthropic", AnthropicLLM)],
)
def test_llm_provider_picks_the_client(provider: Provider, client_type: type) -> None:
    settings = Settings(_env_file=None, llm_provider=provider, llm_api_key=SecretStr("test-key"))

    assert isinstance(build_llm(settings), client_type)


@pytest.mark.usefixtures("no_llm_env")
@pytest.mark.parametrize(
    ("provider", "model", "base_url"),
    [
        ("openai", "muse-spark-1.3", "https://api.meta.ai/v1"),
        ("anthropic", "claude-haiku-5-5", None),
    ],
)
def test_settings_default_model_and_url_per_provider(
    provider: Provider, model: str, base_url: str | None
) -> None:
    settings = Settings(_env_file=None, llm_provider=provider)

    assert settings.model == model
    assert settings.base_url == base_url


@pytest.mark.usefixtures("no_llm_env")
def test_settings_default_to_openai_compatible_provider() -> None:
    assert Settings(_env_file=None).llm_provider == "openai"


@pytest.mark.usefixtures("no_llm_env")
def test_settings_reject_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_frontend_origin(client: TestClient) -> None:
    response = client.options(
        "/api/chat",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


def test_cors_rejects_unknown_origin(client: TestClient) -> None:
    response = client.options(
        "/api/chat",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert "access-control-allow-origin" not in response.headers


def test_settings_read_comma_separated_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, https://bilim.example ,")

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["http://localhost:5173", "https://bilim.example"]
