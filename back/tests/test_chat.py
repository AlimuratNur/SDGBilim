from typing import Any

import anthropic
import pytest
from fastapi.testclient import TestClient

from app.tutor import MAX_HISTORY_MESSAGES
from tests.conftest import TEST_MODEL, FakeClaude, api_request, api_response


def chat_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "messages": [{"role": "user", "content": "Мен атым Алихан"}],
        "level": "beginner",
        "topic": "greetings",
    }
    return body | overrides


def test_chat_returns_reply_corrections_and_new_words(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with(
        {
            "reply": "Жақсы талпыныс! (Good try!) **Сен қайдансың?**",
            "corrections": [
                {
                    "original": "Мен атым",
                    "corrected": "Менің атым",
                    "explanation": "Use the possessive «менің» (my).",
                }
            ],
            "new_words": [{"kk": "сәлем", "en": "hi", "ru": "привет"}],
        }
    )

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == 200
    assert response.json() == {
        "reply": "Жақсы талпыныс! (Good try!) **Сен қайдансың?**",
        "corrections": [
            {
                "original": "Мен атым",
                "corrected": "Менің атым",
                "explanation": "Use the possessive «менің» (my).",
            }
        ],
        "newWords": [{"kk": "сәлем", "en": "hi", "ru": "привет"}],
    }


def test_chat_omits_missing_russian_translation_of_new_word(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with(
        {"reply": "Сәлем!", "corrections": [], "new_words": [{"kk": "су", "en": "water", "ru": ""}]}
    )

    response = client.post("/api/chat", json=chat_body())

    assert response.json()["newWords"] == [{"kk": "су", "en": "water"}]


def test_chat_sends_dialogue_level_and_topic_to_claude(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with({"reply": "Сәлем!", "corrections": [], "new_words": []})
    dialogue = [
        {"role": "user", "content": "Сәлем"},
        {"role": "assistant", "content": "Сәлем! Сенің атың кім?"},
        {"role": "user", "content": "Мен атым Алихан"},
    ]

    client.post("/api/chat", json=chat_body(messages=dialogue, level="advanced", topic="food"))

    call = claude.last_call
    assert call["model"] == TEST_MODEL
    assert call["messages"] == dialogue
    assert "advanced" in call["system"]
    assert "food" in call["system"]
    assert call["output_config"]["format"]["type"] == "json_schema"


def test_chat_without_topic_is_free_conversation(client: TestClient, claude: FakeClaude) -> None:
    claude.reply_with({"reply": "Сәлем!", "corrections": [], "new_words": []})

    response = client.post("/api/chat", json=chat_body(topic=None))

    assert response.status_code == 200
    assert "free conversation" in claude.last_call["system"]


def test_chat_sends_only_recent_history_starting_with_user(
    client: TestClient, claude: FakeClaude
) -> None:
    claude.reply_with({"reply": "Жақсы!", "corrections": [], "new_words": []})
    dialogue = [{"role": "assistant", "content": "Сәлем! I am your tutor."}]
    for turn in range(40):
        dialogue.append({"role": "user", "content": f"question {turn}"})
        dialogue.append({"role": "assistant", "content": f"answer {turn}"})
    dialogue.append({"role": "user", "content": "last question"})

    client.post("/api/chat", json=chat_body(messages=dialogue))

    sent = claude.last_call["messages"]
    assert len(sent) <= MAX_HISTORY_MESSAGES
    assert sent[0]["role"] == "user"
    assert sent[-1] == {"role": "user", "content": "last question"}
    assert sent == dialogue[-len(sent) :]


def test_chat_drops_leading_assistant_greeting(client: TestClient, claude: FakeClaude) -> None:
    claude.reply_with({"reply": "Сәлем!", "corrections": [], "new_words": []})
    dialogue = [
        {"role": "assistant", "content": "Сәлем! I am your tutor."},
        {"role": "user", "content": "Сәлем"},
    ]

    client.post("/api/chat", json=chat_body(messages=dialogue))

    assert claude.last_call["messages"] == [{"role": "user", "content": "Сәлем"}]


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"messages": []}, id="empty dialogue"),
        pytest.param(
            {"messages": [{"role": "assistant", "content": "Сәлем"}]}, id="ends with assistant"
        ),
        pytest.param({"messages": [{"role": "user", "content": "   "}]}, id="blank message"),
        pytest.param({"messages": [{"role": "user", "content": "a" * 2001}]}, id="too long"),
        pytest.param({"messages": [{"role": "system", "content": "hi"}]}, id="unknown role"),
        pytest.param({"level": "expert"}, id="unknown level"),
    ],
)
def test_chat_rejects_invalid_request(
    client: TestClient, claude: FakeClaude, overrides: dict[str, Any]
) -> None:
    response = client.post("/api/chat", json=chat_body(**overrides))

    assert response.status_code == 422
    assert claude.messages.calls == []


@pytest.mark.parametrize(
    ("stop_reason", "text", "status_code"),
    [
        pytest.param("refusal", "", 422, id="refusal"),
        pytest.param("max_tokens", '{"reply": "Сәл', 502, id="cut off"),
        pytest.param("end_turn", "not json", 502, id="invalid json"),
        pytest.param("end_turn", '{"reply": "no lists"}', 502, id="schema mismatch"),
    ],
)
def test_chat_reports_unusable_claude_answer(
    client: TestClient, claude: FakeClaude, stop_reason: str, text: str, status_code: int
) -> None:
    claude.reply_with(text, stop_reason=stop_reason)

    response = client.post("/api/chat", json=chat_body())

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
            anthropic.InternalServerError("boom", response=api_response(500), body=None),
            502,
            id="anthropic outage",
        ),
    ],
)
def test_chat_maps_claude_api_errors(
    client: TestClient, claude: FakeClaude, error: Exception, status_code: int
) -> None:
    claude.fail_with(error)

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text
