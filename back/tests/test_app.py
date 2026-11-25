import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from tests.conftest import FRONTEND_ORIGIN


@pytest.fixture
def no_deepseek_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)


@pytest.mark.usefixtures("no_deepseek_key")
def test_startup_fails_clearly_without_deepseek_key() -> None:
    app = create_app(Settings(_env_file=None))

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"), TestClient(app):
        pass


@pytest.mark.usefixtures("no_deepseek_key")
def test_startup_never_sends_an_openai_key_to_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    # The OpenAI SDK falls back to OPENAI_API_KEY; the backend must not.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    app = create_app(Settings(_env_file=None))

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"), TestClient(app):
        pass


@pytest.mark.usefixtures("no_deepseek_key")
def test_startup_uses_api_key_from_settings() -> None:
    app = create_app(Settings(_env_file=None, deepseek_api_key=SecretStr("sk-test")))

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200


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
