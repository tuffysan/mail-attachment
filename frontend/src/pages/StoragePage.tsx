import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError,
  createStorageDestination,
  deleteStorageDestination,
  getLocalStoragePermissions,
  listManagedStorageDestinations,
  listStorageProviders,
  testStorageDestination,
  updateLocalStoragePermissions,
} from '../api'
import type {
  LocalStoragePermissions,
  StorageDestination,
  StorageProvider,
} from '../types'

const labels: Record<string, string> = {
  client_id: 'Client ID',
  client_secret: 'Client secret',
  token: 'OAuth token JSON',
  root_folder_id: 'Root folder ID',
  drive_id: 'Drive ID',
  drive_type: 'Drive type',
  provider: 'S3 provider',
  access_key_id: 'Access key ID',
  secret_access_key: 'Secret access key',
  region: 'Region',
  endpoint: 'Endpoint',
  acl: 'ACL',
  account: 'Storage account',
  key: 'Account key',
  sas_url: 'SAS URL',
  url: 'WebDAV URL',
  vendor: 'Vendor (nextcloud/owncloud/other)',
  user: 'Username',
  pass: 'Password',
  bearer_token: 'Bearer token',
  host: 'Host',
  port: 'Port',
  key_pem: 'Private key PEM',
  key_file_pass: 'Private key password',
  domain: 'Domain',
}

const permissionModes = [
  { value: '0700', label: '0700 – endast MailHub' },
  { value: '0750', label: '0750 – ägare full, grupp läs/kör' },
  { value: '0770', label: '0770 – ägare och grupp full åtkomst' },
  { value: '0755', label: '0755 – andra får läsa' },
  { value: '0775', label: '0775 – grupp får skriva' },
]

export function StoragePage() {
  const [providers, setProviders] = useState<StorageProvider[]>([])
  const [destinations, setDestinations] = useState<StorageDestination[]>([])
  const [provider, setProvider] = useState('local')
  const [name, setName] = useState('')
  const [basePath, setBasePath] = useState('/data/routed')
  const [config, setConfig] = useState<Record<string,string>>({})
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busyId, setBusyId] = useState('')
  const [creating, setCreating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [permissionTarget, setPermissionTarget] = useState<StorageDestination | null>(null)
  const [permissions, setPermissions] = useState<LocalStoragePermissions | null>(null)
  const [permissionMode, setPermissionMode] = useState('0770')
  const [recursive, setRecursive] = useState(false)

  const definition = useMemo(
    () => providers.find(item => item.key === provider),
    [providers, provider]
  )

  async function reload() {
    setLoading(true)
    try {
      const [providerRows, destinationRows] = await Promise.all([
        listStorageProviders(),
        listManagedStorageDestinations(),
      ])
      setProviders(providerRows)
      setDestinations(destinationRows)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void reload().catch((caught) =>
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Lagringsmålen kunde inte läsas.',
      ),
    )
  }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setNotice('')

    if (!name.trim()) {
      setError('Destinationen måste ha ett namn.')
      return
    }

    if (provider === 'local' && !basePath.trim()) {
      setError('En lokal destination måste ha en sökväg.')
      return
    }

    setCreating(true)

    try {
      const destination = await createStorageDestination({
        name: name.trim(),
        provider,
        base_path: basePath.trim(),
        config,
        is_enabled: true,
      })

      setName('')
      setConfig({})

      try {
        const test = await testStorageDestination(destination.id)
        setNotice(`${destination.name}: ${test.message}`)
      } catch (caught) {
        setError(
          caught instanceof ApiError
            ? `${destination.name} sparades men testet misslyckades: ${caught.message}`
            : `${destination.name} sparades men anslutningstestet misslyckades.`,
        )
      }

      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Lagringsmålet kunde inte sparas.',
      )
    } finally {
      setCreating(false)
    }
  }

  async function testDestination(destination: StorageDestination) {
    setBusyId(destination.id)
    setError('')
    try {
      const result = await testStorageDestination(destination.id)
      setNotice(`${destination.name}: ${result.message}`)
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? `${destination.name}: ${caught.message}`
          : 'Testet misslyckades.'
      )
      await reload()
    } finally {
      setBusyId('')
    }
  }

  async function openPermissions(destination: StorageDestination) {
    setBusyId(destination.id)
    setError('')
    try {
      const result = await getLocalStoragePermissions(destination.id)
      setPermissionTarget(destination)
      setPermissions(result)
      setPermissionMode(result.mode ?? '0770')
      setRecursive(false)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Rättigheterna kunde inte läsas.'
      )
    } finally {
      setBusyId('')
    }
  }

  async function savePermissions(event: FormEvent) {
    event.preventDefault()
    if (!permissionTarget) return

    setBusyId(permissionTarget.id)
    setError('')
    setNotice('')

    try {
      const result = await updateLocalStoragePermissions(
        permissionTarget.id,
        {
          mode: permissionMode,
          recursive,
        },
      )
      setPermissions(result)
      setNotice(
        `${permissionTarget.name}: rättigheter ändrade till ${result.mode}.`
      )
      await testDestination(permissionTarget)
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Rättigheterna kunde inte ändras.'
      )
    } finally {
      setBusyId('')
    }
  }

  async function removeDestination(destination: StorageDestination) {
    if (
      !window.confirm(
        `Ta bort destinationen "${destination.name}"? Regler som använder destinationen kan påverkas.`,
      )
    ) {
      return
    }

    setBusyId(destination.id)
    setError('')
    setNotice('')

    try {
      await deleteStorageDestination(destination.id)
      if (permissionTarget?.id === destination.id) {
        setPermissionTarget(null)
        setPermissions(null)
      }
      setNotice(`Destinationen "${destination.name}" togs bort.`)
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Destinationen kunde inte tas bort.',
      )
    } finally {
      setBusyId('')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Lagring</h1>
        </div>
        <Link className="button-link secondary" to="/">
          Till översikten
        </Link>
      </header>

      <main className="content two-column">
        <section className="panel">
          <p className="eyebrow">Ny destination</p>
          <h2>Anslut lagring</h2>
          <p className="muted">Hemliga värden krypteras innan de sparas.</p>

          {error && <div className="alert">{error}</div>}
          {notice && <div className="success">{notice}</div>}

          <form onSubmit={submit}>
            <label>Namn</label>
            <input
              required
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Företagets Google Drive"
            />

            <label>Leverantör</label>
            <select
              value={provider}
              onChange={e => {
                setProvider(e.target.value)
                setConfig({})
                setBasePath(e.target.value === 'local' ? '/data/routed' : '')
              }}
            >
              {providers.map(item => (
                <option key={item.key} value={item.key}>{item.label}</option>
              ))}
            </select>

            <label>Bas-sökväg</label>
            <input
              value={basePath}
              onChange={e => setBasePath(e.target.value)}
              placeholder="Documents/MailHub"
            />

            {definition?.fields.map(field => (
              <div key={field}>
                <label>{labels[field] || field}</label>
                <input
                  type={definition.secret_fields.includes(field) ? 'password' : 'text'}
                  value={config[field] || ''}
                  onChange={e => setConfig({...config, [field]: e.target.value})}
                />
              </div>
            ))}

            <button disabled={creating || loading}>
              {creating ? 'Sparar och testar…' : 'Spara och testa destination'}
            </button>
          </form>
        </section>

        <section>
          <p className="eyebrow">Konfigurerade mål</p>
          <h2>
            {destinations.length} destination
            {destinations.length === 1 ? '' : 'er'}
          </h2>

          <div className="account-list">
            {!destinations.length && !loading && (
              <div className="empty-state">
                Inga lagringsdestinationer är konfigurerade ännu.
              </div>
            )}

            {destinations.map(destination => (
              <article className="account-card" key={destination.id}>
                <div>
                  <div className="account-title">
                    <h3>{destination.name}</h3>
                    <span
                      className={`status-pill ${
                        destination.last_test_status === 'ok'
                          ? 'ok'
                          : destination.last_test_status === 'failed'
                            ? 'failed'
                            : 'pending'
                      }`}
                    >
                      {destination.last_test_status === 'ok'
                        ? 'Ansluten'
                        : destination.last_test_status === 'failed'
                          ? 'Fel'
                          : 'Ej testad'}
                    </span>
                  </div>

                  <p>{destination.provider} · {destination.base_path || '/'}</p>

                  <p className="muted">
                    Fält: {destination.configured_fields.length
                      ? destination.configured_fields.join(', ')
                      : 'inga'}
                  </p>

                  {destination.last_test_message && (
                    <p className="small">{destination.last_test_message}</p>
                  )}
                </div>

                <div className="card-actions">
                  {destination.provider === 'local' && (
                    <button
                      className="secondary"
                      disabled={busyId === destination.id}
                      onClick={() => void openPermissions(destination)}
                    >
                      Rättigheter
                    </button>
                  )}

                  <button
                    className="secondary"
                    disabled={busyId === destination.id}
                    onClick={() => void testDestination(destination)}
                  >
                    {busyId === destination.id ? 'Arbetar…' : 'Testa'}
                  </button>

                  <button
                    className="danger"
                    disabled={busyId === destination.id}
                    onClick={() => void removeDestination(destination)}
                  >
                    {busyId === destination.id ? 'Arbetar…' : 'Ta bort'}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>

        {permissionTarget && (
          <section className="panel storage-permissions-panel">
            <p className="eyebrow">Lokal lagring</p>
            <h2>Rättigheter – {permissionTarget.name}</h2>

            <div className="setup-summary">
              <p><strong>Sökväg:</strong> <code>{permissions?.path}</code></p>
              <p>
                <strong>Ägare:</strong>{' '}
                {permissions?.owner ?? 'UID'} ({permissions?.uid ?? '-'})
              </p>
              <p>
                <strong>Grupp:</strong>{' '}
                {permissions?.group ?? 'GID'} ({permissions?.gid ?? '-'})
              </p>
              <p><strong>Mode:</strong> {permissions?.mode ?? '-'}</p>
              <p>
                <strong>Skrivbar:</strong>{' '}
                {permissions?.writable ? 'Ja' : 'Nej'}
              </p>
              <p>
                <strong>Körbar/traverserbar:</strong>{' '}
                {permissions?.executable ? 'Ja' : 'Nej'}
              </p>
            </div>

            {permissions && (!permissions.writable || !permissions.executable) && (
              <div className="alert">
                Mail Attachment Hub saknar full åtkomst till katalogen. Välj ett
                lämpligt Unix mode och spara rättigheterna, och kör sedan
                anslutningstestet igen.
              </div>
            )}

            <form onSubmit={savePermissions}>
              <label>Unix-rättigheter</label>
              <select
                value={permissionMode}
                onChange={e => setPermissionMode(e.target.value)}
              >
                {permissionModes.map(item => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={recursive}
                  onChange={e => setRecursive(e.target.checked)}
                />
                Tillämpa även på befintliga mappar och filer
              </label>

              <div className="card-actions">
                <button type="submit" disabled={busyId === permissionTarget.id}>
                  Spara rättigheter
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => setPermissionTarget(null)}
                >
                  Stäng
                </button>
              </div>
            </form>

            <p className="muted">
              Ägare sätts automatiskt till Mail Attachment Hub (UID/GID 10001)
              av Docker-startsteget. Webbgränssnittet ändrar Unix mode utan att
              ge backend root-behörighet.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}
