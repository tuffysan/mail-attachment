import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, getOperationsDashboard } from '../api'
import type { OperationsDashboard } from '../types'

function formatDate(value: string | null): string {
  if (!value) return 'Aldrig'
  return new Intl.DateTimeFormat('sv-SE', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(new Date(value))
}

function label(name: string): string {
  return name.replaceAll('_', ' ')
}

export function AdminPage() {
  const [dashboard, setDashboard] = useState<OperationsDashboard | null>(null)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  async function reload() {
    setRefreshing(true)
    setError('')
    try {
      setDashboard(await getOperationsDashboard())
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Operationsdata kunde inte läsas.')
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    void reload()
    const timer = window.setInterval(() => void reload(), 30000)
    return () => window.clearInterval(timer)
  }, [])

  const counts = dashboard?.counts
  const statCards = counts ? [
    ['E-postkonton', counts.enabled_email_accounts, `${counts.email_accounts} totalt`],
    ['Meddelanden', counts.messages, 'Bearbetade meddelanden'],
    ['Bilagor', counts.attachments, 'Extraherade bilagor'],
    ['Lyckade routes', counts.successful_routes, `${counts.pending_routes} väntar`],
    ['Routingfel', counts.failed_routes, 'Behöver granskas'],
    ['Lagringsfel', counts.failed_storage_destinations, `${counts.healthy_storage_destinations} friska`],
  ] : []

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Operations Dashboard</h1>
        </div>
        <div className="card-actions">
          <button className="secondary" onClick={() => void reload()} disabled={refreshing}>
            {refreshing ? 'Uppdaterar…' : 'Uppdatera'}
          </button>
          <Link className="button-link secondary" to="/">Till översikten</Link>
        </div>
      </header>

      <main className="content operations-layout">
        {error && <div className="alert">{error}</div>}

        <section className="operations-summary">
          <div>
            <p className="eyebrow">Systemstatus</p>
            <h2>{dashboard?.overall_status === 'ok' ? 'Alla kärntjänster fungerar' : 'Systemet behöver uppmärksamhet'}</h2>
            <p className="muted">Senast uppdaterad: {formatDate(dashboard?.generated_at ?? null)}</p>
          </div>
          <span className={`status-pill ${dashboard?.overall_status === 'ok' ? 'ok' : 'failed'}`}>
            {dashboard?.overall_status === 'ok' ? 'OK' : 'Degraderad'}
          </span>
        </section>

        <section className="operations-stats">
          {statCards.map(([title, value, subtitle]) => (
            <article className="metric-card" key={String(title)}>
              <p className="eyebrow">{title}</p>
              <strong>{value}</strong>
              <span>{subtitle}</span>
            </article>
          ))}
        </section>

        <div className="operations-columns">
          <section className="panel">
            <div className="section-heading">
              <div><p className="eyebrow">Beroenden</p><h2>Health checks</h2></div>
            </div>
            <div className="operations-list">
              {dashboard && Object.entries(dashboard.health).map(([name, check]) => (
                <div className="operations-row" key={name}>
                  <div>
                    <strong>{label(name)}</strong>
                    <p>{check.detail}</p>
                  </div>
                  <div className="operations-row-status">
                    <span className={`status-pill ${check.status === 'ok' ? 'ok' : 'failed'}`}>
                      {check.status}
                    </span>
                    <small>{check.latency_ms ?? '-'} ms</small>
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="section-heading">
              <div><p className="eyebrow">Workers</p><h2>Bakgrundsprocesser</h2></div>
            </div>
            <div className="operations-list">
              {dashboard?.workers.length ? dashboard.workers.map(worker => (
                <div className="operations-row" key={worker.name}>
                  <div>
                    <strong>{worker.name}</strong>
                    <p>Heartbeat: {formatDate(worker.heartbeat_at)}</p>
                    <p>{worker.processed_cycles} cykler · {worker.failures} fel</p>
                  </div>
                  <span className={`status-pill ${['running','idle'].includes(worker.state) ? 'ok' : 'pending'}`}>
                    {worker.state}
                  </span>
                </div>
              )) : <p className="muted">Ingen processlokal workerstatus rapporterad.</p>}
            </div>
          </section>
        </div>

        <section className="panel">
          <div className="section-heading">
            <div><p className="eyebrow">Lagring</p><h2>Destinationer</h2></div>
            <Link className="button-link secondary" to="/storage">Hantera lagring</Link>
          </div>
          <div className="operations-table">
            <div className="operations-table-head">
              <span>Namn</span><span>Leverantör</span><span>Status</span><span>Senaste test</span>
            </div>
            {dashboard?.storage.map(item => (
              <div className="operations-table-row" key={item.id}>
                <span><strong>{item.name}</strong><small>{item.enabled ? 'Aktiv' : 'Inaktiv'}</small></span>
                <span>{item.provider}</span>
                <span className={`status-text ${item.status}`}>{item.status}</span>
                <span>{formatDate(item.checked_at)}</span>
              </div>
            ))}
          </div>
        </section>

        <div className="operations-columns">
          <section className="panel">
            <p className="eyebrow">Senaste fel</p>
            <h2>Problem som behöver granskas</h2>
            <div className="operations-list">
              {dashboard?.recent_failures.length ? dashboard.recent_failures.map(item => (
                <div className="failure-row" key={`${item.kind}-${item.id}`}>
                  <div>
                    <strong>{item.kind}: {item.subject}</strong>
                    <p>{item.detail}</p>
                  </div>
                  <small>{formatDate(item.created_at)}</small>
                </div>
              )) : <div className="success">Inga senaste sync- eller routingfel.</div>}
            </div>
          </section>

          <section className="panel">
            <p className="eyebrow">Aktivitet</p>
            <h2>Senaste systemhändelser</h2>
            <div className="operations-list">
              {dashboard?.recent_activity.map(item => (
                <div className="activity-row" key={item.id}>
                  <span className={`activity-level ${item.level}`}>{item.level}</span>
                  <div>
                    <strong>{item.event_type}</strong>
                    <p>{item.message}</p>
                    <small>{formatDate(item.created_at)}</small>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
