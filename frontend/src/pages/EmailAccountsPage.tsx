import { FormEvent, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ApiError,
  clearToken,
  createEmailAccount,
  deleteEmailAccount,
  listEmailAccounts,
  testEmailAccount,
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
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [form, setForm] = useState<EmailAccountCreate>(emptyForm)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [testingId, setTestingId] = useState('')

  async function reload() {
    try {
      setAccounts(await listEmailAccounts())
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        clearToken()
        navigate('/login', { replace: true })
      } else {
        setError('E-postkontona kunde inte läsas.')
      }
    }
  }

  useEffect(() => { void reload() }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      await createEmailAccount(form)
      setForm(emptyForm)
      setNotice('Kontot sparades. Testa anslutningen innan det används.')
      await reload()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Kontot kunde inte sparas.')
    } finally {
      setBusy(false)
    }
  }

  async function connectOAuth(provider: 'google' | 'microsoft') {
        setError('')
        try {
          const result = await startOAuth(provider)
          window.location.href = result.authorization_url
        } catch (caught) {
          setError(caught instanceof ApiError ? caught.message : 'OAuth kunde inte startas.')
        }
      }

      async function syncAccount(account: EmailAccount) {
        setTestingId(account.id)
        try {
          const result = await syncEmailAccount(account.id)
          setNotice(`${account.name}: ${result.messages_created} nya meddelanden och ${result.attachments_created} bilagor.`)
          await reload()
        } catch (caught) {
          setError(caught instanceof ApiError ? caught.message : 'Synkroniseringen misslyckades.')
        } finally {
          setTestingId('')
        }
      }

      async function testAccount(account: EmailAccount) {
    setTestingId(account.id)
    setError('')
    setNotice('')
    try {
      const result = await testEmailAccount(account.id)
      setNotice(`${account.name}: anslutningen fungerar. ${result.message_count ?? 0} meddelanden i ${result.mailbox}.`)
      await reload()
    } catch (caught) {
      setError(caught instanceof ApiError ? `${account.name}: ${caught.message}` : 'Anslutningstestet misslyckades.')
      await reload()
    } finally {
      setTestingId('')
    }
  }

  async function remove(account: EmailAccount) {
    if (!window.confirm(`Ta bort e-postkontot ${account.name}?`)) return
    try {
      await deleteEmailAccount(account.id)
      await reload()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Kontot kunde inte tas bort.')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>E-postkonton</h1>
        </div>
        <Link className="button-link secondary" to="/">Till översikten</Link>
      </header>

      <main className="content two-column">
        <section className="panel">
          <p className="eyebrow">Nytt konto</p>
          <h2>Lägg till IMAP-konto</h2>
              <div className="oauth-actions">
                <button type="button" className="secondary" onClick={() => connectOAuth('google')}>Anslut Gmail med Google</button>
                <button type="button" className="secondary" onClick={() => connectOAuth('microsoft')}>Anslut Microsoft 365</button>
              </div>
          <p className="muted">Lösenordet krypteras innan det sparas i databasen.</p>
          {error && <div className="alert" role="alert">{error}</div>}
          {notice && <div className="success" role="status">{notice}</div>}
          <form onSubmit={submit}>
            <label htmlFor="name">Namn</label>
            <input id="name" required value={form.name} onChange={(e) => setForm({...form, name: e.target.value})} placeholder="Fakturor" />

            <label htmlFor="email">E-postadress</label>
            <input id="email" type="email" required value={form.email_address} onChange={(e) => setForm({...form, email_address: e.target.value, username: form.username || e.target.value})} />

            <label htmlFor="host">IMAP-server</label>
            <input id="host" required value={form.host} onChange={(e) => setForm({...form, host: e.target.value})} />

            <div className="form-row">
              <div>
                <label htmlFor="port">Port</label>
                <input id="port" type="number" min="1" max="65535" required value={form.port} onChange={(e) => setForm({...form, port: Number(e.target.value)})} />
              </div>
              <div>
                <label htmlFor="mailbox">Mapp</label>
                <input id="mailbox" required value={form.mailbox} onChange={(e) => setForm({...form, mailbox: e.target.value})} />
              </div>
            </div>

            <label htmlFor="username">Användarnamn</label>
            <input id="username" required value={form.username} onChange={(e) => setForm({...form, username: e.target.value})} />

            <label htmlFor="password">Lösenord eller applösenord</label>
            <input id="password" type="password" required value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} />

            <label className="checkbox-row">
              <input type="checkbox" checked={form.use_ssl} onChange={(e) => setForm({...form, use_ssl: e.target.checked})} />
              Använd SSL/TLS
            </label>

            <button disabled={busy}>{busy ? 'Sparar…' : 'Spara konto'}</button>
          </form>
        </section>

        <section>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Konfigurerade konton</p>
              <h2>{accounts.length} konto{accounts.length === 1 ? '' : 'n'}</h2>
            </div>
          </div>
          <div className="account-list">
            {accounts.map((account) => (
              <article className="account-card" key={account.id}>
                <div>
                  <div className="account-title">
                    <h3>{account.name}</h3>
                    <span className={`status-pill ${account.last_test_status === 'ok' ? 'ok' : 'pending'}`}>
                      {account.last_test_status === 'ok' ? 'Verifierat' : account.last_test_status === 'failed' ? 'Fel' : 'Ej testat'}
                    </span>
                  </div>
                  <p>{account.email_address}</p>
                  <p className="muted">{account.host}:{account.port} · {account.mailbox}</p>
                  {account.last_test_message && <p className="small">{account.last_test_message}</p>}
                </div>
                <div className="card-actions">
                  <button className="secondary" disabled={testingId === account.id} onClick={() => testAccount(account)}>
                    {testingId === account.id ? 'Testar…' : 'Testa'}
                  </button>
                  <button className="danger" onClick={() => remove(account)}>Ta bort</button>
                </div>
              </article>
            ))}
            {accounts.length === 0 && <div className="empty-state">Inga e-postkonton är konfigurerade ännu.</div>}
          </div>
        </section>
      </main>
    </div>
  )
}
