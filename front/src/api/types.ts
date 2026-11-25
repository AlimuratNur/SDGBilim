// Shared contract between the frontend and the backend (back/).
// Keep this file in sync with the backend team.

export type Role = 'user' | 'assistant'

export type Level = 'beginner' | 'intermediate' | 'advanced'

export type Lang = 'kk' | 'en' | 'ru'

export interface ChatMessage {
  role: Role
  content: string
}

export interface Correction {
  original: string
  corrected: string
  explanation: string
}

export interface NewWord {
  kk: string
  en: string
  ru?: string
}

/** POST /api/chat */
export interface ChatRequest {
  messages: ChatMessage[]
  level: Level
  topic?: string
}

export interface ChatResponse {
  reply: string
  corrections?: Correction[]
  newWords?: NewWord[]
}

/** POST /api/translate */
export interface TranslateRequest {
  text: string
  from: Lang
  to: Lang
}

export interface TranslateResponse {
  translation: string
  transliteration?: string
  notes?: string
}
