import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  ApiError,
  clearToken,
  createEmailAccount,
  deleteEmailAccount,
  listEmailAccounts,
  listEmailAccountSyncRuns,
  retryEmailAccountSync,
  startOAuth,
  syncEmailAccount,
  testEmailAccount,
  updateEmailAccountSchedule,
  validateEmailAccount,
} from '../api'
import type { EmailAccount, EmailAccountCreate, SyncRun } from '../types'

const emptyForm: EmailAccountCreate = {
  name: '',
  email_address: '',
  host: 'imap.gmail.com',
  port: 993,
  username: '',
  password: '',
  mailbox: 'INBOX',
  use_ssl: true,
  is_enabled: true,
}


function formatSyncDate(value: string | null): string {
  if (!value) return 'Aldrig'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('sv-SE', {
    dateStyle: 'short',
    timeStyle: 'medium',
  }).format(date)
}

const syncIntervals = [
  { value: '', label: 'Global standard' },
  { value: '60', label: 'Varje minut' },
  { value: '300', label: 'Var 5:e minut' },
  { value: '900', label: 'Var 15:e minut' },
  { value: '1800', label: 'Var 30:e minut' },
  { value: '3600', label: 'Varje timme' },
  { value: '21600', label: 'Var 6:e timme' },
  { value: '43200', label: 'Var 12:e timme' },
  { value: '86400', label: 'En gång per dygn' },
]

export function EmailAccountsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [form, setForm] = useState<EmailAccountCreate>(emptyForm)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validated, setValidated] = useState(false)
  const [activeAccountId, setActiveAccountId] = useState('')
  const [historyOpenId, setHistoryOpenId] = useState('')
  const [historyByAccount, setHistoryByAccount] = useState<Record<string, SyncRun[]>>({})

  async function reload() {
    try {
      setAccounts(await listEmailAccounts())
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        clearToken()
        navigate('/login', { replace: true })
        return
      }

      setError('E-postkontona kunde inte läsas.')
    }
  }

  useEffect(() => {
    void reload()

    const oauth = searchParams.get('oauth')
    if (oauth === 'google-connected') {
      setNotice('Google-kontot anslöts och sparades.')
      setSearchParams({}, { replace: true })
    } else if (oauth === 'connected') {
      setNotice('OAuth-kontot anslöts.')
      setSearchParams({}, { replace: true })
    }
  }, [])

  function updateForm(patch: Partial<EmailAccountCreate>) {
    setValidated(false)
    setForm((current) => ({ ...current, ...patch }))
  }

  async function validateBeforeSave() {
    setValidating(true)
    setError('')
    setNotice('')
    setValidated(false)

    try {
      const result = await validateEmailAccount({
        host: form.host,
        port: form.port,
        username: form.username,
        password: form.password,
        mailbox: form.mailbox,
        use_ssl: form.use_ssl,
      })
      setValidated(true)
      setNotice(
        `IMAP-anslutningen fungerar. ${result.message_count ?? 0} ` +
          `meddelanden i ${result.mailbox}.`,
      )
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'IMAP-inställningarna kunde inte verifieras.',
      )
    } finally {
      setValidating(false)
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')

    try {
      await createEmailAccount(form)
      setForm(emptyForm)
      setValidated(false)
      setNotice('Kontot sparades.')
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Kontot kunde inte sparas.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function connectOAuth(provider: 'google' | 'microsoft') {
    setError('')
    setNotice('')

    try {
      const result = await startOAuth(provider)
      window.location.href = result.authorization_url
    } catch (caught) {
      if (
        provider === 'google' &&
        caught instanceof ApiError &&
        caught.message.includes('Google OAuth is not configured')
      ) {
        navigate('/admin/google-oauth')
        return
      }

      setError(
        caught instanceof ApiError
          ? caught.message
          : 'OAuth kunde inte startas.',
      )
    }
  }

  async function syncAccount(account: EmailAccount) {
    setActiveAccountId(account.id)
    setError('')
    setNotice('')

    try {
      const result = await syncEmailAccount(account.id)
      setNotice(
        `${account.name}: ${result.messages_created} nya meddelanden och ` +
          `${result.attachments_created} bilagor.`,
      )
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? `${account.name}: ${caught.message}`
          : 'Synkroniseringen misslyckades.',
      )
    } finally {
      setActiveAccountId('')
    }
  }

  async function testAccount(account: EmailAccount) {
    setActiveAccountId(account.id)
    setError('')
    setNotice('')

    try {
      const result = await testEmailAccount(account.id)
      setNotice(
        `${account.name}: anslutningen fungerar. ` +
          `${result.message_count ?? 0} meddelanden i ${result.mailbox}.`,
      )
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? `${account.name}: ${caught.message}`
          : 'Anslutningstestet misslyckades.',
      )
      await reload()
    } finally {
      setActiveAccountId('')
    }
  }


async function loadHistory(account: EmailAccount) {
  if (historyOpenId === account.id) {
    setHistoryOpenId('')
    return
  }

  setActiveAccountId(account.id)
  setError('')

  try {
    const rows = await listEmailAccountSyncRuns(account.id)
    setHistoryByAccount(current => ({
      ...current,
      [account.id]: rows,
    }))
    setHistoryOpenId(account.id)
  } catch (caught) {
    setError(
      caught instanceof ApiError
        ? `${account.name}: ${caught.message}`
        : 'Synkhistoriken kunde inte läsas.',
    )
  } finally {
    setActiveAccountId('')
  }
}

async function saveSchedule(
  account: EmailAccount,
  rawValue: string,
) {
  setActiveAccountId(account.id)
  setError('')
  setNotice('')

  try {
    await updateEmailAccountSchedule(account.id, {
      sync_interval_seconds: rawValue === '' ? null : Number(rawValue),
    })
    setNotice(`${account.name}: synkschemat uppdaterades.`)
    await reload()
  } catch (caught) {
    setError(
      caught instanceof ApiError
        ? `${account.name}: ${caught.message}`
        : 'Synkschemat kunde inte sparas.',
    )
  } finally {
    setActiveAccountId('')
  }
}

async function toggleAccount(account: EmailAccount) {
  setActiveAccountId(account.id)
  setError('')
  setNotice('')

  try {
    await updateEmailAccountSchedule(account.id, {
      sync_interval_seconds: account.sync_interval_seconds,
      is_enabled: !account.is_enabled,
    })
    setNotice(
      `${account.name}: automatisk synk ${
        account.is_enabled ? 'pausades' : 'aktiverades'
      }.`,
    )
    await reload()
  } catch (caught) {
    setError(
      caught instanceof ApiError
        ? `${account.name}: ${caught.message}`
        : 'Kontots synkstatus kunde inte ändras.',
    )
  } finally {
    setActiveAccountId('')
  }
}

async function retrySync(account: EmailAccount) {
  setActiveAccountId(account.id)
  setError('')
  setNotice('')

  try {
    const result = await retryEmailAccountSync(account.id)
    setNotice(
      `${account.name}: retry lyckades på försök ${result.attempt}. ` +
        `${result.messages_created} nya meddelanden och ` +
        `${result.attachments_created} bilagor.`,
    )
    const rows = await listEmailAccountSyncRuns(account.id)
    setHistoryByAccount(current => ({
      ...current,
      [account.id]: rows,
    }))
    setHistoryOpenId(account.id)
    await reload()
  } catch (caught) {
    setError(
      caught instanceof ApiError
        ? `${account.name}: ${caught.message}`
        : 'Retry av synkronisering misslyckades.',
    )
  } finally {
    setActiveAccountId('')
  }
}

  async function remove(account: EmailAccount) {
    if (!window.confirm(`Ta bort e-postkontot ${account.name}?`)) {
      return
    }

    setError('')
    setNotice('')

    try {
      await deleteEmailAccount(account.id)
      setNotice(`${account.name} har tagits bort.`)
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Kontot kunde inte tas bort.',
      )
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>E-postkonton</h1>
        </div>
        <Link className="button-link secondary" to="/">
          Till översikten
        </Link>
      </header>

      <main className="content two-column">
        <section className="panel">
          <p className="eyebrow">Nytt konto</p>
          <h2>Lägg till e-postkonto</h2>

          <div className="oauth-actions">
            <button
              type="button"
              className="secondary"
              onClick={() => void connectOAuth('google')}
            >
              Anslut Gmail med Google
            </button>

            <button
              type="button"
              className="secondary"
              onClick={() => void connectOAuth('microsoft')}
            >
              Anslut Microsoft 365
            </button>
          </div>

          <p className="muted">
            Du kan även lägga till ett vanligt IMAP-konto. Lösenordet
            krypteras innan det sparas i databasen.
          </p>

          {error && (
            <div className="alert" role="alert">
              {error}
            </div>
          )}

          {notice && (
            <div className="success" role="status">
              {notice}
            </div>
          )}

          <form onSubmit={submit}>
            <label htmlFor="name">Namn</label>
            <input
              id="name"
              required
              value={form.name}
              onChange={(event) =>
                updateForm({ name: event.target.value })
              }
              placeholder="Fakturor"
            />

            <label htmlFor="email">E-postadress</label>
            <input
              id="email"
              type="email"
              required
              value={form.email_address}
              onChange={(event) =>
                updateForm({
                  email_address: event.target.value,
                  username: form.username || event.target.value,
                })
              }
            />

            <label htmlFor="host">IMAP-server</label>
            <input
              id="host"
              required
              value={form.host}
              onChange={(event) =>
                updateForm({ host: event.target.value })
              }
            />

            <div className="form-row">
              <div>
                <label htmlFor="port">Port</label>
                <input
                  id="port"
                  type="number"
                  min="1"
                  max="65535"
                  required
                  value={form.port}
                  onChange={(event) =>
                    updateForm({ port: Number(event.target.value) })
                  }
                />
              </div>

              <div>
                <label htmlFor="mailbox">Mapp</label>
                <input
                  id="mailbox"
                  required
                  value={form.mailbox}
                  onChange={(event) =>
                    updateForm({ mailbox: event.target.value })
                  }
                />
              </div>
            </div>

            <label htmlFor="username">Användarnamn</label>
            <input
              id="username"
              required
              value={form.username}
              onChange={(event) =>
                updateForm({ username: event.target.value })
              }
            />

            <label htmlFor="password">Lösenord eller applösenord</label>
            <input
              id="password"
              type="password"
              required
              value={form.password}
              onChange={(event) =>
                updateForm({ password: event.target.value })
              }
            />

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={form.use_ssl}
                onChange={(event) =>
                  updateForm({ use_ssl: event.target.checked })
                }
              />
              Använd SSL/TLS
            </label>

            <div className="card-actions form-actions">
              <button
                type="button"
                className="secondary"
                disabled={busy || validating}
                onClick={() => void validateBeforeSave()}
              >
                {validating ? 'Testar…' : 'Testa inställningar'}
              </button>

              <button disabled={busy || validating}>
                {busy ? 'Sparar…' : validated ? 'Spara verifierat konto' : 'Spara konto'}
              </button>
            </div>
          </form>
        </section>

        <section>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Konfigurerade konton</p>
              <h2>
                {accounts.length} konto{accounts.length === 1 ? '' : 'n'}
              </h2>
            </div>
          </div>

          <div className="account-list">
            {accounts.map((account) => {
              const isActive = activeAccountId === account.id

              return (
                <article className="account-card" key={account.id}>
                  <div>
                    <div className="account-title">
                      <h3>{account.name}</h3>
                      <span
                        className={`status-pill ${
                          account.last_test_status === 'ok'
                            ? 'ok'
                            : 'pending'
                        }`}
                      >
                        {account.last_test_status === 'ok'
                          ? 'Verifierat'
                          : account.last_test_status === 'failed'
                            ? 'Fel'
                            : 'Ej testat'}
                      </span>
                    </div>

                    <p>{account.email_address}</p>
                    <p className="muted">
                      {account.auth_type === 'oauth'
                        ? `${account.oauth_provider ?? 'OAuth'} · ${account.mailbox}`
                        : `${account.host}:${account.port} · ${account.mailbox}`}
                    </p>

                    {account.last_test_message && (
                      <p className="small">{account.last_test_message}</p>
                    )}
                  </div>

                  <div className="email-account-controls">
                    <div className="sync-schedule">
                      <label htmlFor={`sync-${account.id}`}>Automatisk synk</label>
                      <select
                        id={`sync-${account.id}`}
                        disabled={isActive || !account.is_enabled}
                        value={account.sync_interval_seconds ?? ''}
                        onChange={event =>
                          void saveSchedule(account, event.target.value)
                        }
                      >
                        {syncIntervals.map(option => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <small>
                        Senast: {formatSyncDate(account.last_sync_at)}
                      </small>
                    </div>

                    <div className="card-actions">
                      <button
                        className="secondary"
                        disabled={isActive}
                        onClick={() => void testAccount(account)}
                      >
                        {isActive ? 'Arbetar…' : 'Testa'}
                      </button>

                      <button
                        className="secondary"
                        disabled={isActive || !account.is_enabled}
                        onClick={() => void syncAccount(account)}
                      >
                        {isActive ? 'Arbetar…' : 'Synka nu'}
                      </button>

                      <button
                        className="secondary"
                        disabled={isActive}
                        onClick={() => void loadHistory(account)}
                      >
                        {historyOpenId === account.id ? 'Dölj historik' : 'Historik'}
                      </button>

                      <button
                        className="secondary"
                        disabled={isActive}
                        onClick={() => void toggleAccount(account)}
                      >
                        {account.is_enabled ? 'Pausa auto-sync' : 'Aktivera auto-sync'}
                      </button>

                      <button
                        className="danger"
                        disabled={isActive}
                        onClick={() => void remove(account)}
                      >
                        Ta bort
                      </button>
                    </div>

                    {historyOpenId === account.id && (
                      <div className="sync-history">
                        {(historyByAccount[account.id] ?? []).length === 0 ? (
                          <p className="muted">Ingen synkhistorik ännu.</p>
                        ) : (
                          (historyByAccount[account.id] ?? []).map(run => (
                            <div className="sync-history-row" key={run.id}>
                              <div>
                                <strong>{formatSyncDate(run.started_at)}</strong>
                                <span>
                                  Försök {run.attempt} · {run.messages_seen} lästa ·{' '}
                                  {run.messages_created} nya · {run.attachments_created} bilagor
                                </span>
                                {run.error_message && (
                                  <small className="sync-error">{run.error_message}</small>
                                )}
                              </div>

                              <div className="sync-history-actions">
                                <span
                                  className={`status-pill ${
                                    run.status === 'succeeded'
                                      ? 'ok'
                                      : run.status === 'failed'
                                        ? 'failed'
                                        : 'pending'
                                  }`}
                                >
                                  {run.status}
                                </span>

                                {run.status === 'failed' && (
                                  <button
                                    className="secondary"
                                    disabled={isActive}
                                    onClick={() => void retrySync(account)}
                                  >
                                    Försök igen
                                  </button>
                                )}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                </article>
              )
            })}

            {accounts.length === 0 && (
              <div className="empty-state">
                Inga e-postkonton är konfigurerade ännu.
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
