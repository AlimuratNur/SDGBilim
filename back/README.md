# BilimAI — backend

FastAPI server for the Kazakh-language AI tutor (SDG KBTU Hackathon, SDG 4).
It holds the DeepSeek API key and answers the frontend in `front/`.

## Run

Needs [uv](https://docs.astral.sh/uv/) and a [DeepSeek API key](https://platform.deepseek.com/api_keys).

```bash
cp .env.example .env    # then put your key into DEEPSEEK_API_KEY
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
uv run pytest           # tests: DeepSeek is replaced by a fake client, no key or network needed
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy app tests   # types (strict)
```

## Configuration

Read from environment variables or `back/.env` (git-ignored).

| Variable                  | Default                 | What it does                              |
| ------------------------- | ----------------------- | ----------------------------------------- |
| `DEEPSEEK_API_KEY`        | —                       | DeepSeek API key. Required.               |
| `DEEPSEEK_MODEL`          | `deepseek-flash`        | Model for the tutor and the translator.   |
| `DEEPSEEK_BASE_URL`       | `https://api.deepseek.com` | DeepSeek API endpoint.                 |
| `CORS_ORIGINS`            | `http://localhost:5173` | Comma-separated frontend origins.         |
| `REQUEST_TIMEOUT_SECONDS` | `60`                    | Timeout for one DeepSeek request.         |

## Deploy (Vercel)

Two Vercel projects in the `dorhsis-projects` scope, one per folder:

| Folder   | Vercel project | Production URL                      | Env vars (Production)                    |
| -------- | -------------- | ----------------------------------- | ---------------------------------------- |
| `back/`  | `sdgbilim-api` | https://sdgbilim-api.vercel.app     | `DEEPSEEK_API_KEY`, `CORS_ORIGINS`       |
| `front/` | `sdgbilim`     | https://sdgbilim.vercel.app         | `VITE_API_URL=https://sdgbilim-api.vercel.app` |

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
cd back && npx vercel@latest env add DEEPSEEK_API_KEY production
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
| 422    | Invalid request, or DeepSeek's content filter blocked the answer     | JSON details / text    |
| 500    | The API key is wrong                                                 | text for the student   |
| 502    | DeepSeek returned an error, a cut-off, empty or broken answer        | text for the student   |
| 503    | Rate limit, overload, timeout, no network or empty DeepSeek balance  | text for the student   |

The frontend shows the body of an error response to the student, so tutor errors are plain text.

## How it works

```
app/
  main.py      FastAPI app: routes, CORS, error handler, DeepSeek client
  schemas.py   HTTP contract (mirror of front/src/api/types.ts)
  tutor.py     DeepSeek calls: chat and translate, error mapping
  prompts.py   System prompts, levels and topics
  config.py    Settings from env / .env
tests/         API tests with a fake DeepSeek client
```

- DeepSeek is called through the OpenAI SDK (`base_url=https://api.deepseek.com`), model
  `deepseek-flash` in non-thinking mode, so answers come back in a few seconds.
- [JSON mode](https://api-docs.deepseek.com/guides/json_mode) returns valid JSON but does not
  enforce a schema, so the prompts show an example answer and every answer is validated with
  Pydantic. `finish_reason` is checked first: a filtered or cut-off answer becomes a clear error.
  Blank content, a known JSON-mode quirk, is retried once.
- Chat sends only the last 30 messages of the dialogue, so long lessons stay fast and cheap.
- The key is always passed explicitly, so an `OPENAI_API_KEY` from the environment is never
  sent to DeepSeek.
- The text to translate is wrapped in `<text>` tags, and the prompt tells the model never to
  follow instructions inside it.
