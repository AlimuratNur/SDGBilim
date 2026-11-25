"""Talks to Claude: the tutor chat and the translator."""

import logging
from collections.abc import Sequence
from functools import cache
from typing import Literal

import anthropic
from anthropic import AsyncAnthropic, transform_schema
from anthropic.types import JSONOutputFormatParam, Message, MessageParam
from pydantic import BaseModel, Field, ValidationError

from app.prompts import TRANSLATE_SYSTEM, chat_system_prompt, translate_user_message
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Correction,
    NewWord,
    TranslateRequest,
    TranslateResponse,
)

logger = logging.getLogger(__name__)

# Only the recent part of the dialogue goes to Claude: enough context for a lesson,
# while long sessions stay fast and cheap.
MAX_HISTORY_MESSAGES = 30
# Room for adaptive thinking plus the JSON answer.
MAX_OUTPUT_TOKENS = 16000

Effort = Literal["low", "medium", "high"]


class TutorError(Exception):
    """A failure the frontend should show to the student as is."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# What Claude must return. Every field is required so the structured output is fully
# specified; empty strings and lists mean "nothing to add".
class _DraftWord(BaseModel):
    kk: str
    en: str
    ru: str


class _ChatDraft(BaseModel):
    reply: str
    corrections: list[Correction]
    new_words: list[_DraftWord]


class _TranslationDraft(BaseModel):
    translation: str
    transliteration: str = Field(description="Empty string unless the target is Kazakh.")
    notes: str = Field(description="Empty string when there is nothing useful to add.")


@cache
def _json_format(model: type[BaseModel]) -> JSONOutputFormatParam:
    return {"type": "json_schema", "schema": transform_schema(model)}


def recent_dialogue(messages: Sequence[ChatMessage]) -> list[MessageParam]:
    """The last MAX_HISTORY_MESSAGES messages, trimmed so the dialogue starts with the student."""
    recent = list(messages[-MAX_HISTORY_MESSAGES:])
    while recent and recent[0].role != "user":
        recent.pop(0)
    return [_to_message_param(message) for message in recent]


def _to_message_param(message: ChatMessage) -> MessageParam:
    if message.role == "user":
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}


class Tutor:
    def __init__(self, client: AsyncAnthropic, model: str) -> None:
        self._client = client
        self._model = model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        answer = await self._ask(
            system=chat_system_prompt(request.level, request.topic),
            messages=recent_dialogue(request.messages),
            output=_ChatDraft,
            effort="medium",
        )
        return ChatResponse(
            reply=answer.reply,
            corrections=answer.corrections,
            new_words=[NewWord(kk=w.kk, en=w.en, ru=w.ru or None) for w in answer.new_words],
        )

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        prompt = translate_user_message(request.text, request.source, request.target)
        answer = await self._ask(
            system=TRANSLATE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output=_TranslationDraft,
            effort="low",
        )
        return TranslateResponse(
            translation=answer.translation,
            transliteration=answer.transliteration or None,
            notes=answer.notes or None,
        )

    async def _ask[Answer: BaseModel](
        self,
        *,
        system: str,
        messages: list[MessageParam],
        output: type[Answer],
        effort: Effort,
    ) -> Answer:
        """Sends one request and returns Claude's answer validated against `output`."""
        response = await self._create(
            system=system, messages=messages, output_format=_json_format(output), effort=effort
        )

        if response.stop_reason == "refusal":
            logger.warning("Claude declined request %s: %s", response.id, response.stop_details)
            raise TutorError(422, "The tutor can't help with this request. Try rephrasing it.")
        if response.stop_reason != "end_turn":
            logger.error("Claude stopped early (%s) on %s", response.stop_reason, response.id)
            raise TutorError(502, "The answer was cut off. Try a shorter message.")

        # With adaptive thinking the answer is not the first block: pick it by type.
        text = next((block.text for block in response.content if block.type == "text"), "")
        try:
            return output.model_validate_json(text)
        except ValidationError as error:
            logger.error("Claude answer %s does not match the schema: %s", response.id, error)
            raise TutorError(502, "The tutor sent a broken answer. Try again.") from error

    async def _create(
        self,
        *,
        system: str,
        messages: list[MessageParam],
        output_format: JSONOutputFormatParam,
        effort: Effort,
    ) -> Message:
        try:
            return await self._client.messages.create(
                model=self._model,
                max_tokens=MAX_OUTPUT_TOKENS,
                system=system,
                messages=messages,
                output_config={"effort": effort, "format": output_format},
            )
        except (anthropic.RateLimitError, anthropic.APIConnectionError) as error:
            logger.warning("Claude unavailable: %r", error)
            raise TutorError(503, "The tutor is busy right now. Try again in a minute.") from error
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as error:
            logger.error("Claude rejected the backend credentials: %r", error)
            raise TutorError(
                500, "The backend is misconfigured: check ANTHROPIC_API_KEY."
            ) from error
        except anthropic.APIStatusError as error:
            logger.error("Claude API error %s: %r", error.status_code, error)
            raise TutorError(502, "The AI service returned an error. Try again.") from error
