import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError,
  applyUpdate,
  checkForUpdates,
  getOperationsDashboard,
  getUpdateStatus,
} from '../api'
import type { OperationsDashboard, UpdateStatus } from '../types'

function formatDate(value: string | null): string {
  if (!value) return 'Aldrig'
  return new Intl.DateTimeFormat('sv-SE', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(new Date(value))
}


function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value <= 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = value
  let unit = 0

  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }

  return `${size >= 10 || unit === 0 ? size.toFixed(0) : size.toFixed(1)} ${units[unit]}`
}

function formatUptime(value: number | null | undefined): string {
  if (value === null || value === undefined || value < 0) return 'Okänd'

  const seconds = Math.floor(value)
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days} d ${hours} h`
  if (hours > 0) return `${hours} h ${minutes} min`
  return `${minutes} min`
}

function label(name: string): string {
  return name.replaceAll('_', ' ')
}

function shortCommit(value: string | null): string {
  return value ? value.slice(0, 8) : '–'
}

function updateStateLabel(
  state: UpdateStatus['state'] | undefined,
): string {
  switch (state) {
    case 'idle':
      return 'Redo'
    case 'checking':
      return 'Kontrollerar'
    case 'up_to_date':
      return 'Uppdaterad'
    case 'update_available':
      return 'Ny version finns'
    case 'updating':
      return 'Uppdaterar'
    case 'success':
      return 'Uppdaterad'
    case 'error':
      return 'Fel'
    case 'unavailable':
      return 'Ej installerad'
    default:
      return 'Okänd'
  }
}

export function AdminPage() {
  const [dashboard, setDashboard] = useState<OperationsDashboard | null>(null)
  const [update, setUpdate] = useState<UpdateStatus | null>(null)
  const [error, setError] = useState('')
  const [updateError, setUpdateError] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [checkingUpdate, setCheckingUpdate] = useState(false)

  const operationRunning =
    update?.state === 'checking' || update?.state === 'updating'

  async function reload() {
    setRefreshing(true)
    setError('')
    try {
      setDashboard(await getOperationsDashboard())
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Operationsdata kunde inte läsas.',
      )
    } finally {
      setRefreshing(false)
    }
  }

  async function loadUpdateStatus() {
    try {
      const current = await getUpdateStatus()
      setUpdate(current)
      setUpdateError('')
    } catch (caught) {
      setUpdate(null)
      setUpdateError(
        caught instanceof ApiError
          ? caught.message
          : 'Uppdateringsstatus kunde inte läsas.',
      )
    }
  }

  async function checkUpdate() {
    setCheckingUpdate(true)
    setUpdateError('')
    try {
      const next = await checkForUpdates()
      setUpdate(next)
      window.setTimeout(() => void loadUpdateStatus(), 1000)
    } catch (caught) {
      setUpdateError(
        caught instanceof ApiError
          ? caught.message
          : 'GitHub kunde inte kontrolleras.',
      )
    } finally {
      setCheckingUpdate(false)
    }
  }

  async function runUpdate() {
    if (
      !window.confirm(
        'Installera den nya versionen nu? Webbgränssnittet kan vara otillgängligt en kort stund.',
      )
    ) {
      return
    }

    setUpdateError('')
    try {
      const next = await applyUpdate()
      setUpdate(next)
      window.setTimeout(() => void loadUpdateStatus(), 1000)
      window.setTimeout(() => void reload(), 5000)
    } catch (caught) {
      setUpdateError(
        caught instanceof ApiError
          ? caught.message
          : 'Uppdateringen kunde inte startas.',
      )
    }
  }

  useEffect(() => {
    void reload()
    void loadUpdateStatus()

    const dashboardTimer = window.setInterval(() => void reload(), 30000)

    return () => {
      window.clearInterval(dashboardTimer)
    }
  }, [])

  useEffect(() => {
    if (!operationRunning) return

    const updateTimer = window.setInterval(
      () => void loadUpdateStatus(),
      2000,
    )

    return () => {
      window.clearInterval(updateTimer)
    }
  }, [operationRunning])

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
          <button
            className="secondary"
            onClick={() => void reload()}
            disabled={refreshing}
          >
            {refreshing ? 'Uppdaterar…' : 'Uppdatera status'}
          </button>
          <Link className="button-link secondary" to="/admin/backups">
            Backup & Restore
          </Link>
          <Link className="button-link secondary" to="/">
            Till översikten
          </Link>
        </div>
      </header>

      <main className="content operations-layout">
        {error && <div className="alert">{error}</div>}

        <section className="panel software-update-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Programvara</p>
              <h2>GitHub-uppdatering</h2>
            </div>
            <span
              className={`status-pill ${
                update?.state === 'update_available'
                  ? 'pending'
                  : update?.state === 'error' || update?.state === 'unavailable'
                    ? 'failed'
                    : 'ok'
              }`}
            >
              {updateStateLabel(update?.state)}
            </span>
          </div>

          {updateError && <div className="alert">{updateError}</div>}

          <div className="update-version-grid">
            <div>
              <span>Installerad commit</span>
              <strong>{shortCommit(update?.installed_commit ?? null)}</strong>
            </div>
            <div>
              <span>Senaste på GitHub</span>
              <strong>{shortCommit(update?.latest_commit ?? null)}</strong>
            </div>
            <div>
              <span>Senast kontrollerad</span>
              <strong>{formatDate(update?.checked_at ?? null)}</strong>
            </div>
          </div>

          {update?.latest_message && (
            <p className="update-commit-message">
              <strong>Senaste ändring:</strong> {update.latest_message}
              {update.latest_date ? ` · ${formatDate(update.latest_date)}` : ''}
            </p>
          )}

          {update?.message && (
            <p className="muted">{update.message}</p>
          )}

          {update?.state === 'unavailable' && (
            <div className="alert">
              Uppdateringsagenten kan inte nås. Kontrollera att LXC-agenten är
              installerad och att backend kan läsa och skriva <code>/control</code>.
            </div>
          )}

          {update?.state === 'error' && (
            <div className="alert">
              Uppdateringsagenten rapporterade ett fel. Kontrollera
              <code> /var/lib/mailhub-control/update.log </code> i LXC:n.
            </div>
          )}

          {update?.state === 'updating' && (
            <div className="update-progress">
              <span />
              <p>
                Hämtar kod, bygger Docker-images och startar om tjänsterna.
                Sidan kan tillfälligt tappa kontakten med backend.
              </p>
            </div>
          )}

          <div className="card-actions">
            <button
              className="secondary"
              disabled={operationRunning || checkingUpdate}
              onClick={() => void checkUpdate()}
            >
              {update?.state === 'checking' || checkingUpdate
                ? 'Kontrollerar…'
                : 'Kontrollera GitHub'}
            </button>

            <button
              disabled={
                operationRunning ||
                update?.state !== 'update_available' ||
                !update?.update_available
              }
              onClick={() => void runUpdate()}
            >
              {update?.state === 'updating' ? 'Uppdaterar…' : 'Uppdatera nu'}
            </button>

            {update?.state === 'success' && (
              <button
                className="secondary"
                onClick={() => window.location.reload()}
              >
                Ladda om nya gränssnittet
              </button>
            )}
          </div>
        </section>

        <section className="operations-summary">
          <div>
            <p className="eyebrow">Systemstatus</p>
            <h2>
              {dashboard?.overall_status === 'ok'
                ? 'Alla kärntjänster fungerar'
                : 'Systemet behöver uppmärksamhet'}
            </h2>
            <p className="muted">
              Senast uppdaterad: {formatDate(dashboard?.generated_at ?? null)}
            </p>
          </div>
          <span
            className={`status-pill ${
              dashboard?.overall_status === 'ok' ? 'ok' : 'failed'
            }`}
          >
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


        {dashboard && (
          <section className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">LXC-resurser</p>
                <h2>Systemresurser</h2>
              </div>
              <span
                className={`status-pill ${
                  dashboard.system.memory_used_percent >= 95 ||
                  dashboard.system.disk_used_percent >= 95
                    ? 'failed'
                    : dashboard.system.memory_used_percent >= 85 ||
                        dashboard.system.disk_used_percent >= 85
                      ? 'pending'
                      : 'ok'
                }`}
              >
                {dashboard.system.disk_used_percent >= 95
                  ? 'Disk kritisk'
                  : dashboard.system.memory_used_percent >= 95
                    ? 'RAM kritiskt'
                    : 'OK'}
              </span>
            </div>

            <div className="resource-grid">
              <article className="resource-card">
                <span>CPU / Load</span>
                <strong>
                  {dashboard.system.load_1m ?? '–'}
                </strong>
                <small>
                  {dashboard.system.cpu_count} CPU · 5m {dashboard.system.load_5m ?? '–'} ·
                  15m {dashboard.system.load_15m ?? '–'}
                </small>
              </article>

              <article className="resource-card">
                <span>RAM</span>
                <strong>{dashboard.system.memory_used_percent}%</strong>
                <small>
                  {formatBytes(
                    dashboard.system.memory_total_bytes -
                      dashboard.system.memory_available_bytes,
                  )}{' '}
                  av {formatBytes(dashboard.system.memory_total_bytes)}
                </small>
              </article>

              <article className="resource-card">
                <span>Disk</span>
                <strong>{dashboard.system.disk_used_percent}%</strong>
                <small>
                  {formatBytes(
                    dashboard.system.disk_total_bytes -
                      dashboard.system.disk_free_bytes,
                  )}{' '}
                  av {formatBytes(dashboard.system.disk_total_bytes)}
                </small>
              </article>

              <article className="resource-card">
                <span>Uptime</span>
                <strong>{formatUptime(dashboard.system.uptime_seconds)}</strong>
                <small>LXC/processmiljö</small>
              </article>
            </div>
          </section>
        )}

        {dashboard && (
          <section className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Backup</p>
                <h2>Backupstatus</h2>
              </div>
              <Link className="button-link secondary" to="/admin/backups">
                Hantera backup
              </Link>
            </div>

            <div className="backup-summary-grid">
              <div>
                <span>Antal</span>
                <strong>{dashboard.backups.count}</strong>
              </div>
              <div>
                <span>Senaste</span>
                <strong>{dashboard.backups.latest_id ?? 'Ingen backup'}</strong>
              </div>
              <div>
                <span>Senaste datum</span>
                <strong>{formatDate(dashboard.backups.latest_created_at)}</strong>
              </div>
              <div>
                <span>Total storlek</span>
                <strong>{formatBytes(dashboard.backups.total_size_bytes)}</strong>
              </div>
            </div>

            {dashboard.backups.message && (
              <p className="muted">{dashboard.backups.message}</p>
            )}
          </section>
        )}

        <div className="operations-columns">
          <section className="panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Beroenden</p>
                <h2>Health checks</h2>
              </div>
            </div>
            <div className="operations-list">
              {dashboard &&
                Object.entries(dashboard.health).map(([name, check]) => (
                  <div className="operations-row" key={name}>
                    <div>
                      <strong>{label(name)}</strong>
                      <p>{check.detail}</p>
                    </div>
                    <div className="operations-row-status">
                      <span
                        className={`status-pill ${
                          check.status === 'ok' ? 'ok' : 'failed'
                        }`}
                      >
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
              <div>
                <p className="eyebrow">Workers</p>
                <h2>Bakgrundsprocesser</h2>
              </div>
            </div>
            <div className="operations-list">
              {dashboard?.workers.length ? (
                dashboard.workers.map(worker => (
                  <div className="operations-row" key={worker.name}>
                    <div>
                      <strong>{worker.name}</strong>
                      <p>Heartbeat: {formatDate(worker.heartbeat_at)}</p>
                      <p>
                        {worker.processed_cycles} cykler · {worker.failures} fel
                      </p>
                    </div>
                    <span
                      className={`status-pill ${
                        ['running', 'idle'].includes(worker.state)
                          ? 'ok'
                          : 'pending'
                      }`}
                    >
                      {worker.state}
                    </span>
                  </div>
                ))
              ) : (
                <p className="muted">
                  Ingen processlokal workerstatus rapporterad.
                </p>
              )}
            </div>
          </section>
        </div>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Synkronisering</p>
              <h2>Senaste körningar</h2>
            </div>
            <Link className="button-link secondary" to="/email-accounts">
              Hantera konton
            </Link>
          </div>

          <div className="operations-table sync-table">
            <div className="operations-table-head">
              <span>Konto</span>
              <span>Status</span>
              <span>Resultat</span>
              <span>Start</span>
            </div>

            {dashboard?.recent_syncs.length ? (
              dashboard.recent_syncs.map(sync => (
                <div className="operations-table-row" key={sync.id}>
                  <span>
                    <strong>{sync.account_name}</strong>
                    <small>{sync.email_address}</small>
                  </span>
                  <span
                    className={`status-text ${
                      sync.status === 'failed' ? 'failed' : 'ok'
                    }`}
                  >
                    {sync.status}
                  </span>
                  <span>
                    {sync.messages_created} meddelanden ·{' '}
                    {sync.attachments_created} bilagor
                    {sync.error_message && (
                      <small className="sync-error">{sync.error_message}</small>
                    )}
                  </span>
                  <span>{formatDate(sync.started_at)}</span>
                </div>
              ))
            ) : (
              <div className="empty-state">
                Ingen synkroniseringshistorik finns ännu.
              </div>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Lagring</p>
              <h2>Destinationer</h2>
            </div>
            <Link className="button-link secondary" to="/storage">
              Hantera lagring
            </Link>
          </div>
          <div className="operations-table">
            <div className="operations-table-head">
              <span>Namn</span>
              <span>Leverantör</span>
              <span>Status</span>
              <span>Senaste test</span>
            </div>
            {dashboard?.storage.map(item => (
              <div className="operations-table-row" key={item.id}>
                <span>
                  <strong>{item.name}</strong>
                  <small>{item.enabled ? 'Aktiv' : 'Inaktiv'}</small>
                </span>
                <span>{item.provider}</span>
                <span className={`status-text ${item.status}`}>
                  {item.status}
                </span>
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
              {dashboard?.recent_failures.length ? (
                dashboard.recent_failures.map(item => (
                  <div
                    className="failure-row"
                    key={`${item.kind}-${item.id}`}
                  >
                    <div>
                      <strong>
                        {item.kind}: {item.subject}
                      </strong>
                      <p>{item.detail}</p>
                    </div>
                    <small>{formatDate(item.created_at)}</small>
                  </div>
                ))
              ) : (
                <div className="success">Inga senaste sync- eller routingfel.</div>
              )}
            </div>
          </section>

          <section className="panel">
            <p className="eyebrow">Aktivitet</p>
            <h2>Senaste systemhändelser</h2>
            <div className="operations-list">
              {dashboard?.recent_activity.map(item => (
                <div className="activity-row" key={item.id}>
                  <span className={`activity-level ${item.level}`}>
                    {item.level}
                  </span>
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
