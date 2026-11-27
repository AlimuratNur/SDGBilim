import json
from collections.abc import Iterator
from typing import Any, cast

import httpx2
import pytest
from anthropic import AsyncAnthropic
from anthropic.types import Message
from fastapi.testclient import TestClient
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.config import Settings
from app.llm import AnthropicLLM, OpenAICompatibleLLM, StructuredLLM
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


class FakeOpenAI:
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


class FakeAnthropicMessages:
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
        self.messages = FakeAnthropicMessages()

    @property
    def last_call(self) -> dict[str, Any]:
        assert self.messages.calls, "Claude was not called"
        return self.messages.calls[-1]

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


def api_request() -> httpx2.Request:
    return httpx2.Request("POST", "https://api.meta.ai/v1/chat/completions")


def api_response(status_code: int) -> httpx2.Response:
    return httpx2.Response(status_code, request=api_request())


@pytest.fixture
def llm() -> FakeOpenAI:
    return FakeOpenAI()


def _test_client(llm: StructuredLLM) -> Iterator[TestClient]:
    settings = Settings(_env_file=None, cors_origins=[FRONTEND_ORIGIN])
    with TestClient(create_app(settings, llm=llm)) as test_client:
        yield test_client


@pytest.fixture
def client(llm: FakeOpenAI) -> Iterator[TestClient]:
    """The app on an OpenAI-compatible provider."""
    yield from _test_client(OpenAICompatibleLLM(cast(AsyncOpenAI, llm), TEST_MODEL))


@pytest.fixture
def claude() -> FakeClaude:
    return FakeClaude()


@pytest.fixture
def claude_client(claude: FakeClaude) -> Iterator[TestClient]:
    """The app on Claude."""
    yield from _test_client(AnthropicLLM(cast(AsyncAnthropic, claude), TEST_MODEL))
