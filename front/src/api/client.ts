import type {
  ChatRequest,
  ChatResponse,
  TranslateRequest,
  TranslateResponse,
} from './types'
import { mockChat, mockTranslate } from './mock'

// The browser never talks to the AI provider directly: the API key lives on the backend.
// Set VITE_API_URL (e.g. http://localhost:8000) in front/.env.local to use the real backend.
// Without it the app runs on mock answers, so the UI can be demoed on its own.
const API_URL = import.meta.env.VITE_API_URL as string | undefined

export const isMockMode = !API_URL

async function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`Request failed (${res.status}) ${text}`.trim())
  }
  return (await res.json()) as TRes
}

export function sendChat(req: ChatRequest): Promise<ChatResponse> {
  return isMockMode ? mockChat(req) : post('/api/chat', req)
}

export function translate(req: TranslateRequest): Promise<TranslateResponse> {
  return isMockMode ? mockTranslate(req) : post('/api/translate', req)
}
