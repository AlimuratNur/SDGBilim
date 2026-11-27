# BilimAI — backend

FastAPI server for the Kazakh-language AI tutor (SDG KBTU Hackathon, SDG 4).
It holds the LLM API key and answers the frontend in `front/`. The model is Claude or any
OpenAI-compatible API (Meta Model API by default), picked by `LLM_PROVIDER`.

## Run

Needs [uv](https://docs.astral.sh/uv/) and an API key: [Claude](https://platform.claude.com/settings/keys)
or an OpenAI-compatible provider such as the [Meta Model API](https://dev.meta.ai/).

```bash
cp .env.example .env    # then put your key into LLM_API_KEY
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
uv run pytest           # tests: the LLM is replaced by a fake client, no key or network needed
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy app tests   # types (strict)
```

## Configuration

Read from environment variables or `back/.env` (git-ignored).

| Variable                  | Default                 | What it does                              |
| ------------------------- | ----------------------- | ----------------------------------------- |
| `LLM_PROVIDER`            | `openai`                | `anthropic` (Claude) or `openai` (any OpenAI-compatible API). |
| `LLM_API_KEY`             | —                       | Key of that provider. Required.           |
| `LLM_MODEL`               | per provider            | `claude-haiku-5-5` / `muse-spark-1.3`.    |
| `LLM_BASE_URL`            | per provider            | Anthropic's endpoint / `https://api.meta.ai/v1`. |
| `CORS_ORIGINS`            | `http://localhost:5173` | Comma-separated frontend origins.         |
| `REQUEST_TIMEOUT_SECONDS` | `60`                    | Timeout for one model request.            |

## Deploy (Vercel)

Two Vercel projects in the `dorhsis-projects` scope, one per folder:

| Folder   | Vercel project | Production URL                      | Env vars (Production)                    |
| -------- | -------------- | ----------------------------------- | ---------------------------------------- |
| `back/`  | `sdgbilim-api` | https://sdgbilim-api.vercel.app     | `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `CORS_ORIGINS` |
| `front/` | `sdgbilim`     | https://sdgbilim.vercel.app         | `VITE_API_URL=https://sdgbilim-api.vercel.app` |

Production currently runs on **Gemini** through its OpenAI-compatible API (`LLM_PROVIDER`
unset, so `openai`; `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`;
`LLM_MODEL=gemini-3.5-flash-lite`) with a free AI Studio key. `gemini-3.8-flash` answered 503
(overloaded) on the free tier, so the Flash-Lite model is used.

`vercel.json` in each folder pins the framework (`fastapi`, `vite`); `front/vercel.json` also
sends every path to `index.html` so links like `/tutor` work. `.vercelignore` keeps `.env` files
and tests out of the upload.

### Automatic deploys

Every push to `main` runs a GitHub Actions workflow for the folder that changed:
[`deploy-back.yml`](../.github/workflows/deploy-back.yml) for `back/`,
[`deploy-front.yml`](../.github/workflows/deploy-front.yml) for `front/`. Each one runs the
lint, type checks, tests and build, and deploys to Vercel production only if they pass. Both can also be
started by hand from the Actions tab (Run workflow).

One-time setup (the Vercel GitHub app cannot be used: the Vercel account and the repository
belong to different GitHub users):

1. The owner of the Vercel account creates a token at
   [vercel.com/account/settings/tokens](https://vercel.com/account/settings/tokens),
   scope `dorhsis' projects`.
2. The repository owner adds it on GitHub: Settings → Secrets and variables → Actions →
   New repository secret, name `VERCEL_TOKEN`.

Until the secret exists, the workflows still run the checks and skip the deploy with a warning.

### Manual deploys

```bash
cd back && npx vercel@latest deploy --prod
cd front && npx vercel@latest deploy --prod
```

### Secrets

The API key is set once in Vercel, never committed:

```bash
cd back && npx vercel@latest env add LLM_API_KEY production
```

Env var changes apply on the next deploy. If the frontend moves to another domain, update
`CORS_ORIGINS` in `sdgbilim-api`.

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
| 422    | Invalid request, or the model declined to answer                    | JSON details / text    |
| 500    | The API key or the model name is wrong                               | text for the student   |
| 502    | The model returned an error, a cut-off, empty or broken answer       | text for the student   |
| 503    | Rate limit, provider overloaded, timeout, no network, empty balance | text for the student   |

The frontend shows the body of an error response to the student, so tutor errors are plain text.

## How it works

```
app/
  main.py      FastAPI app: routes, CORS, error handler
  schemas.py   HTTP contract (mirror of front/src/api/types.ts)
  tutor.py     Chat and translate: prompts, history, answer shape
  llm.py       LLM clients (Claude, OpenAI-compatible): JSON schema, stop reasons, errors
  prompts.py   System prompts, levels and topics
  config.py    Settings from env / .env
tests/         API tests with fake Anthropic and OpenAI SDKs
```

- `LLM_PROVIDER=anthropic` calls Claude through the Anthropic SDK with
  [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs);
  `stop_reason` is checked before the JSON is read. `LLM_PROVIDER=openai` calls any
  OpenAI-compatible API through the OpenAI SDK with a strict `json_schema` response format;
  `finish_reason` and `refusal` are checked first, and blank content is retried once.
- Both send the JSON schema of the answer's Pydantic model and validate the answer against it.
  A declined, cut-off or broken answer becomes a clear error for the student.
- Switching provider is configuration only: set `LLM_PROVIDER` and `LLM_API_KEY` (and, if
  needed, `LLM_MODEL` / `LLM_BASE_URL`) in Vercel and redeploy.
- Chat sends only the last 30 messages of the dialogue, so long lessons stay fast and cheap.
- The key is always passed explicitly, so `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` from the
  environment are never read or sent to another provider.
- The text to translate is wrapped in `<text>` tags, and the prompt tells the model never to
  follow instructions inside it.
