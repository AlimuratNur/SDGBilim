import { Link } from 'react-router-dom'
import { LetterGrid } from '../components/LetterGrid'
import { MessageBubble } from '../components/MessageBubble'

const notes = [
  {
    title: 'Corrections with the rule',
    text: 'Each mistake comes back fixed, with one sentence on why.',
  },
  {
    title: 'Words you keep',
    text: 'New words from the conversation collect next to the chat, with English and Russian.',
  },
  {
    title: 'Your level, your topic',
    text: 'Beginner to advanced. Greetings, family, food, the city, university life, numbers.',
  },
]

export function Home() {
  return (
    <>
      <section className="hero">
        <div className="container hero-inner">
          <div className="hero-copy">
            <h1 lang="kk">Қазақша сөйлейік.</h1>
            <p className="hero-en">Let&apos;s speak Kazakh.</p>
            <p className="lead">
              An AI tutor that talks with you at your level, corrects every mistake and explains the rule behind it. Free
              for every student, at any hour.
            </p>
            <div className="actions">
              <Link to="/tutor" className="btn btn-primary">
                Start a lesson
              </Link>
              <Link to="/translate" className="btn btn-outline">
                Open the translator
              </Link>
            </div>
          </div>
          <LetterGrid />
        </div>
      </section>

      <section className="section">
        <div className="container demo">
          <div className="demo-copy">
            <h2>A lesson, as it happens</h2>
            <p className="section-lead">
              Write the way you can. The tutor answers in Kazakh, translates what is new for your level and marks what to
              fix.
            </p>
            <dl className="notes">
              {notes.map((n) => (
                <div key={n.title}>
                  <dt>{n.title}</dt>
                  <dd>{n.text}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="chat-sample" role="img" aria-label="Example lesson: the tutor corrects «Мен атым» to «Менің атым»">
            <MessageBubble role="assistant" content={'Сәлем! **Сенің атың кім?**\n(Hi! What is your name?)'} />
            <MessageBubble role="user" content="Мен атым Алихан" />
            <MessageBubble
              role="assistant"
              content={'Жақсы талпыныс! (Good try!)\nNow tell me: **Сен қайдансың?** (Where are you from?)'}
              corrections={[
                {
                  original: 'Мен атым',
                  corrected: 'Менің атым',
                  explanation: 'Use the possessive «менің» (my) with «атым» (my name).',
                },
              ]}
            />
          </div>
        </div>
      </section>

      <section className="section sdg">
        <div className="container sdg-inner">
          <div className="sdg-badge" aria-hidden="true">
            <span>4</span>
            Quality education
          </div>
          <div>
            <h2>Built for SDG 4</h2>
            <p className="section-lead">
              Target 4.6 asks that everyone gains literacy and language skills. BilimAI takes the cost and the schedule out
              of learning Kazakh, with feedback for each learner.
            </p>
            <Link to="/tutor" className="btn btn-primary">
              <span lang="kk">Бастайық</span> — start a lesson
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
