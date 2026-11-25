"""Talks to DeepSeek: the tutor chat and the translator."""

import logging
from collections.abc import Sequence

import openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError

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

# Only the recent part of the dialogue goes to the model: enough context for a lesson,
# while long sessions stay fast and cheap.
MAX_HISTORY_MESSAGES = 30
# Answers are short JSON objects; the cap only guards against runaway output.
MAX_OUTPUT_TOKENS = 4096
# DeepSeek's recommended temperature for conversation and translation.
TEMPERATURE = 1.3
# DeepSeek JSON mode sometimes returns blank content; its docs say to retry.
ATTEMPTS_ON_BLANK_CONTENT = 2


class TutorError(Exception):
    """A failure the frontend should show to the student as is."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# What the model must return. DeepSeek JSON mode does not enforce a schema, so every answer
# is validated against these models; empty strings and lists mean "nothing to add".
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
    transliteration: str
    notes: str


def recent_dialogue(messages: Sequence[ChatMessage]) -> list[ChatCompletionMessageParam]:
    """The last MAX_HISTORY_MESSAGES messages, trimmed so the dialogue starts with the student."""
    recent = list(messages[-MAX_HISTORY_MESSAGES:])
    while recent and recent[0].role != "user":
        recent.pop(0)
    return [_to_message_param(message) for message in recent]


def _to_message_param(message: ChatMessage) -> ChatCompletionMessageParam:
    if message.role == "user":
        return {"role": "user", "content": message.content}
    return {"role": "assistant", "content": message.content}


class Tutor:
    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        answer = await self._ask(
            system=chat_system_prompt(request.level, request.topic),
            messages=recent_dialogue(request.messages),
            output=_ChatDraft,
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
        messages: list[ChatCompletionMessageParam],
        output: type[Answer],
    ) -> Answer:
        """Sends the request and returns the model's answer validated against `output`."""
        conversation: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system},
            *messages,
        ]
        for _ in range(ATTEMPTS_ON_BLANK_CONTENT):
            content = await self._complete(conversation)
            if content.strip():
                break
            logger.warning("DeepSeek returned blank content")
        else:
            raise TutorError(502, "The tutor sent an empty answer. Try again.")

        try:
            return output.model_validate_json(content)
        except ValidationError as error:
            logger.error("DeepSeek answer does not match the expected JSON: %s", error)
            raise TutorError(502, "The tutor sent a broken answer. Try again.") from error

    async def _complete(self, conversation: list[ChatCompletionMessageParam]) -> str:
        """Returns the text of one complete answer, or raises TutorError."""
        completion = await self._create(conversation)
        if not completion.choices:
            logger.error("DeepSeek returned no choices on %s", completion.id)
            raise TutorError(502, "The tutor sent an empty answer. Try again.")
        choice = completion.choices[0]
        # DeepSeek adds finish reasons the OpenAI types do not list, so compare plain strings.
        finish_reason: str = choice.finish_reason

        if finish_reason == "content_filter":
            logger.warning("DeepSeek filtered the answer to %s", completion.id)
            raise TutorError(422, "The tutor can't help with this request. Try rephrasing it.")
        if finish_reason == "insufficient_system_resource":
            raise TutorError(503, "The tutor is busy right now. Try again in a minute.")
        if finish_reason != "stop":
            logger.error("DeepSeek stopped early (%s) on %s", finish_reason, completion.id)
            raise TutorError(502, "The answer was cut off. Try a shorter message.")
        return choice.message.content or ""

    async def _create(self, conversation: list[ChatCompletionMessageParam]) -> ChatCompletion:
        try:
            return await self._client.chat.completions.create(
                model=self._model,
                messages=conversation,
                response_format={"type": "json_object"},
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=TEMPERATURE,
                # Non-thinking mode: answers come back in a few seconds.
                extra_body={"thinking": {"type": "disabled"}},
            )
        except (openai.RateLimitError, openai.APIConnectionError) as error:
            logger.warning("DeepSeek unavailable: %r", error)
            raise TutorError(503, "The tutor is busy right now. Try again in a minute.") from error
        except (openai.AuthenticationError, openai.PermissionDeniedError) as error:
            logger.error("DeepSeek rejected the backend API key: %r", error)
            raise TutorError(
                500, "The backend is misconfigured: check DEEPSEEK_API_KEY."
            ) from error
        except openai.APIStatusError as error:
            if error.status_code == 402:
                logger.error("DeepSeek balance is empty: top up the account")
                raise TutorError(
                    503, "The tutor is unavailable: the AI service balance is empty."
                ) from error
            logger.error("DeepSeek API error %s: %r", error.status_code, error)
            raise TutorError(502, "The AI service returned an error. Try again.") from error
