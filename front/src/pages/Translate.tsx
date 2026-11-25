import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { translate } from '../api/client'
import type { Lang, TranslateResponse } from '../api/types'
import { KazakhKeyboard } from '../components/KazakhKeyboard'
import { insertAtCaret } from '../utils/insertAtCaret'

const langs: { id: Lang; label: string }[] = [
  { id: 'en', label: 'English' },
  { id: 'ru', label: 'Русский' },
  { id: 'kk', label: 'Қазақша' },
]

export function Translate() {
  const [from, setFrom] = useState<Lang>('en')
  const [to, setTo] = useState<Lang>('kk')
  const [text, setText] = useState('')
  const [result, setResult] = useState<TranslateResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!text.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      setResult(await translate({ text, from, to }))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  function swap() {
    setFrom(to)
    setTo(from)
    if (result) {
      setText(result.translation)
      setResult(null)
    }
  }

  function insertLetter(letter: string) {
    const el = inputRef.current
    const { value, caret } = insertAtCaret(el, text, letter)
    setText(value)
    requestAnimationFrame(() => el?.setSelectionRange(caret, caret))
  }

  return (
    <div className="container translate">
      <h1 className="page-title">Translator · Аудармашы</h1>
      <p className="section-sub left">Kazakh ⇄ English ⇄ Russian, with transliteration and usage notes from the AI.</p>

      <form className="panel translate-panel" onSubmit={onSubmit}>
        <div className="lang-bar">
          <select value={from} onChange={(e) => setFrom(e.target.value as Lang)} aria-label="From language">
            {langs.map((l) => (
              <option key={l.id} value={l.id}>
                {l.label}
              </option>
            ))}
          </select>
          <button type="button" className="btn btn-ghost btn-sm" onClick={swap} aria-label="Swap languages">
            ⇄
          </button>
          <select value={to} onChange={(e) => setTo(e.target.value as Lang)} aria-label="To language">
            {langs.map((l) => (
              <option key={l.id} value={l.id}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        <div className="translate-grid">
          <div>
            <textarea
              ref={inputRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type a word or sentence…"
              rows={6}
            />
            {from === 'kk' && <KazakhKeyboard onInsert={insertLetter} />}
          </div>
          <div className="translate-out" aria-live="polite">
            {loading ? (
              <span className="muted">Translating…</span>
            ) : error ? (
              <span className="error">⚠ {error}</span>
            ) : result ? (
              <>
                <p className="translation">{result.translation}</p>
                {result.transliteration && <p className="muted">🔤 {result.transliteration}</p>}
                {result.notes && <p className="note">💡 {result.notes}</p>}
              </>
            ) : (
              <span className="muted">Translation will appear here</span>
            )}
          </div>
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading || !text.trim()}>
          Translate
        </button>
      </form>
    </div>
  )
}
