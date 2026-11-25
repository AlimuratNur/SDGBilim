import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { sendChat } from '../api/client'
import type { ChatMessage, Correction, Level, NewWord } from '../api/types'
import { levels, topics } from '../data/lessons'
import { KazakhKeyboard } from '../components/KazakhKeyboard'
import { insertAtCaret } from '../utils/insertAtCaret'
import { BrandMark } from '../components/BrandMark'
import { MessageBubble } from '../components/MessageBubble'

interface UiMessage extends ChatMessage {
  corrections?: Correction[]
}

const greeting: UiMessage = {
  role: 'assistant',
  content:
    'Сәлем! I am **BilimAI**, your Kazakh tutor.\nPick a topic or just write «Сәлем» to begin.',
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
      <aside className="panel tutor-side" aria-label="Lesson settings">
        <h2 className="panel-title">Level</h2>
        <div className="seg" role="group" aria-label="Level">
          {levels.map((l) => (
            <button
              key={l.id}
              type="button"
              aria-pressed={level === l.id}
              onClick={() => setLevel(l.id)}
              title={l.kk}
            >
              {l.label}
            </button>
          ))}
        </div>

        <h2 className="panel-title">Topic</h2>
        <div className="topics">
          {topics.map((t) => (
            <button
              key={t.id}
              type="button"
              className="topic"
              aria-pressed={topic === t.id}
              onClick={() => pickTopic(t.id)}
              disabled={loading}
            >
              <span className="topic-kk" lang="kk">
                {t.kk}
              </span>
              <span className="topic-en">{t.title}</span>
            </button>
          ))}
        </div>

        <button type="button" className="btn btn-outline btn-sm" onClick={reset}>
          New conversation
        </button>
      </aside>

      <section className="panel chat" aria-label="Conversation">
        <div className="chat-log" aria-live="polite">
          {messages.map((m, i) => (
            <MessageBubble key={i} role={m.role} content={m.content} corrections={m.corrections} />
          ))}
          {loading && (
            <div className="msg msg-assistant">
              <BrandMark size="sm" />
              <div className="typing" role="status" aria-label="The tutor is typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
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
              aria-label="Your message"
              placeholder="Қазақша жазыңыз… (Write in Kazakh, Enter to send)"
              rows={2}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
              Send
            </button>
          </div>
        </form>
      </section>

      <aside className="panel tutor-words" aria-label="New words">
        <h2 className="panel-title">
          New words <span lang="kk">· Жаңа сөздер</span>
        </h2>
        {words.length === 0 ? (
          <p className="empty">Words from your conversation collect here.</p>
        ) : (
          <ul className="words">
            {words.map((w) => (
              <li key={w.kk}>
                <span className="word-kk" lang="kk">
                  {w.kk}
                </span>
                <span className="word-tr">
                  {w.en}
                  {w.ru && <> · {w.ru}</>}
                </span>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </div>
  )
}
