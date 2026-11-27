"""The tutor on Claude (LLM_PROVIDER=anthropic): request shape and error mapping."""

from typing import Any

import anthropic
import pytest
from fastapi.testclient import TestClient

from tests.conftest import TEST_MODEL, FakeClaude, api_request, api_response

CHAT_ANSWER = {
    "reply": "Жақсы талпыныс! **Сен қайдансың?**",
    "corrections": [
        {"original": "Мен атым", "corrected": "Менің атым", "explanation": "Use «менің» (my)."}
    ],
    "new_words": [{"kk": "қайдан", "en": "where from", "ru": "откуда"}],
}


def chat_body() -> dict[str, Any]:
    return {
        "messages": [
            {"role": "assistant", "content": "Сәлем! I am your tutor."},
            {"role": "user", "content": "Мен атым Алихан"},
        ],
        "level": "beginner",
        "topic": "greetings",
    }


def test_chat_on_claude_reads_the_text_block_after_thinking(
    claude_client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with(CHAT_ANSWER)

    response = claude_client.post("/api/chat", json=chat_body())

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Жақсы талпыныс! **Сен қайдансың?**",
        "corrections": [
            {"original": "Мен атым", "corrected": "Менің атым", "explanation": "Use «менің» (my)."}
        ],
        "newWords": [{"kk": "қайдан", "en": "where from", "ru": "откуда"}],
    }


def test_chat_on_claude_sends_system_dialogue_and_json_schema(
    claude_client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with(CHAT_ANSWER)

    claude_client.post("/api/chat", json=chat_body())

    call = claude.last_call
    output_format = call["output_config"]["format"]
    assert call["model"] == TEST_MODEL
    assert "beginner" in call["system"]
    # The UI greeting is dropped: the dialogue sent to Claude starts with the student.
    assert call["messages"] == [{"role": "user", "content": "Мен атым Алихан"}]
    assert output_format["type"] == "json_schema"
    assert output_format["schema"]["required"] == ["reply", "corrections", "new_words"]


def test_translate_on_claude(claude_client: TestClient, claude: FakeClaude) -> None:
    claude.reply_with({"translation": "Рақмет", "transliteration": "Raqmet", "notes": ""})

    response = claude_client.post(
        "/api/translate", json={"text": "thank you", "from": "en", "to": "kk"}
    )

    assert response.status_code == 200
    assert response.json() == {"translation": "Рақмет", "transliteration": "Raqmet"}
    assert "<text>\nthank you\n</text>" in claude.last_call["messages"][0]["content"]


@pytest.mark.parametrize(
    ("stop_reason", "text", "status_code"),
    [
        pytest.param("refusal", "", 422, id="refusal"),
        pytest.param("max_tokens", '{"reply": "Сәл', 502, id="cut off"),
        pytest.param("end_turn", "not json", 502, id="invalid json"),
        pytest.param("end_turn", '{"reply": "no lists"}', 502, id="schema mismatch"),
    ],
)
def test_chat_on_claude_reports_unusable_answer(
    claude_client: TestClient, claude: FakeClaude, stop_reason: str, text: str, status_code: int
) -> None:
    claude.reply_with(text, stop_reason=stop_reason)

    response = claude_client.post("/api/chat", json=chat_body())

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        pytest.param(
            anthropic.RateLimitError("slow down", response=api_response(429), body=None),
            503,
            id="rate limited",
        ),
        pytest.param(anthropic.APIConnectionError(request=api_request()), 503, id="no network"),
        pytest.param(anthropic.APITimeoutError(request=api_request()), 503, id="timeout"),
        pytest.param(
            anthropic.AuthenticationError("bad key", response=api_response(401), body=None),
            500,
            id="bad api key",
        ),
        pytest.param(
            anthropic.NotFoundError("model", response=api_response(404), body=None),
            500,
            id="unknown model",
        ),
        pytest.param(
            anthropic.InternalServerError("boom", response=api_response(500), body=None),
            502,
            id="anthropic outage",
        ),
    ],
)
def test_chat_on_claude_maps_api_errors(
    claude_client: TestClient, claude: FakeClaude, error: Exception, status_code: int
) -> None:
    claude.fail_with(error)

    response = claude_client.post("/api/chat", json=chat_body())

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text
