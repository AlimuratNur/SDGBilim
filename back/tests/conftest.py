import json
from collections.abc import Iterator
from typing import Any, cast

import httpx2
import pytest
from fastapi.testclient import TestClient
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.config import Settings
from app.main import create_app

TEST_MODEL = "test-model"
FRONTEND_ORIGIN = "http://localhost:5173"


class FakeCompletions:
    """Stands in for `AsyncOpenAI().chat.completions`: records requests, returns canned outcomes.

    Outcomes are used in order; the last one repeats for any further request.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.outcomes: list[ChatCompletion | Exception] = []

    async def create(self, **kwargs: Any) -> ChatCompletion:
        self.calls.append(kwargs)
        assert self.outcomes, "test did not set a model reply"
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeChat:
    def __init__(self) -> None:
        self.completions = FakeCompletions()


class FakeLLM:
    def __init__(self) -> None:
        self.chat = FakeChat()

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self.chat.completions.calls

    @property
    def last_call(self) -> dict[str, Any]:
        assert self.calls, "the model was not called"
        return self.calls[-1]

    def reply_with(
        self,
        payload: dict[str, Any] | str,
        finish_reason: str = "stop",
        refusal: str | None = None,
    ) -> None:
        content = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        # `construct` skips validation, like the SDK does for real responses, which may carry
        # provider-specific values.
        completion = ChatCompletion.construct(
            id="chatcmpl-test",
            object="chat.completion",
            created=0,
            model=TEST_MODEL,
            choices=[
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "message": {"role": "assistant", "content": content, "refusal": refusal},
                }
            ],
        )
        self.chat.completions.outcomes.append(completion)

    def fail_with(self, error: Exception) -> None:
        self.chat.completions.outcomes.append(error)


def api_request() -> httpx2.Request:
    return httpx2.Request("POST", "https://api.meta.ai/v1/chat/completions")


def api_response(status_code: int) -> httpx2.Response:
    return httpx2.Response(status_code, request=api_request())


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def client(llm: FakeLLM) -> Iterator[TestClient]:
    settings = Settings(_env_file=None, llm_model=TEST_MODEL, cors_origins=[FRONTEND_ORIGIN])
    app = create_app(settings, llm_client=cast(AsyncOpenAI, llm))
    with TestClient(app) as test_client:
        yield test_client
