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

  // The backend rejects equal languages, so picking the other side's language swaps them.
  function pickFrom(lang: Lang) {
    if (lang === to) setTo(from)
    setFrom(lang)
  }

  function pickTo(lang: Lang) {
    if (lang === from) setFrom(to)
    setTo(lang)
  }

  function insertLetter(letter: string) {
    const el = inputRef.current
    const { value, caret } = insertAtCaret(el, text, letter)
    setText(value)
    requestAnimationFrame(() => el?.setSelectionRange(caret, caret))
  }

  return (
    <div className="container translate">
      <h1 className="page-title">
        Translator <span lang="kk">· Аудармашы</span>
      </h1>
      <p className="section-lead">Kazakh, English and Russian, with the Latin spelling and a usage note when it helps.</p>

      <form className="panel translate-panel" onSubmit={onSubmit}>
        <div className="lang-bar">
          <LangPicker label="From" value={from} onChange={pickFrom} />
          <button type="button" className="swap" onClick={swap} aria-label="Swap languages">
            <span aria-hidden="true">⇄</span>
          </button>
          <LangPicker label="To" value={to} onChange={pickTo} />
        </div>

        <div className="translate-grid">
          <div className="translate-in">
            <textarea
              ref={inputRef}
              value={text}
              onChange={(e) => setText(e.target.value)}
              aria-label="Text to translate"
              placeholder="Type a word or a sentence"
              rows={6}
            />
            {from === 'kk' && <KazakhKeyboard onInsert={insertLetter} />}
          </div>
          <div className="translate-out" aria-live="polite">
            {loading ? (
              <p className="empty">Translating…</p>
            ) : error ? (
              <p className="error" role="alert">
                {error}
              </p>
            ) : result ? (
              <>
                <p className="translation" lang={to}>
                  {result.translation}
                </p>
                {result.transliteration && (
                  <p className="out-line">
                    <span className="out-label">Latin</span>
                    {result.transliteration}
                  </p>
                )}
                {result.notes && (
                  <p className="out-line">
                    <span className="out-label">Note</span>
                    {result.notes}
                  </p>
                )}
              </>
            ) : (
              <p className="empty">The translation appears here.</p>
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

function LangPicker({ label, value, onChange }: { label: string; value: Lang; onChange: (lang: Lang) => void }) {
  return (
    <div className="seg seg-row" role="group" aria-label={`${label} language`}>
      {langs.map((l) => (
        <button key={l.id} type="button" aria-pressed={value === l.id} onClick={() => onChange(l.id)}>
          {l.label}
        </button>
      ))}
    </div>
  )
}
