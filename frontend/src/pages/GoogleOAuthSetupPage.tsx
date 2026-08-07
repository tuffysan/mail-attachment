import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError,
  clearGoogleOAuthConfig,
  getGoogleOAuthConfig,
  saveGoogleOAuthConfig,
  startOAuth,
} from '../api'
import type { GoogleOAuthConfig } from '../types'

function suggestedBaseUrl(): string {
  const origin = window.location.origin
  try {
    const url = new URL(origin)
    const isLocalhost =
      url.hostname === 'localhost' ||
      url.hostname === '127.0.0.1' ||
      url.hostname === '::1'

    if (url.protocol === 'https:' || isLocalhost) {
      return origin
    }
  } catch {
    // Ignore malformed browser origin.
  }
  return ''
}

export function GoogleOAuthSetupPage() {
  const [config, setConfig] = useState<GoogleOAuthConfig | null>(null)
  const [clientId, setClientId] = useState('')
  const [clientSecret, setClientSecret] = useState('')
  const [baseUrl, setBaseUrl] = useState(suggestedBaseUrl())
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [copied, setCopied] = useState(false)

  const callbackUrl = useMemo(() => {
    if (config?.redirect_uri && baseUrl === config.public_base_url) {
      return config.redirect_uri
    }
    if (!baseUrl) return ''
    return `${baseUrl.replace(/\/+$/, '')}/api/v1/oauth/google/callback`
  }, [baseUrl, config])

  async function reload() {
    const current = await getGoogleOAuthConfig()
    setConfig(current)
    setClientId(current.client_id ?? '')
    setBaseUrl(current.public_base_url ?? suggestedBaseUrl())
  }

  useEffect(() => {
    void reload().catch((caught) => {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Google OAuth-konfigurationen kunde inte läsas.',
      )
    })
  }, [])

  async function save(event?: FormEvent) {
    event?.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')

    try {
      const saved = await saveGoogleOAuthConfig({
        client_id: clientId,
        client_secret: clientSecret || null,
        public_base_url: baseUrl,
      })
      setConfig(saved)
      setClientSecret('')
      setNotice('Google OAuth-konfigurationen är sparad krypterat.')
      return saved
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Google OAuth-konfigurationen kunde inte sparas.',
      )
      return null
    } finally {
      setBusy(false)
    }
  }

  async function saveAndConnect() {
    const saved = await save()
    if (!saved?.configured) return

    setBusy(true)
    setError('')
    try {
      const result = await startOAuth('google')
      window.location.assign(result.authorization_url)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Google-inloggningen kunde inte startas.',
      )
      setBusy(false)
    }
  }

  async function connect() {
    setBusy(true)
    setError('')
    try {
      const result = await startOAuth('google')
      window.location.assign(result.authorization_url)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Google-inloggningen kunde inte startas.',
      )
      setBusy(false)
    }
  }

  async function resetConfig() {
    if (!window.confirm('Ta bort den sparade Google OAuth-konfigurationen?')) {
      return
    }

    setBusy(true)
    setError('')
    try {
      await clearGoogleOAuthConfig()
      setConfig(null)
      setClientId('')
      setClientSecret('')
      setBaseUrl(suggestedBaseUrl())
      setNotice('Google OAuth-konfigurationen har tagits bort.')
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Konfigurationen kunde inte tas bort.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function copyCallback() {
    if (!callbackUrl) return

    try {
      await navigator.clipboard.writeText(callbackUrl)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setError('Callback-URL kunde inte kopieras automatiskt. Markera och kopiera den manuellt.')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Google OAuth</h1>
        </div>
        <div className="card-actions">
          <Link className="button-link secondary" to="/email-accounts">
            E-postkonton
          </Link>
          <Link className="button-link secondary" to="/admin">
            Administration
          </Link>
        </div>
      </header>

      <main className="content google-oauth-layout">
        {error && <div className="alert">{error}</div>}
        {notice && <div className="success">{notice}</div>}

        <section className="panel google-oauth-hero">
          <div>
            <p className="eyebrow">Google Workspace / Gmail</p>
            <h2>
              {config?.configured
                ? 'Google OAuth är konfigurerat'
                : 'Konfigurera Google OAuth'}
            </h2>
            <p className="muted">
              Client Secret lagras krypterat i Mail Attachment Hub och visas
              aldrig igen i webbgränssnittet.
            </p>
          </div>
          <span
            className={`status-pill ${
              config?.configured ? 'ok' : 'failed'
            }`}
          >
            {config?.configured ? 'Konfigurerad' : 'Inte konfigurerad'}
          </span>
        </section>

        <section className="panel">
          <p className="eyebrow">Steg 1</p>
          <h2>Öppna Google Cloud</h2>
          <p className="muted">
            Börja med Google Auth Platform. Skapa eller välj ett projekt,
            konfigurera consent screen och skapa sedan en OAuth Client av typen
            Web application.
          </p>

          <div className="google-link-grid">
            <a
              className="button-link"
              href={
                config?.google_auth_overview_url ??
                'https://console.cloud.google.com/auth/overview'
              }
              target="_blank"
              rel="noreferrer"
            >
              Öppna Google Auth Platform
            </a>

            <a
              className="button-link secondary"
              href={
                config?.gmail_api_url ??
                'https://console.cloud.google.com/apis/library/gmail.googleapis.com'
              }
              target="_blank"
              rel="noreferrer"
            >
              Aktivera Gmail API
            </a>

            <a
              className="button-link secondary"
              href={
                config?.google_clients_url ??
                'https://console.cloud.google.com/auth/clients'
              }
              target="_blank"
              rel="noreferrer"
            >
              Öppna OAuth Clients
            </a>
          </div>
        </section>

        <section className="panel">
          <p className="eyebrow">Steg 2</p>
          <h2>Callback URL</h2>

          <div className="alert google-oauth-warning">
            Google accepterar normalt inte HTTP eller råa LAN-IP-adresser för
            Web OAuth. Använd ett HTTPS-hostname som når Mail Attachment Hub.
            Localhost är undantaget.
          </div>

          <label htmlFor="google-base-url">OAuth Base URL</label>
          <input
            id="google-base-url"
            placeholder="https://mail.example.com"
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
          />

          <label>Authorized redirect URI i Google</label>
          <div className="copy-field">
            <code>
              {callbackUrl || 'Ange ett HTTPS-hostname ovan'}
            </code>
            <button
              type="button"
              className="secondary"
              disabled={!callbackUrl}
              onClick={() => void copyCallback()}
            >
              {copied ? 'Kopierad' : 'Kopiera'}
            </button>
          </div>

          <p className="muted">
            Lägg exakt denna URI under Authorized redirect URIs på din Web
            application-klient i Google Cloud.
          </p>
        </section>

        <section className="panel">
          <p className="eyebrow">Steg 3</p>
          <h2>Client ID och Client Secret</h2>

          <form onSubmit={(event) => void save(event)}>
            <label htmlFor="google-client-id">Google Client ID</label>
            <input
              id="google-client-id"
              required
              autoComplete="off"
              placeholder="123456789.apps.googleusercontent.com"
              value={clientId}
              onChange={(event) => setClientId(event.target.value)}
            />

            <label htmlFor="google-client-secret">
              Google Client Secret
            </label>
            <input
              id="google-client-secret"
              type="password"
              autoComplete="new-password"
              required={!config?.client_secret_configured}
              placeholder={
                config?.client_secret_configured
                  ? 'Sparad – lämna tomt för att behålla'
                  : 'Klistra in Client Secret'
              }
              value={clientSecret}
              onChange={(event) => setClientSecret(event.target.value)}
            />

            <div className="card-actions">
              <button type="submit" disabled={busy}>
                {busy ? 'Sparar…' : 'Spara Google-konfiguration'}
              </button>

              <button
                type="button"
                className="secondary"
                disabled={busy}
                onClick={() => void saveAndConnect()}
              >
                Spara och anslut Google
              </button>
            </div>
          </form>
        </section>

        <section className="panel">
          <p className="eyebrow">Steg 4</p>
          <h2>Anslut Gmail-konto</h2>
          <p className="muted">
            När konfigurationen är sparad skickas du direkt till Googles
            inloggnings- och consent-sida. Efter godkännande kommer du tillbaka
            till Mail Attachment Hub och Gmail-kontot skapas automatiskt.
          </p>

          <div className="card-actions">
            <button
              disabled={!config?.configured || busy}
              onClick={() => void connect()}
            >
              Anslut Google-konto
            </button>

            {config?.configured && (
              <button
                className="danger"
                disabled={busy}
                onClick={() => void resetConfig()}
              >
                Ta bort Google-konfiguration
              </button>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
