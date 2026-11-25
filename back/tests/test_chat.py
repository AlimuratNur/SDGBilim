from typing import Any

import openai
import pytest
from fastapi.testclient import TestClient

from app.tutor import MAX_HISTORY_MESSAGES
from tests.conftest import TEST_MODEL, FakeLLM, api_request, api_response

EMPTY_ANSWER = {"reply": "Сәлем!", "corrections": [], "new_words": []}


def chat_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "messages": [{"role": "user", "content": "Мен атым Алихан"}],
        "level": "beginner",
        "topic": "greetings",
    }
    return body | overrides


def test_chat_returns_reply_corrections_and_new_words(client: TestClient, llm: FakeLLM) -> None:
    llm.reply_with(
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
    client: TestClient, llm: FakeLLM
) -> None:
    llm.reply_with(
        {"reply": "Сәлем!", "corrections": [], "new_words": [{"kk": "су", "en": "water", "ru": ""}]}
    )

    response = client.post("/api/chat", json=chat_body())

    assert response.json()["newWords"] == [{"kk": "су", "en": "water"}]


def test_chat_sends_system_prompt_and_dialogue_to_the_model(
    client: TestClient, llm: FakeLLM
) -> None:
    llm.reply_with(EMPTY_ANSWER)
    dialogue = [
        {"role": "user", "content": "Сәлем"},
        {"role": "assistant", "content": "Сәлем! Сенің атың кім?"},
        {"role": "user", "content": "Мен атым Алихан"},
    ]

    client.post("/api/chat", json=chat_body(messages=dialogue, level="advanced", topic="food"))

    call = llm.last_call
    system, *sent = call["messages"]
    assert call["model"] == TEST_MODEL
    assert system["role"] == "system"
    assert "advanced" in system["content"]
    assert "food" in system["content"]
    assert sent == dialogue


def test_chat_asks_for_an_answer_matching_the_json_schema(client: TestClient, llm: FakeLLM) -> None:
    llm.reply_with(EMPTY_ANSWER)

    client.post("/api/chat", json=chat_body())

    response_format = llm.last_call["response_format"]
    schema = response_format["json_schema"]["schema"]
    assert response_format["type"] == "json_schema"
    assert schema["required"] == ["reply", "corrections", "new_words"]
    assert schema["additionalProperties"] is False


def test_chat_without_topic_is_free_conversation(client: TestClient, llm: FakeLLM) -> None:
    llm.reply_with(EMPTY_ANSWER)

    response = client.post("/api/chat", json=chat_body(topic=None))

    assert response.status_code == 200
    assert "free conversation" in llm.last_call["messages"][0]["content"]


def test_chat_sends_only_recent_history_starting_with_user(
    client: TestClient, llm: FakeLLM
) -> None:
    llm.reply_with(EMPTY_ANSWER)
    dialogue = [{"role": "assistant", "content": "Сәлем! I am your tutor."}]
    for turn in range(40):
        dialogue.append({"role": "user", "content": f"question {turn}"})
        dialogue.append({"role": "assistant", "content": f"answer {turn}"})
    dialogue.append({"role": "user", "content": "last question"})

    client.post("/api/chat", json=chat_body(messages=dialogue))

    sent = llm.last_call["messages"][1:]
    assert len(sent) <= MAX_HISTORY_MESSAGES
    assert sent[0]["role"] == "user"
    assert sent[-1] == {"role": "user", "content": "last question"}
    assert sent == dialogue[-len(sent) :]


def test_chat_drops_leading_assistant_greeting(client: TestClient, llm: FakeLLM) -> None:
    llm.reply_with(EMPTY_ANSWER)
    dialogue = [
        {"role": "assistant", "content": "Сәлем! I am your tutor."},
        {"role": "user", "content": "Сәлем"},
    ]

    client.post("/api/chat", json=chat_body(messages=dialogue))

    assert llm.last_call["messages"][1:] == [{"role": "user", "content": "Сәлем"}]


def test_chat_retries_once_when_the_model_returns_blank_content(
    client: TestClient, llm: FakeLLM
) -> None:
    llm.reply_with("   ")
    llm.reply_with(EMPTY_ANSWER)

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == 200
    assert response.json()["reply"] == "Сәлем!"
    assert len(llm.calls) == 2


def test_chat_gives_up_when_content_stays_blank(client: TestClient, llm: FakeLLM) -> None:
    llm.reply_with("   ")

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == 502
    assert len(llm.calls) == 2


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
    client: TestClient, llm: FakeLLM, overrides: dict[str, Any]
) -> None:
    response = client.post("/api/chat", json=chat_body(**overrides))

    assert response.status_code == 422
    assert llm.calls == []


@pytest.mark.parametrize(
    ("finish_reason", "content", "status_code"),
    [
        pytest.param("content_filter", "", 422, id="content filter"),
        pytest.param("length", '{"reply": "Сәл', 502, id="cut off"),
        pytest.param("tool_calls", "", 502, id="unexpected stop"),
        pytest.param("stop", "not json", 502, id="invalid json"),
        pytest.param("stop", '{"reply": "no lists"}', 502, id="schema mismatch"),
    ],
)
def test_chat_reports_unusable_answer(
    client: TestClient, llm: FakeLLM, finish_reason: str, content: str, status_code: int
) -> None:
    llm.reply_with(content, finish_reason=finish_reason)

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text


def test_chat_reports_model_refusal(client: TestClient, llm: FakeLLM) -> None:
    llm.reply_with("", refusal="I can't help with that.")

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        pytest.param(
            openai.RateLimitError("slow down", response=api_response(429), body=None),
            503,
            id="rate limited",
        ),
        pytest.param(openai.APIConnectionError(request=api_request()), 503, id="no network"),
        pytest.param(openai.APITimeoutError(request=api_request()), 503, id="timeout"),
        pytest.param(
            openai.APIStatusError("Payment Required", response=api_response(402), body=None),
            503,
            id="balance is empty",
        ),
        pytest.param(
            openai.AuthenticationError("bad key", response=api_response(401), body=None),
            500,
            id="bad api key",
        ),
        pytest.param(
            openai.NotFoundError("model_not_found", response=api_response(404), body=None),
            500,
            id="unknown model",
        ),
        pytest.param(
            openai.InternalServerError("boom", response=api_response(500), body=None),
            502,
            id="provider outage",
        ),
    ],
)
def test_chat_maps_llm_api_errors(
    client: TestClient, llm: FakeLLM, error: Exception, status_code: int
) -> None:
    llm.fail_with(error)

    response = client.post("/api/chat", json=chat_body())

    assert response.status_code == status_code
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text
