"""BilimAI backend: HTTP API for the Kazakh tutor frontend (front/)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from openai import AsyncOpenAI

from app.config import Settings
from app.schemas import ChatRequest, ChatResponse, TranslateRequest, TranslateResponse
from app.tutor import Tutor, TutorError


def _llm_client(settings: Settings) -> AsyncOpenAI:
    # The key is always passed explicitly: the OpenAI SDK would otherwise fall back to
    # OPENAI_API_KEY and send it to another provider.
    if settings.llm_api_key is None:
        raise RuntimeError("No LLM API key: set LLM_API_KEY in back/.env (see .env.example).")
    return AsyncOpenAI(
        api_key=settings.llm_api_key.get_secret_value(),
        base_url=settings.llm_base_url,
        timeout=settings.request_timeout_seconds,
    )


def create_app(settings: Settings | None = None, llm_client: AsyncOpenAI | None = None) -> FastAPI:
    """Builds the app. Tests pass their own settings and a fake LLM client."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = llm_client or _llm_client(settings)
        app.state.tutor = Tutor(client, settings.llm_model)
        yield
        if llm_client is None:
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
