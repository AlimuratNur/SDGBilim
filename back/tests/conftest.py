import json
from collections.abc import Iterator
from typing import Any, cast

import httpx2
import pytest
from anthropic import AsyncAnthropic
from anthropic.types import Message
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

TEST_MODEL = "test-model"
FRONTEND_ORIGIN = "http://localhost:5173"


class FakeMessages:
    """Stands in for `AsyncAnthropic().messages`: records requests, returns a canned outcome."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.outcome: Message | Exception | None = None

    async def create(self, **kwargs: Any) -> Message:
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        assert self.outcome is not None, "test did not set a Claude reply"
        return self.outcome


class FakeClaude:
    def __init__(self) -> None:
        self.messages = FakeMessages()

    def reply_with(self, payload: dict[str, Any] | str, stop_reason: str = "end_turn") -> None:
        text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        self.messages.outcome = Message.model_validate(
            {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": TEST_MODEL,
                # Adaptive thinking puts a thinking block before the answer.
                "content": [
                    {"type": "thinking", "thinking": "", "signature": "sig"},
                    {"type": "text", "text": text},
                ],
                "stop_reason": stop_reason,
                "usage": {"input_tokens": 10, "output_tokens": 10},
            }
        )

    def fail_with(self, error: Exception) -> None:
        self.messages.outcome = error

    @property
    def last_call(self) -> dict[str, Any]:
        assert self.messages.calls, "Claude was not called"
        return self.messages.calls[-1]


def api_request() -> httpx2.Request:
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def api_response(status_code: int) -> httpx2.Response:
    return httpx2.Response(status_code, request=api_request())


@pytest.fixture
def claude() -> FakeClaude:
    return FakeClaude()


@pytest.fixture
def client(claude: FakeClaude) -> Iterator[TestClient]:
    settings = Settings(_env_file=None, claude_model=TEST_MODEL, cors_origins=[FRONTEND_ORIGIN])
    app = create_app(settings, anthropic_client=cast(AsyncAnthropic, claude))
    with TestClient(app) as test_client:
        yield test_client
