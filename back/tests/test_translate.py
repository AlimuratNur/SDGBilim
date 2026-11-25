from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeClaude


def translate_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"text": "thank you", "from": "en", "to": "kk"}
    return body | overrides


def test_translate_returns_translation_with_transliteration_and_notes(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with(
        {
            "translation": "Рақмет",
            "transliteration": "Raqmet",
            "notes": "«Рақмет сізге» is more polite.",
        }
    )

    response = client.post("/api/translate", json=translate_body())

    assert response.status_code == 200
    assert response.json() == {
        "translation": "Рақмет",
        "transliteration": "Raqmet",
        "notes": "«Рақмет сізге» is more polite.",
    }


def test_translate_omits_empty_transliteration_and_notes(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with({"translation": "Спасибо", "transliteration": "", "notes": ""})

    response = client.post("/api/translate", json=translate_body(to="ru"))

    assert response.json() == {"translation": "Спасибо"}


def test_translate_sends_text_and_language_pair_to_claude(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with({"translation": "Hello", "transliteration": "", "notes": ""})

    client.post(
        "/api/translate", json=translate_body(text="Сәлеметсіз бе", **{"from": "kk"}, to="en")
    )

    call = claude.last_call
    [message] = call["messages"]
    assert message["role"] == "user"
    assert "<text>\nСәлеметсіз бе\n</text>" in message["content"]
    assert "from Kazakh to English" in message["content"]
    assert call["output_config"]["format"]["type"] == "json_schema"


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"to": "en"}, id="same language"),
        pytest.param({"text": "   "}, id="blank text"),
        pytest.param({"text": "a" * 2001}, id="too long"),
        pytest.param({"to": "de"}, id="unsupported language"),
    ],
)
def test_translate_rejects_invalid_request(
    client: TestClient, claude: FakeClaude, overrides: dict[str, Any]
) -> None:
    response = client.post("/api/translate", json=translate_body(**overrides))

    assert response.status_code == 422
    assert claude.messages.calls == []


def test_translate_reports_refusal(client: TestClient, claude: FakeClaude) -> None:
    claude.reply_with("", stop_reason="refusal")

    response = client.post("/api/translate", json=translate_body())

    assert response.status_code == 422
    assert response.text
