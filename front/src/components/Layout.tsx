import { NavLink, Outlet } from 'react-router-dom'
import { isMockMode } from '../api/client'
import { BrandMark } from './BrandMark'

export function Layout() {
  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>

      <header className="nav">
        <div className="container nav-inner">
          <NavLink to="/" className="brand" aria-label="BilimAI home">
            <BrandMark />
            <span>
              Bilim<span className="brand-ai">AI</span>
            </span>
          </NavLink>
          <nav className="nav-links" aria-label="Main">
            <NavLink to="/" end>
              Home
            </NavLink>
            <NavLink to="/tutor">Tutor</NavLink>
            <NavLink to="/translate">Translator</NavLink>
          </nav>
        </div>
      </header>

      {isMockMode && (
        <p className="demo-note">
          Demo mode: answers are pre-written. Set <code>VITE_API_URL</code> to connect the backend.
        </p>
      )}

      <main id="main">
        <Outlet />
      </main>

      <footer className="footer">
        <div className="container footer-inner">
          <span>BilimAI · SDG KBTU Hackathon 2026 · SDG 4 Quality Education</span>
          <span>Powered by Meta Muse</span>
        </div>
      </footer>
    </div>
  )
}
