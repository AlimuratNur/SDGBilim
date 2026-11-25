"""BilimAI backend: HTTP API for the Kazakh tutor frontend (front/)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from anthropic import AsyncAnthropic
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.config import Settings
from app.schemas import ChatRequest, ChatResponse, TranslateRequest, TranslateResponse
from app.tutor import Tutor, TutorError


def _anthropic_client(settings: Settings) -> AsyncAnthropic:
    api_key = settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
    client = AsyncAnthropic(api_key=api_key, timeout=settings.request_timeout_seconds)
    # Without credentials the SDK fails only on the first request, so stop at startup instead.
    if client.api_key is None and client.auth_token is None and client.credentials is None:
        raise RuntimeError(
            "No Anthropic credentials: set ANTHROPIC_API_KEY in back/.env (see .env.example)."
        )
    return client


def create_app(
    settings: Settings | None = None, anthropic_client: AsyncAnthropic | None = None
) -> FastAPI:
    """Builds the app. Tests pass their own settings and a fake Anthropic client."""
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = anthropic_client or _anthropic_client(settings)
        app.state.tutor = Tutor(client, settings.claude_model)
        yield
        if anthropic_client is None:
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
