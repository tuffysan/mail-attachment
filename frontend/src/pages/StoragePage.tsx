import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError, createStorageDestination, deleteStorageDestination,
  listManagedStorageDestinations, listStorageProviders, testStorageDestination
} from '../api'
import type { StorageDestination, StorageProvider } from '../types'

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

  const definition = useMemo(
    () => providers.find(item => item.key === provider),
    [providers, provider]
  )

  async function reload() {
    const [providerRows, destinationRows] = await Promise.all([
      listStorageProviders(), listManagedStorageDestinations()
    ])
    setProviders(providerRows)
    setDestinations(destinationRows)
  }

  useEffect(() => { void reload().catch(() => setError('Lagringsmålen kunde inte läsas.')) }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      await createStorageDestination({
        name,
        provider,
        base_path: basePath,
        config,
        is_enabled: true,
      })
      setName('')
      setConfig({})
      setNotice('Lagringsmålet sparades. Testa anslutningen innan det används.')
      await reload()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Lagringsmålet kunde inte sparas.')
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
      setError(caught instanceof ApiError ? `${destination.name}: ${caught.message}` : 'Testet misslyckades.')
      await reload()
    } finally {
      setBusyId('')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">Mail Attachment Hub</p><h1>Lagring</h1></div>
        <Link className="button-link secondary" to="/">Till översikten</Link>
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
            <input required value={name} onChange={e => setName(e.target.value)} placeholder="Företagets Google Drive" />

            <label>Leverantör</label>
            <select value={provider} onChange={e => {
              setProvider(e.target.value)
              setConfig({})
              setBasePath(e.target.value === 'local' ? '/data/routed' : '')
            }}>
              {providers.map(item => <option key={item.key} value={item.key}>{item.label}</option>)}
            </select>

            <label>Bas-sökväg</label>
            <input value={basePath} onChange={e => setBasePath(e.target.value)} placeholder="Documents/MailHub" />

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

            <button>Spara destination</button>
          </form>
        </section>

        <section>
          <p className="eyebrow">Konfigurerade mål</p>
          <h2>{destinations.length} destination{destinations.length === 1 ? '' : 'er'}</h2>
          <div className="account-list">
            {destinations.map(destination => (
              <article className="account-card" key={destination.id}>
                <div>
                  <div className="account-title">
                    <h3>{destination.name}</h3>
                    <span className={`status-pill ${destination.last_test_status === 'ok' ? 'ok' : 'pending'}`}>
                      {destination.last_test_status === 'ok' ? 'Ansluten' : destination.last_test_status === 'failed' ? 'Fel' : 'Ej testad'}
                    </span>
                  </div>
                  <p>{destination.provider} · {destination.base_path || '/'}</p>
                  <p className="muted">
                    Fält: {destination.configured_fields.length ? destination.configured_fields.join(', ') : 'inga'}
                  </p>
                  {destination.last_test_message && <p className="small">{destination.last_test_message}</p>}
                </div>
                <div className="card-actions">
                  <button className="secondary" disabled={busyId === destination.id} onClick={() => testDestination(destination)}>
                    {busyId === destination.id ? 'Testar…' : 'Testa'}
                  </button>
                  <button className="danger" onClick={async () => {
                    try {
                      await deleteStorageDestination(destination.id)
                      await reload()
                    } catch (caught) {
                      setError(caught instanceof ApiError ? caught.message : 'Destinationen kunde inte tas bort.')
                    }
                  }}>Ta bort</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
