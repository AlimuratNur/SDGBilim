# BilimAI — backend

FastAPI server for the Kazakh-language AI tutor (SDG KBTU Hackathon, SDG 4).
It holds the Claude API key and answers the frontend in `front/`.

## Run

Needs [uv](https://docs.astral.sh/uv/) and an Anthropic API key.

```bash
cp .env.example .env    # then put your key into ANTHROPIC_API_KEY
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Then point the frontend at it in `front/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

Without a key the server stops at startup with a clear error. The frontend can still run
on its own in demo mode.

## Check

```bash
uv run pytest           # tests: Claude is replaced by a fake client, no key or network needed
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy app tests   # types (strict)
```

## Configuration

Read from environment variables or `back/.env` (git-ignored).

| Variable                  | Default                 | What it does                              |
| ------------------------- | ----------------------- | ----------------------------------------- |
| `ANTHROPIC_API_KEY`       | —                       | Claude API key. Required.                 |
| `CLAUDE_MODEL`            | `claude-haiku-5-5`      | Model for the tutor and the translator.   |
| `CORS_ORIGINS`            | `http://localhost:5173` | Comma-separated frontend origins.         |
| `REQUEST_TIMEOUT_SECONDS` | `60`                    | Timeout for one Claude request.           |

## API

The contract with request/response examples is in [`front/README.md`](../front/README.md#api-contract-for-the-backend);
the types are in [`front/src/api/types.ts`](../front/src/api/types.ts) and mirrored in
[`app/schemas.py`](app/schemas.py). Keep them in sync.

| Endpoint              | Request             | Response              |
| --------------------- | ------------------- | --------------------- |
| `POST /api/chat`      | `ChatRequest`       | `ChatResponse`        |
| `POST /api/translate` | `TranslateRequest`  | `TranslateResponse`   |
| `GET /api/health`     | —                   | `{"status": "ok"}`    |

Errors:

| Status | When                                                                 | Body                   |
| ------ | -------------------------------------------------------------------- | ---------------------- |
| 422    | Invalid request, or Claude declined it                               | JSON details / text    |
| 500    | The API key is wrong                                                 | text for the student   |
| 502    | Claude returned an error, a cut-off or a broken answer               | text for the student   |
| 503    | Rate limit, timeout or no network to Claude                          | text for the student   |

The frontend shows the body of an error response to the student, so tutor errors are plain text.

## How it works

```
app/
  main.py      FastAPI app: routes, CORS, error handler, Anthropic client
  schemas.py   HTTP contract (mirror of front/src/api/types.ts)
  tutor.py     Claude calls: chat and translate, error mapping
  prompts.py   System prompts, levels and topics
  config.py    Settings from env / .env
tests/         API tests with a fake Anthropic client
```

- Claude answers with [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs):
  a JSON schema built from Pydantic models, so `corrections` and `newWords` come back as fields.
  `stop_reason` is checked before the JSON is parsed: a refusal or a cut-off answer becomes a clear error.
- Chat sends only the last 30 messages of the dialogue to Claude, so long lessons stay fast and cheap.
- Effort: `medium` for the tutor (grammar corrections need care), `low` for the translator.
- The text to translate is wrapped in `<text>` tags, and the prompt tells Claude never to follow
  instructions inside it.
