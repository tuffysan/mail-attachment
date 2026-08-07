import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ApiError,
  changePassword,
  clearToken,
  getAuditLog,
  getCurrentUser,
} from '../api'
import type { AuditLogItem, User } from '../types'

function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('sv-SE', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(date)
}

export function SecurityPage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [audit, setAudit] = useState<AuditLogItem[]>([])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [repeatPassword, setRepeatPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      const current = await getCurrentUser()
      setUser(current)
      if (current.is_admin) {
        setAudit(await getAuditLog())
      }
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        clearToken()
        navigate('/login', { replace: true })
        return
      }
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Säkerhetsinformationen kunde inte läsas.',
      )
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setNotice('')

    if (newPassword.length < 12) {
      setError('Det nya lösenordet måste vara minst 12 tecken.')
      return
    }
    if (newPassword !== repeatPassword) {
      setError('De nya lösenorden matchar inte.')
      return
    }

    setBusy(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      clearToken()
      setNotice('Lösenordet ändrades. Alla tidigare sessioner är nu ogiltiga.')
      window.setTimeout(() => navigate('/login', { replace: true }), 1200)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Lösenordet kunde inte ändras.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Säkerhet</h1>
        </div>
        <Link className="button-link secondary" to="/">
          Till översikten
        </Link>
      </header>

      <main className="content two-column">
        <section className="panel">
          <p className="eyebrow">Konto</p>
          <h2>Byt lösenord</h2>
          <p className="muted">
            När lösenordet ändras höjs användarens token-version. Alla tidigare
            access tokens blir då ogiltiga och du måste logga in igen.
          </p>

          {error && <div className="alert" role="alert">{error}</div>}
          {notice && <div className="success" role="status">{notice}</div>}

          <form onSubmit={submit}>
            <label>Nuvarande lösenord</label>
            <input
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={event => setCurrentPassword(event.target.value)}
              required
            />

            <label>Nytt lösenord</label>
            <input
              type="password"
              minLength={12}
              autoComplete="new-password"
              value={newPassword}
              onChange={event => setNewPassword(event.target.value)}
              required
            />

            <label>Upprepa nytt lösenord</label>
            <input
              type="password"
              minLength={12}
              autoComplete="new-password"
              value={repeatPassword}
              onChange={event => setRepeatPassword(event.target.value)}
              required
            />

            <button disabled={busy}>
              {busy ? 'Ändrar…' : 'Byt lösenord och logga ut alla sessioner'}
            </button>
          </form>
        </section>

        <section className="panel">
          <p className="eyebrow">Session</p>
          <h2>Aktuell användare</h2>
          <p><strong>{user?.display_name ?? 'Laddar…'}</strong></p>
          <p className="muted">{user?.email}</p>
          <p>
            Roll: {user?.is_admin ? 'Administratör' : 'Användare'}
          </p>
          <button
            className="secondary"
            onClick={() => {
              clearToken()
              navigate('/login', { replace: true })
            }}
          >
            Logga ut denna session
          </button>
        </section>

        {user?.is_admin && (
          <section className="panel security-audit-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Audit</p>
                <h2>Senaste säkerhetshändelser</h2>
              </div>
              <button className="secondary" onClick={() => void load()}>
                Uppdatera
              </button>
            </div>

            <div className="operations-table">
              <div className="operations-table-head">
                <span>Händelse</span>
                <span>Tid</span>
                <span>Adress</span>
                <span>Objekt</span>
              </div>
              {audit.length ? audit.map(item => (
                <div className="operations-table-row" key={item.id}>
                  <span>{item.action}</span>
                  <span>{formatDate(item.created_at)}</span>
                  <span>{item.remote_address ?? '–'}</span>
                  <span>{item.entity_id ?? '–'}</span>
                </div>
              )) : (
                <div className="empty-state">Ingen audit-historik ännu.</div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
