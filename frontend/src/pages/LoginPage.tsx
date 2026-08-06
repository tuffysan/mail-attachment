import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, getSetupStatus, login, setToken } from '../api'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const token = await login(email, password)
      setToken(token.access_token)
      const setup = await getSetupStatus()
      navigate(setup.completed ? '/' : '/setup', { replace: true })
    } catch (caught) {
      setError(caught instanceof ApiError && caught.status === 401
        ? 'Fel e-postadress eller lösenord.'
        : 'Det gick inte att logga in. Kontrollera att tjänsten är igång.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card" aria-labelledby="login-title">
        <div className="brand-mark" aria-hidden="true">MA</div>
        <p className="eyebrow">Mail Attachment Hub</p>
        <h1 id="login-title">Logga in</h1>
        <p className="muted">Hantera e-postbilagor och lagringsflöden på ett säkert ställe.</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="email">E-postadress</label>
          <input id="email" type="email" autoComplete="username" required value={email}
            onChange={(event) => setEmail(event.target.value)} />

          <label htmlFor="password">Lösenord</label>
          <input id="password" type="password" autoComplete="current-password" required
            minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} />

          {error && <div className="alert" role="alert">{error}</div>}
          <button type="submit" disabled={submitting}>
            {submitting ? 'Loggar in…' : 'Logga in'}
          </button>
        </form>
        <p className="hint">Administratörsuppgifterna skapas av <code>make init</code>.</p>
      </section>
    </main>
  )
}
