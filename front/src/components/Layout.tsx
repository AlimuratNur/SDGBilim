import { NavLink, Outlet } from 'react-router-dom'
import { isMockMode } from '../api/client'

export function Layout() {
  return (
    <div className="app">
      <header className="nav">
        <div className="container nav-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark" aria-hidden>
              ☀
            </span>
            Bilim<span className="brand-accent">AI</span>
          </NavLink>
          <nav className="nav-links">
            <NavLink to="/" end>
              Home
            </NavLink>
            <NavLink to="/tutor">Tutor</NavLink>
            <NavLink to="/translate">Translate</NavLink>
          </nav>
          <NavLink to="/tutor" className="btn btn-primary btn-sm nav-cta">
            Start learning
          </NavLink>
        </div>
      </header>

      {isMockMode && (
        <div className="mock-banner">
          Demo mode — answers are mocked. Set <code>VITE_API_URL</code> to connect the Claude Haiku backend.
        </div>
      )}

      <main>
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container footer-inner">
          <span>
            BilimAI · SDG KBTU Hackathon 2026 · <strong>SDG 4</strong> Quality Education
          </span>
          <span className="muted">Powered by Claude Haiku</span>
        </div>
      </footer>
    </div>
  )
}
