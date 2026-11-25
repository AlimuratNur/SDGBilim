from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from tests.conftest import FRONTEND_ORIGIN

CREDENTIAL_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_PROFILE",
    "ANTHROPIC_CONFIG_DIR",
    "ANTHROPIC_FEDERATION_RULE_ID",
    "ANTHROPIC_ORGANIZATION_ID",
    "ANTHROPIC_IDENTITY_TOKEN",
    "ANTHROPIC_IDENTITY_TOKEN_FILE",
]


@pytest.fixture
def no_anthropic_credentials(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in CREDENTIAL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    # An empty home directory: no `ant auth login` profile in ~/.config/anthropic either.
    monkeypatch.setenv("HOME", str(tmp_path))


@pytest.mark.usefixtures("no_anthropic_credentials")
def test_startup_fails_clearly_without_anthropic_credentials() -> None:
    app = create_app(Settings(_env_file=None))

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"), TestClient(app):
        pass


@pytest.mark.usefixtures("no_anthropic_credentials")
def test_startup_uses_api_key_from_settings() -> None:
    app = create_app(Settings(_env_file=None, anthropic_api_key=SecretStr("sk-ant-test")))

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
