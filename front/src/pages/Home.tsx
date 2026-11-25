import { Link } from 'react-router-dom'

const features = [
  {
    icon: '💬',
    title: 'Conversational tutor',
    text: 'Chat in Kazakh at your level. The tutor asks questions, keeps the dialogue going and adapts to you.',
  },
  {
    icon: '✍️',
    title: 'Instant corrections',
    text: 'Every mistake gets a gentle fix with a short explanation of the grammar rule behind it.',
  },
  {
    icon: '🔁',
    title: 'Smart translator',
    text: 'Translate between Kazakh, English and Russian with Latin transliteration and usage notes.',
  },
  {
    icon: '📚',
    title: 'New words, every lesson',
    text: 'Words from each conversation are collected so you can review them later.',
  },
]

const steps = [
  { n: '1', title: 'Pick a topic & level', text: 'Greetings, family, food, university life — from beginner to advanced.' },
  { n: '2', title: 'Talk with the tutor', text: 'Write in Kazakh (or mix with English/Russian when you get stuck).' },
  { n: '3', title: 'Learn from feedback', text: 'See corrections and new vocabulary right next to the chat.' },
]

export function Home() {
  return (
    <>
      <section className="hero">
        <div className="container hero-inner">
          <div>
            <span className="eyebrow">SDG 4 · Quality Education</span>
            <h1>
              Learn Kazakh with your personal <span className="hl">AI tutor</span>
            </h1>
            <p className="lead">
              BilimAI is a patient tutor that speaks with you, corrects your mistakes and translates on the fly — powered by
              Claude Haiku. Available 24/7, free for every student.
            </p>
            <div className="hero-actions">
              <Link to="/tutor" className="btn btn-primary">
                Start a lesson
              </Link>
              <Link to="/translate" className="btn btn-ghost">
                Try the translator
              </Link>
            </div>
          </div>

          <div className="hero-card" aria-hidden>
            <div className="bubble bubble-ai">
              Сәлем! Сенің атың кім?
              <small>Hi! What is your name?</small>
            </div>
            <div className="bubble bubble-user">Мен атым Алихан</div>
            <div className="bubble bubble-ai">
              Жақсы! Almost: <b>Менің</b> атым Алихан ✨
              <small>Use the possessive «менің» — “my”.</small>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2 className="section-title">Why BilimAI?</h2>
          <p className="section-sub">
            Kazakh is the state language of Kazakhstan, yet many students lack daily practice and access to tutors. We make
            practice personal, affordable and always available.
          </p>
          <div className="grid-4">
            {features.map((f) => (
              <article key={f.title} className="card">
                <div className="card-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section section-alt">
        <div className="container">
          <h2 className="section-title">How it works</h2>
          <div className="grid-3">
            {steps.map((s) => (
              <div key={s.n} className="step">
                <span className="step-n">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container sdg">
          <div className="sdg-badge">
            <span>4</span>
            Quality
            <br />
            Education
          </div>
          <div>
            <h2 className="section-title left">Our contribution to SDG 4</h2>
            <p>
              Target 4.6 aims for everyone to gain literacy and language skills. BilimAI lowers the barrier to learning the
              Kazakh language: no tutor fees, no schedule, and feedback tuned to each learner.
            </p>
            <Link to="/tutor" className="btn btn-primary">
              Бастайық! — Let&apos;s begin
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
