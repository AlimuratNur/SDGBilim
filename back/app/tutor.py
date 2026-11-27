"""The tutor chat and the translator: prompts, dialogue history and the answers' shape."""

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict

from app.llm import StructuredLLM, Turn
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

# Only the recent part of the dialogue goes to the model: enough context for a lesson,
# while long sessions stay fast and cheap.
MAX_HISTORY_MESSAGES = 30


# What the model must return. The request sends these as a JSON schema (no extra keys, every
# key required); answers are validated against them too. Empty strings and lists mean
# "nothing to add".
class _Draft(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _DraftCorrection(_Draft):
    original: str
    corrected: str
    explanation: str


class _DraftWord(_Draft):
    kk: str
    en: str
    ru: str


class _ChatDraft(_Draft):
    reply: str
    corrections: list[_DraftCorrection]
    new_words: list[_DraftWord]


class _TranslationDraft(_Draft):
    translation: str
    transliteration: str
    notes: str


def recent_dialogue(messages: Sequence[ChatMessage]) -> list[Turn]:
    """The last MAX_HISTORY_MESSAGES messages, trimmed so the dialogue starts with the student."""
    recent = list(messages[-MAX_HISTORY_MESSAGES:])
    while recent and recent[0].role != "user":
        recent.pop(0)
    return [Turn(m.role, m.content) for m in recent]


class Tutor:
    def __init__(self, llm: StructuredLLM) -> None:
        self._llm = llm

    async def chat(self, request: ChatRequest) -> ChatResponse:
        answer = await self._llm.answer(
            system=chat_system_prompt(request.level, request.topic),
            turns=recent_dialogue(request.messages),
            output=_ChatDraft,
        )
        return ChatResponse(
            reply=answer.reply,
            corrections=[Correction(**c.model_dump()) for c in answer.corrections],
            new_words=[NewWord(kk=w.kk, en=w.en, ru=w.ru or None) for w in answer.new_words],
        )

    async def translate(self, request: TranslateRequest) -> TranslateResponse:
        prompt = translate_user_message(request.text, request.source, request.target)
        answer = await self._llm.answer(
            system=TRANSLATE_SYSTEM,
            turns=[Turn("user", prompt)],
            output=_TranslationDraft,
        )
        return TranslateResponse(
            translation=answer.translation,
            transliteration=answer.transliteration or None,
            notes=answer.notes or None,
        )
