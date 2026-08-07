import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, clearToken, getCurrentUser, getReadiness } from '../api'
import type { ReadyResponse, User } from '../types'

function healthLabel(name: string): string {
  if (name === 'postgres') return 'PostgreSQL'
  if (name === 'redis') return 'Redis'
  if (name === 'attachment_storage') return 'Bilagelagring'
  return name.replaceAll('_', ' ')
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [health, setHealth] = useState<ReadyResponse | null>(null)
  const [userError, setUserError] = useState('')
  const [healthError, setHealthError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  const loadHealth = useCallback(async () => {
    setRefreshing(true)
    setHealthError('')

    try {
      setHealth(await getReadiness())
    } catch (caught) {
      setHealthError(
        caught instanceof ApiError
          ? caught.message
          : 'Dashboarden kunde inte läsa systemstatus från backend.',
      )
    } finally {
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadDashboard() {
      setUserError('')

      try {
        const currentUser = await getCurrentUser()
        if (!cancelled) setUser(currentUser)
      } catch (caught) {
        if (caught instanceof ApiError && caught.status === 401) {
          clearToken()
          navigate('/login', { replace: true })
          return
        }

        if (!cancelled) {
          setUserError(
            caught instanceof ApiError
              ? caught.message
              : 'Dashboarden kunde inte läsa användarinformation från backend.',
          )
        }
        return
      }

      if (!cancelled) {
        await loadHealth()
      }
    }

    void loadDashboard()

    return () => {
      cancelled = true
    }
  }, [loadHealth, navigate])

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
        <div className="card-actions">
          <button
            className="secondary"
            disabled={refreshing}
            onClick={() => void loadHealth()}
          >
            {refreshing ? 'Kontrollerar…' : 'Uppdatera status'}
          </button>
          <button className="secondary" onClick={logout}>Logga ut</button>
        </div>
      </header>

      <main className="content">
        {userError && <div className="alert" role="alert">{userError}</div>}
        {healthError && <div className="alert" role="alert">{healthError}</div>}

        <section className="welcome-card">
          <div>
            <p className="eyebrow">Inloggad användare</p>
            <h2>{user?.display_name ?? 'Laddar…'}</h2>
            <p className="muted">{user?.email}</p>
          </div>
          {user?.is_admin && <span className="badge">Administratör</span>}
        </section>

        <section className="quick-actions" aria-labelledby="quick-actions-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Snabbvägar</p>
              <h2 id="quick-actions-title">Hantera Mail Attachment Hub</h2>
            </div>
          </div>

          <div className="quick-action-grid">
            <Link className="quick-action-card" to="/email-accounts">
              <strong>E-postkonton</strong>
              <span>IMAP, Gmail OAuth, test och synkronisering.</span>
            </Link>

            <Link className="quick-action-card" to="/rules">
              <strong>Regler</strong>
              <span>Bestäm vilka bilagor som ska routas och vart.</span>
            </Link>

            <Link className="quick-action-card" to="/storage">
              <strong>Lagring</strong>
              <span>Destinationer, anslutningstest och lokala rättigheter.</span>
            </Link>

            {user?.is_admin && (
              <Link className="quick-action-card" to="/admin/google-oauth">
                <strong>Google OAuth</strong>
                <span>Konfigurera Google Cloud och anslut Gmail.</span>
              </Link>
            )}

            {user?.is_admin && (
              <Link className="quick-action-card" to="/admin/backups">
                <strong>Backup & Restore</strong>
                <span>Skapa backup, visa historik och återställ säkert.</span>
              </Link>
            )}

            {user?.is_admin && (
              <Link className="quick-action-card" to="/admin">
                <strong>Operations</strong>
                <span>Workers, GitHub Update, health och senaste fel.</span>
              </Link>
            )}
          </div>
        </section>

        <section aria-labelledby="system-status-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">System</p>
              <h2 id="system-status-title">Tjänstestatus</h2>
            </div>

            <span
              className={`status-pill ${
                health?.status === 'ok'
                  ? 'ok'
                  : health?.status === 'degraded'
                    ? 'failed'
                    : 'pending'
              }`}
            >
              {health?.status === 'ok'
                ? 'Alla system fungerar'
                : health?.status === 'degraded'
                  ? 'En eller flera tjänster är degraderade'
                  : 'Kontrollerar…'}
            </span>
          </div>

          <div className="status-grid">
            {health ? (
              Object.entries(health.checks).map(([name, check]) => (
                <article className="status-card" key={name}>
                  <div
                    className={`status-dot ${
                      check.status === 'ok' ? 'ok' : 'failed'
                    }`}
                  />
                  <div>
                    <h3>{healthLabel(name)}</h3>
                    <p>
                      {check.status === 'ok'
                        ? check.detail || 'Ansluten och redo'
                        : check.detail}
                    </p>
                  </div>
                </article>
              ))
            ) : (
              <p className="muted">Läser systemstatus…</p>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
