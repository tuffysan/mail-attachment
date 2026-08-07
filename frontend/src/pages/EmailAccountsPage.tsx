import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  ApiError,
  clearToken,
  createEmailAccount,
  deleteEmailAccount,
  listEmailAccounts,
  startOAuth,
  syncEmailAccount,
  testEmailAccount,
  validateEmailAccount,
} from '../api'
import type { EmailAccount, EmailAccountCreate } from '../types'

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
                      disabled={isActive}
                      onClick={() => void syncAccount(account)}
                    >
                      {isActive ? 'Arbetar…' : 'Synkronisera'}
                    </button>

                    <button
                      className="danger"
                      disabled={isActive}
                      onClick={() => void remove(account)}
                    >
                      Ta bort
                    </button>
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
