import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError,
  createBackup,
  getBackups,
  refreshBackups,
  restoreBackup,
} from '../api'
import type { BackupItem, BackupOverview } from '../types'

function formatDate(value: string | null): string {
  if (!value) return 'Okänd'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('sv-SE', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(date)
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

function stateLabel(state: BackupOverview['status']['state']): string {
  switch (state) {
    case 'refreshing':
      return 'Uppdaterar lista'
    case 'creating':
      return 'Skapar backup'
    case 'restoring':
      return 'Återställer'
    case 'success':
      return 'Klar'
    case 'error':
      return 'Fel'
    default:
      return 'Redo'
  }
}

export function BackupsPage() {
  const [overview, setOverview] = useState<BackupOverview | null>(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionBusy, setActionBusy] = useState(false)

  const load = useCallback(async () => {
    try {
      setOverview(await getBackups())
      setError('')
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Backupstatus kunde inte läsas.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const operationRunning =
    overview?.status.state === 'creating' ||
    overview?.status.state === 'restoring' ||
    overview?.status.state === 'refreshing'

  useEffect(() => {
    if (!operationRunning) return

    const timer = window.setInterval(() => {
      void load()
    }, 2000)

    return () => window.clearInterval(timer)
  }, [load, operationRunning])

  async function runCreate() {
    setActionBusy(true)
    setError('')
    setNotice('')

    try {
      const status = await createBackup()
      setOverview(current =>
        current ? { ...current, status } : { status, backups: [] },
      )
      setNotice('Backup har startats. Sidan uppdateras automatiskt.')
      window.setTimeout(() => void load(), 1000)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Backup kunde inte startas.',
      )
    } finally {
      setActionBusy(false)
    }
  }

  async function refresh() {
    setActionBusy(true)
    setError('')
    setNotice('')

    try {
      const status = await refreshBackups()
      setOverview(current =>
        current ? { ...current, status } : { status, backups: [] },
      )
      window.setTimeout(() => void load(), 1000)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Backuplistan kunde inte uppdateras.',
      )
    } finally {
      setActionBusy(false)
    }
  }

  async function restore(item: BackupItem) {
    const expected = `RESTORE ${item.id}`
    const confirmation = window.prompt(
      `Återställning ersätter databas, bilagor, routade filer och .env.\n\n` +
        `En säkerhetsbackup skapas först.\n\n` +
        `Skriv exakt:\n${expected}`,
    )

    if (confirmation === null) return

    if (confirmation !== expected) {
      setError(`Bekräftelsen måste vara exakt: ${expected}`)
      return
    }

    if (
      !window.confirm(
        `Starta restore av ${item.id} nu? Webbgränssnittet kan startas om under återställningen.`,
      )
    ) {
      return
    }

    setActionBusy(true)
    setError('')
    setNotice('')

    try {
      const status = await restoreBackup(item.id, confirmation)
      setOverview(current =>
        current ? { ...current, status } : { status, backups: [] },
      )
      setNotice(
        'Restore har startats. En pre-restore backup skapas automatiskt först.',
      )
      window.setTimeout(() => void load(), 2000)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Restore kunde inte startas.',
      )
    } finally {
      setActionBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Backup & Restore</h1>
        </div>
        <div className="card-actions">
          <Link className="button-link secondary" to="/admin">
            Operations
          </Link>
          <Link className="button-link secondary" to="/">
            Till översikten
          </Link>
        </div>
      </header>

      <main className="content">
        {error && <div className="alert" role="alert">{error}</div>}
        {notice && <div className="success">{notice}</div>}

        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Skydd av data</p>
              <h2>Backupstatus</h2>
            </div>

            <span
              className={`status-pill ${
                overview?.status.state === 'error'
                  ? 'failed'
                  : operationRunning
                    ? 'pending'
                    : 'ok'
              }`}
            >
              {overview ? stateLabel(overview.status.state) : 'Läser…'}
            </span>
          </div>

          <p className="muted">
            Backup innehåller PostgreSQL-databasen, bilagor, routade filer och
            den matchande <code>.env</code>-filen. Den behövs för att krypterade
            e-post/OAuth-uppgifter ska kunna återställas korrekt.
          </p>

          {overview?.status.message && (
            <p>
              <strong>Status:</strong> {overview.status.message}
            </p>
          )}

          {overview?.status.backup_id && (
            <p className="muted">
              Backup: <code>{overview.status.backup_id}</code>
            </p>
          )}

          <div className="card-actions">
            <button
              disabled={actionBusy || operationRunning}
              onClick={() => void runCreate()}
            >
              {overview?.status.state === 'creating'
                ? 'Skapar backup…'
                : 'Skapa backup nu'}
            </button>

            <button
              className="secondary"
              disabled={actionBusy || operationRunning}
              onClick={() => void refresh()}
            >
              Uppdatera historik
            </button>
          </div>
        </section>

        <section>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Historik</p>
              <h2>
                {overview?.backups.length ?? 0} backup
                {(overview?.backups.length ?? 0) === 1 ? '' : 'er'}
              </h2>
            </div>
          </div>

          <div className="backup-list">
            {!loading && !overview?.backups.length && (
              <div className="empty-state">
                Inga backuper finns ännu. Skapa den första backupen ovan.
              </div>
            )}

            {overview?.backups.map(item => (
              <article className="backup-card" key={item.id}>
                <div className="backup-card-main">
                  <div className="account-title">
                    <h3>{item.id}</h3>
                    <span
                      className={`status-pill ${
                        item.sha256_verified ? 'ok' : 'pending'
                      }`}
                    >
                      {item.sha256_verified ? 'Verifierad' : 'Ej markerad'}
                    </span>
                  </div>

                  <p>{formatDate(item.created_at)}</p>

                  <div className="backup-size-grid">
                    <span>
                      <strong>{formatBytes(item.size_bytes)}</strong>
                      <small>Totalt</small>
                    </span>
                    <span>
                      <strong>{formatBytes(item.database_bytes)}</strong>
                      <small>Databas</small>
                    </span>
                    <span>
                      <strong>{formatBytes(item.attachments_bytes)}</strong>
                      <small>Bilagor</small>
                    </span>
                    <span>
                      <strong>{formatBytes(item.routed_bytes)}</strong>
                      <small>Routat</small>
                    </span>
                  </div>

                  <p className="muted">
                    Miljöfil: {item.has_environment ? 'Ja' : 'Saknas'}
                  </p>
                </div>

                <button
                  className="danger"
                  disabled={actionBusy || operationRunning || !item.has_environment}
                  onClick={() => void restore(item)}
                >
                  Återställ
                </button>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
