# BilimAI — frontend

React + TypeScript + Vite site for the Kazakh-language AI tutor (SDG KBTU Hackathon, SDG 4).

## Run

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build
```

Without a backend, the app runs in **demo mode** with mocked answers (`src/api/mock.ts`).
To use the real backend, create `front/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

> The LLM API key must stay on the backend. The browser only talks to `back/`.

## Pages

| Route        | What it does                                                        |
| ------------ | ------------------------------------------------------------------- |
| `/`          | Landing page: idea, features, how it works, SDG 4                   |
| `/tutor`     | Chat with the tutor: level, topics, corrections, new-words panel    |
| `/translate` | Kazakh ⇄ English ⇄ Russian translator with transliteration          |

Both input boxes have a row of Kazakh-only letters (ә ғ қ ң ө ұ ү һ і) for students without a Kazakh keyboard.

## API contract (for the backend)

Types live in `src/api/types.ts`. The backend needs CORS enabled for the frontend origin.

### `POST /api/chat`

```jsonc
// request
{
  "messages": [{ "role": "user", "content": "Мен атым Алихан" }], // full dialogue, oldest first
  "level": "beginner",          // "beginner" | "intermediate" | "advanced"
  "topic": "greetings"          // optional: greetings | family | food | city | school | numbers
}
// response
{
  "reply": "Жақсы талпыныс! ... **bold** is supported, \n for new lines",
  "corrections": [               // optional
    { "original": "Мен атым", "corrected": "Менің атым", "explanation": "Use the possessive..." }
  ],
  "newWords": [                  // optional
    { "kk": "сәлем", "en": "hi", "ru": "привет" }
  ]
}
```

The backend asks the model for an answer that follows a JSON schema and validates it, so `corrections` and `newWords` come back as separate fields.

### `POST /api/translate`

```jsonc
// request
{ "text": "thank you", "from": "en", "to": "kk" }   // "kk" | "en" | "ru"
// response
{ "translation": "Рақмет", "transliteration": "Raqmet", "notes": "optional usage note" }
```

## Structure

```
src/
  api/          types.ts (contract), client.ts (fetch + mock switch), mock.ts
  components/   Layout, KazakhKeyboard, RichText
  data/         topics, levels, Kazakh letters
  pages/        Home, Tutor, Translate
  utils/        insertAtCaret
  index.css     design tokens (Kazakh flag sky-blue + gold), light/dark
```
