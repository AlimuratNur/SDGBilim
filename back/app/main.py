"""BilimAI backend: HTTP API for the Kazakh tutor frontend (front/)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config import Settings
from app.errors import TutorError
from app.llm import StructuredLLM, build_llm
from app.schemas import ChatRequest, ChatResponse, TranslateRequest, TranslateResponse
from app.tutor import Tutor


def create_app(settings: Settings | None = None, llm: StructuredLLM | None = None) -> FastAPI:
    """Builds the app. Tests pass their own settings and an LLM client over a fake SDK."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = llm or build_llm(settings)
        app.state.tutor = Tutor(client)
        yield
        if llm is None:
            await client.close()

    app = FastAPI(title="BilimAI backend", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(TutorError)
    async def tutor_error_handler(_: Request, error: TutorError) -> PlainTextResponse:
        # The frontend shows the response body to the student, so it is plain text.
        return PlainTextResponse(error.message, status_code=error.status_code)

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/chat", response_model_exclude_none=True)
    async def chat(body: ChatRequest, request: Request) -> ChatResponse:
        tutor: Tutor = request.app.state.tutor
        return await tutor.chat(body)

    @app.post("/api/translate", response_model_exclude_none=True)
    async def translate(body: TranslateRequest, request: Request) -> TranslateResponse:
        tutor: Tutor = request.app.state.tutor
        return await tutor.translate(body)

    return app


app = create_app()
