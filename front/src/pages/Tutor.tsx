import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { sendChat } from '../api/client'
import type { ChatMessage, Correction, Level, NewWord } from '../api/types'
import { levels, topics } from '../data/lessons'
import { KazakhKeyboard } from '../components/KazakhKeyboard'
import { insertAtCaret } from '../utils/insertAtCaret'
import { RichText } from '../components/RichText'

interface UiMessage extends ChatMessage {
  corrections?: Correction[]
}

const greeting: UiMessage = {
  role: 'assistant',
  content:
    'Сәлем! 👋 I am **BilimAI**, your Kazakh tutor.\nPick a topic on the left or just say «Сәлем» to begin.',
}

export function Tutor() {
  const [messages, setMessages] = useState<UiMessage[]>([greeting])
  const [input, setInput] = useState('')
  const [level, setLevel] = useState<Level>('beginner')
  const [topic, setTopic] = useState<string | undefined>()
  const [words, setWords] = useState<NewWord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const inputRef = useRef<HTMLTextAreaElement>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  async function send(text: string) {
    const content = text.trim()
    if (!content || loading) return

    const next: UiMessage[] = [...messages, { role: 'user', content }]
    setMessages(next)
    setInput('')
    setError(null)
    setLoading(true)

    try {
      const res = await sendChat({
        // the static greeting is UI-only; the backend gets the real dialogue
        messages: next.filter((m) => m !== greeting).map(({ role, content }) => ({ role, content })),
        level,
        topic,
      })
      setMessages((m) => [...m, { role: 'assistant', content: res.reply, corrections: res.corrections }])
      if (res.newWords?.length) {
        setWords((w) => {
          const known = new Set(w.map((x) => x.kk))
          return [...w, ...res.newWords!.filter((x) => !known.has(x.kk))]
        })
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    void send(input)
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send(input)
    }
  }

  function insertLetter(letter: string) {
    const el = inputRef.current
    const { value, caret } = insertAtCaret(el, input, letter)
    setInput(value)
    requestAnimationFrame(() => el?.setSelectionRange(caret, caret))
  }

  function pickTopic(id: string) {
    const t = topics.find((x) => x.id === id)
    if (!t) return
    setTopic(t.id)
    void send(t.starter)
  }

  function reset() {
    setMessages([greeting])
    setTopic(undefined)
    setError(null)
  }

  return (
    <div className="container tutor">
      <aside className="panel tutor-side">
        <h3>Level · Деңгей</h3>
        <div className="seg">
          {levels.map((l) => (
            <button
              key={l.id}
              type="button"
              className={level === l.id ? 'active' : ''}
              onClick={() => setLevel(l.id)}
              title={l.kk}
            >
              {l.label}
            </button>
          ))}
        </div>

        <h3>Topics · Тақырыптар</h3>
        <div className="topics">
          {topics.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`topic ${topic === t.id ? 'active' : ''}`}
              onClick={() => pickTopic(t.id)}
              disabled={loading}
            >
              <span className="topic-emoji">{t.emoji}</span>
              <span>
                {t.title}
                <small>{t.kk}</small>
              </span>
            </button>
          ))}
        </div>

        <button type="button" className="btn btn-ghost btn-sm full" onClick={reset}>
          New conversation
        </button>
      </aside>

      <section className="panel chat">
        <div className="chat-log" aria-live="polite">
          {messages.map((m, i) => (
            <div key={i} className={`msg msg-${m.role}`}>
              {m.role === 'assistant' && <span className="avatar">☀</span>}
              <div className="msg-body">
                <div className="bubble-text">
                  <RichText text={m.content} />
                </div>
                {m.corrections?.map((c, j) => (
                  <div key={j} className="correction">
                    <div>
                      <s>{c.original}</s> → <strong>{c.corrected}</strong>
                    </div>
                    <small>{c.explanation}</small>
                  </div>
                ))}
              </div>
            </div>
          ))}
          {loading && (
            <div className="msg msg-assistant">
              <span className="avatar">☀</span>
              <div className="typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
          {error && <div className="error">⚠ {error}</div>}
          <div ref={endRef} />
        </div>

        <form className="chat-input" onSubmit={onSubmit}>
          <KazakhKeyboard onInsert={insertLetter} />
          <div className="chat-row">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Қазақша жазыңыз… (Write in Kazakh — Enter to send)"
              rows={2}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </form>
      </section>

      <aside className="panel tutor-words">
        <h3>New words · Жаңа сөздер</h3>
        {words.length === 0 ? (
          <p className="muted small">New vocabulary from your lesson will appear here.</p>
        ) : (
          <ul className="words">
            {words.map((w) => (
              <li key={w.kk}>
                <strong>{w.kk}</strong>
                <span>{w.en}</span>
                {w.ru && <span className="muted">{w.ru}</span>}
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  )
}
