import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, clearToken, getCurrentUser, getReadiness } from '../api'
import type { ReadyResponse, User } from '../types'

export function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [health, setHealth] = useState<ReadyResponse | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getCurrentUser(), getReadiness()])
      .then(([currentUser, readiness]) => {
        setUser(currentUser)
        setHealth(readiness)
      })
      .catch((caught) => {
        if (caught instanceof ApiError && caught.status === 401) {
          clearToken()
          navigate('/login', { replace: true })
          return
        }
        setError('Dashboarden kunde inte läsa status från backend.')
      })
  }, [navigate])

  function logout() {
    clearToken()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Översikt</h1>
        </div>
        <button className="secondary" onClick={logout}>Logga ut</button>
      </header>

      <main className="content">
        {error && <div className="alert" role="alert">{error}</div>}
        <section className="welcome-card">
          <div>
            <p className="eyebrow">Inloggad användare</p>
            <h2>{user?.display_name ?? 'Laddar…'}</h2>
            <p className="muted">{user?.email}</p>
          </div>
          {user?.is_admin && <span className="badge">Administratör</span>}
        </section>

        <section aria-labelledby="system-status-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">System</p>
              <h2 id="system-status-title">Tjänstestatus</h2>
            </div>
            <span className={`status-pill ${health?.status === 'ok' ? 'ok' : 'pending'}`}>
              {health?.status === 'ok' ? 'Alla system fungerar' : 'Kontrollerar…'}
            </span>
          </div>

          <div className="status-grid">
            {health ? Object.entries(health.checks).map(([name, check]) => (
              <article className="status-card" key={name}>
                <div className={`status-dot ${check.status === 'ok' ? 'ok' : 'failed'}`} />
                <div>
                  <h3>{name === 'postgres' ? 'PostgreSQL' : name === 'redis' ? 'Redis' : name}</h3>
                  <p>{check.status === 'ok' ? 'Ansluten och redo' : check.detail}</p>
                </div>
              </article>
            )) : <p className="muted">Läser systemstatus…</p>}
          </div>
        </section>

        <section className="coming-next">
          <p className="eyebrow">E-post</p>
          <h2>Anslut dina inkorgar</h2>
          <p className="muted">Lägg till flera IMAP-konton, spara uppgifterna krypterat och testa anslutningen direkt.</p>
          <Link className="button-link" to="/email-accounts">Hantera e-postkonton</Link>
          <Link className="button-link" to="/rules">Hantera regler</Link>
          <Link className="button-link secondary" to="/storage">Hantera lagring</Link>
        </section>
      </main>
    </div>
  )
}
