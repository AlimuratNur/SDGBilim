"""HTTP contract with the frontend. Mirrors front/src/api/types.ts: keep the two in sync."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Role = Literal["user", "assistant"]
Level = Literal["beginner", "intermediate", "advanced"]
Lang = Literal["kk", "en", "ru"]

MAX_MESSAGE_CHARS = 2000
# Abuse guard only: the tutor itself sends just the recent part of the dialogue to the model.
MAX_REQUEST_MESSAGES = 200
MAX_TRANSLATE_CHARS = 2000


class _Request(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ChatMessage(_Request):
    role: Role
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class Correction(BaseModel):
    original: str
    corrected: str
    explanation: str


class NewWord(BaseModel):
    kk: str
    en: str
    ru: str | None = None


class ChatRequest(_Request):
    """POST /api/chat"""

    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_REQUEST_MESSAGES)
    level: Level
    topic: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _last_message_is_from_user(self) -> Self:
        if self.messages[-1].role != "user":
            raise ValueError("the last message must be from the user")
        return self


class ChatResponse(BaseModel):
    reply: str
    corrections: list[Correction] = []
    new_words: list[NewWord] = Field(default=[], serialization_alias="newWords")


class TranslateRequest(_Request):
    """POST /api/translate"""

    text: str = Field(min_length=1, max_length=MAX_TRANSLATE_CHARS)
    source: Lang = Field(alias="from")
    target: Lang = Field(alias="to")

    @model_validator(mode="after")
    def _languages_differ(self) -> Self:
        if self.source == self.target:
            raise ValueError("'from' and 'to' must be different languages")
        return self


class TranslateResponse(BaseModel):
    translation: str
    transliteration: str | None = None
    notes: str | None = None
