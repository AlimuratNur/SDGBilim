"""Language model clients.

Each client sends a system prompt and a dialogue, asks for an answer that follows the JSON
schema of a Pydantic model, and returns that answer validated, or raises TutorError with a
message for the student. LLM_PROVIDER picks the client (see app/config.py).
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from typing import Protocol

import anthropic
import openai
from anthropic import AsyncAnthropic, transform_schema
from anthropic.types import JSONOutputFormatParam, Message, MessageParam
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from openai.types.shared_params import ResponseFormatJSONSchema
from pydantic import BaseModel, ValidationError

from app.config import Settings
from app.errors import TutorError
from app.schemas import Role

logger = logging.getLogger(__name__)

BUSY = "The tutor is busy right now. Try again in a minute."
DECLINED = "The tutor can't help with this request. Try rephrasing it."
CUT_OFF = "The answer was cut off. Try a shorter message."
EMPTY = "The tutor sent an empty answer. Try again."
BROKEN = "The tutor sent a broken answer. Try again."
BAD_KEY = "The backend is misconfigured: check LLM_API_KEY."
BAD_MODEL = "The backend is misconfigured: check LLM_MODEL."
NO_BALANCE = "The tutor is unavailable: the AI service balance is empty."
PROVIDER_ERROR = "The AI service returned an error. Try again."

# "Overloaded": 503 on OpenAI-compatible APIs (Gemini, Meta...), 529 on Anthropic.
OVERLOADED_STATUSES = frozenset({503, 529})


@dataclass(frozen=True)
class Turn:
    role: Role
    content: str


class StructuredLLM(Protocol):
    async def answer[Answer: BaseModel](
        self, *, system: str, turns: Sequence[Turn], output: type[Answer]
    ) -> Answer: ...

    async def close(self) -> None: ...


def build_llm(settings: Settings) -> StructuredLLM:
    """The client for LLM_PROVIDER. Fails at startup, not on the first request, without a key."""
    # The key is always passed explicitly: the SDKs would otherwise fall back to
    # OPENAI_API_KEY / ANTHROPIC_API_KEY and could send one provider's key to another.
    if settings.llm_api_key is None:
        raise RuntimeError("No LLM API key: set LLM_API_KEY in back/.env (see .env.example).")
    key = settings.llm_api_key.get_secret_value()
    timeout = settings.request_timeout_seconds
    if settings.llm_provider == "anthropic":
        claude = AsyncAnthropic(api_key=key, base_url=settings.base_url, timeout=timeout)
        return AnthropicLLM(claude, settings.model)
    compatible = AsyncOpenAI(api_key=key, base_url=settings.base_url, timeout=timeout)
    return OpenAICompatibleLLM(compatible, settings.model)


def _validated[Answer: BaseModel](output: type[Answer], text: str) -> Answer:
    try:
        return output.model_validate_json(text)
    except ValidationError as error:
        logger.error("The model's answer does not match the JSON schema: %s", error)
        raise TutorError(502, BROKEN) from error


# ---------------------------------------------------------------------------------------------
# Claude (Anthropic SDK)
# ---------------------------------------------------------------------------------------------


@cache
def _anthropic_format(output: type[BaseModel]) -> JSONOutputFormatParam:
    return {"type": "json_schema", "schema": transform_schema(output)}


def _anthropic_message(turn: Turn) -> MessageParam:
    if turn.role == "user":
        return {"role": "user", "content": turn.content}
    return {"role": "assistant", "content": turn.content}


class AnthropicLLM:
    # Room for adaptive thinking plus the JSON answer.
    MAX_OUTPUT_TOKENS = 16000

    def __init__(self, client: AsyncAnthropic, model: str) -> None:
        self._client = client
        self._model = model

    async def answer[Answer: BaseModel](
        self, *, system: str, turns: Sequence[Turn], output: type[Answer]
    ) -> Answer:
        response = await self._create(
            system, [_anthropic_message(t) for t in turns], _anthropic_format(output)
        )
        if response.stop_reason == "refusal":
            logger.warning("Claude declined %s: %s", response.id, response.stop_details)
            raise TutorError(422, DECLINED)
        if response.stop_reason != "end_turn":
            logger.error("Claude stopped early (%s) on %s", response.stop_reason, response.id)
            raise TutorError(502, CUT_OFF)
        # With adaptive thinking the answer is not the first block: pick it by type.
        text = next((block.text for block in response.content if block.type == "text"), "")
        return _validated(output, text)

    async def close(self) -> None:
        await self._client.close()

    async def _create(
        self, system: str, messages: list[MessageParam], output_format: JSONOutputFormatParam
    ) -> Message:
        try:
            return await self._client.messages.create(
                model=self._model,
                max_tokens=self.MAX_OUTPUT_TOKENS,
                system=system,
                messages=messages,
                output_config={"format": output_format},
            )
        except (anthropic.RateLimitError, anthropic.APIConnectionError) as error:
            logger.warning("Claude unavailable: %r", error)
            raise TutorError(503, BUSY) from error
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as error:
            logger.error("Claude rejected the backend API key: %r", error)
            raise TutorError(500, BAD_KEY) from error
        except anthropic.NotFoundError as error:
            logger.error("Claude does not know model %s: %r", self._model, error)
            raise TutorError(500, BAD_MODEL) from error
        except anthropic.APIStatusError as error:
            if error.status_code in OVERLOADED_STATUSES:
                logger.warning("Claude is overloaded: %r", error)
                raise TutorError(503, BUSY) from error
            logger.error("Claude API error %s: %r", error.status_code, error)
            raise TutorError(502, PROVIDER_ERROR) from error


# ---------------------------------------------------------------------------------------------
# Any OpenAI-compatible chat API (OpenAI SDK)
# ---------------------------------------------------------------------------------------------


@cache
def _openai_format(output: type[BaseModel]) -> ResponseFormatJSONSchema:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": output.__name__.strip("_"),
            "schema": output.model_json_schema(),
            "strict": True,
        },
    }


def _openai_message(turn: Turn) -> ChatCompletionMessageParam:
    if turn.role == "user":
        return {"role": "user", "content": turn.content}
    return {"role": "assistant", "content": turn.content}


class OpenAICompatibleLLM:
    # Answers are short JSON objects; the cap only guards against runaway output.
    MAX_OUTPUT_TOKENS = 4096
    # Some providers occasionally return blank content for a JSON answer.
    ATTEMPTS_ON_BLANK_CONTENT = 2

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def answer[Answer: BaseModel](
        self, *, system: str, turns: Sequence[Turn], output: type[Answer]
    ) -> Answer:
        conversation: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system},
            *(_openai_message(t) for t in turns),
        ]
        for _ in range(self.ATTEMPTS_ON_BLANK_CONTENT):
            content = await self._complete(conversation, _openai_format(output))
            if content.strip():
                return _validated(output, content)
            logger.warning("The model returned blank content")
        raise TutorError(502, EMPTY)

    async def close(self) -> None:
        await self._client.close()

    async def _complete(
        self,
        conversation: list[ChatCompletionMessageParam],
        response_format: ResponseFormatJSONSchema,
    ) -> str:
        """Returns the text of one complete answer, or raises TutorError."""
        completion = await self._create(conversation, response_format)
        if not completion.choices:
            logger.error("The model returned no choices on %s", completion.id)
            raise TutorError(502, EMPTY)
        choice = completion.choices[0]
        # Providers may add finish reasons the OpenAI types do not list, so compare plain strings.
        finish_reason: str = choice.finish_reason

        if choice.message.refusal or finish_reason == "content_filter":
            logger.warning("The model declined %s: %s", completion.id, choice.message.refusal)
            raise TutorError(422, DECLINED)
        if finish_reason != "stop":
            logger.error("The model stopped early (%s) on %s", finish_reason, completion.id)
            raise TutorError(502, CUT_OFF)
        return choice.message.content or ""

    async def _create(
        self,
        conversation: list[ChatCompletionMessageParam],
        response_format: ResponseFormatJSONSchema,
    ) -> ChatCompletion:
        try:
            return await self._client.chat.completions.create(
                model=self._model,
                messages=conversation,
                response_format=response_format,
                max_tokens=self.MAX_OUTPUT_TOKENS,
            )
        except (openai.RateLimitError, openai.APIConnectionError) as error:
            logger.warning("The LLM API is unavailable: %r", error)
            raise TutorError(503, BUSY) from error
        except (openai.AuthenticationError, openai.PermissionDeniedError) as error:
            logger.error("The LLM API rejected the backend API key: %r", error)
            raise TutorError(500, BAD_KEY) from error
        except openai.NotFoundError as error:
            logger.error("The LLM API does not know model %s: %r", self._model, error)
            raise TutorError(500, BAD_MODEL) from error
        except openai.APIStatusError as error:
            if error.status_code == 402:
                logger.error("The LLM account balance is empty: top it up")
                raise TutorError(503, NO_BALANCE) from error
            if error.status_code in OVERLOADED_STATUSES:
                logger.warning("The LLM API is overloaded: %r", error)
                raise TutorError(503, BUSY) from error
            logger.error("LLM API error %s: %r", error.status_code, error)
            raise TutorError(502, PROVIDER_ERROR) from error
