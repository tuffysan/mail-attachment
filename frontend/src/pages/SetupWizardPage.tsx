import { FormEvent, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ApiError,
  changeSetupPassword,
  completeSetup,
  createEmailAccount,
  createRule,
  createStorageDestination,
  getCurrentUser,
  getSetupStatus,
  listManagedStorageDestinations,
  updateSetupPreferences,
} from '../api'
import type { SetupStatus, User } from '../types'

type Step = 1 | 2 | 3 | 4 | 5

export function SetupWizardPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>(1)
  const [status, setStatus] = useState<SetupStatus | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const [displayName, setDisplayName] = useState('Administrator')
  const [language, setLanguage] = useState('sv')
  const [timezone, setTimezone] = useState('Europe/Stockholm')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')

  const [emailAddress, setEmailAddress] = useState('')
  const [emailPassword, setEmailPassword] = useState('')
  const [imapHost, setImapHost] = useState('imap.gmail.com')

  const [storageName, setStorageName] = useState('Local routed files')
  const [storagePath, setStoragePath] = useState('/data/routed')
  const [destinationId, setDestinationId] = useState('')

  const [ruleName, setRuleName] = useState('PDF attachments')
  const [filenamePattern, setFilenamePattern] = useState('\\.pdf$')
  const [folderTemplate, setFolderTemplate] = useState('{year}/{month}/{sender}')

  useEffect(() => {
    Promise.all([getSetupStatus(), getCurrentUser(), listManagedStorageDestinations()])
      .then(([setup, currentUser, destinations]) => {
        if (setup.completed) {
          navigate('/', { replace: true })
          return
        }
        setStatus(setup)
        setUser(currentUser)
        setDisplayName(currentUser.display_name)
        setLanguage(setup.language)
        setTimezone(setup.timezone)
        const local = destinations.find(item => item.provider === 'local')
        if (local) setDestinationId(local.id)
      })
      .catch(() => setError('Installationsguiden kunde inte läsa aktuell konfiguration.'))
  }, [navigate])

  async function saveAdmin(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await updateSetupPreferences({
        display_name: displayName,
        language,
        timezone,
      })
      if (currentPassword || newPassword) {
        if (!currentPassword || !newPassword) {
          throw new Error('Fyll i både nuvarande och nytt lösenord.')
        }
        await changeSetupPassword({
          current_password: currentPassword,
          new_password: newPassword,
        })
      }
      setStep(2)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : String(caught))
    } finally {
      setBusy(false)
    }
  }

  async function saveEmail(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (emailAddress && emailPassword) {
        await createEmailAccount({
          name: 'Primary inbox',
          email_address: emailAddress,
          host: imapHost,
          port: 993,
          username: emailAddress,
          password: emailPassword,
          mailbox: 'INBOX',
          use_ssl: true,
          is_enabled: true,
        })
      }
      setStep(3)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'E-postkontot kunde inte sparas.')
    } finally {
      setBusy(false)
    }
  }

  async function saveStorage(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (!destinationId) {
        const destination = await createStorageDestination({
          name: storageName,
          provider: 'local',
          base_path: storagePath,
          config: {},
          is_enabled: true,
        })
        setDestinationId(destination.id)
      }
      setStep(4)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Lagringsmålet kunde inte sparas.')
    } finally {
      setBusy(false)
    }
  }

  async function saveRule(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (destinationId) {
        await createRule({
          name: ruleName,
          priority: 100,
          is_enabled: true,
          stop_processing: false,
          filename_pattern: filenamePattern || null,
          folder_template: folderTemplate,
          destination_ids: [destinationId],
        })
      }
      setStep(5)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Regeln kunde inte sparas.')
    } finally {
      setBusy(false)
    }
  }

  async function finish() {
    setBusy(true)
    setError('')
    try {
      await completeSetup()
      navigate('/', { replace: true })
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Guiden kunde inte slutföras.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="wizard-shell">
      <section className="wizard-card">
        <div className="wizard-header">
          <div className="brand-mark">MA</div>
          <div>
            <p className="eyebrow">Första konfiguration</p>
            <h1>Välkommen till Mail Attachment Hub</h1>
            <p className="muted">Steg {step} av 5 · Inloggad som {user?.email ?? 'administratör'}</p>
          </div>
        </div>

        <div className="wizard-progress" aria-label={`Steg ${step} av 5`}>
          {[1,2,3,4,5].map(value => (
            <span key={value} className={value <= step ? 'active' : ''}>{value}</span>
          ))}
        </div>

        {error && <div className="alert" role="alert">{error}</div>}

        {step === 1 && (
          <form onSubmit={saveAdmin}>
            <h2>Administratör och regionala inställningar</h2>
            <label>Visningsnamn</label>
            <input required value={displayName} onChange={e => setDisplayName(e.target.value)} />
            <div className="form-row">
              <div>
                <label>Språk</label>
                <select value={language} onChange={e => setLanguage(e.target.value)}>
                  <option value="sv">Svenska</option>
                  <option value="en">English</option>
                </select>
              </div>
              <div>
                <label>Tidszon</label>
                <select value={timezone} onChange={e => setTimezone(e.target.value)}>
                  <option value="Europe/Stockholm">Europe/Stockholm</option>
                  <option value="Europe/Copenhagen">Europe/Copenhagen</option>
                  <option value="Europe/London">Europe/London</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>
            </div>
            <p className="muted">Byt gärna det genererade installationslösenordet nu.</p>
            <label>Nuvarande lösenord</label>
            <input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
            <label>Nytt lösenord</label>
            <input type="password" minLength={12} value={newPassword} onChange={e => setNewPassword(e.target.value)} />
            <button disabled={busy}>{busy ? 'Sparar…' : 'Fortsätt'}</button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={saveEmail}>
            <h2>Anslut första e-postkontot</h2>
            <p className="muted">Du kan hoppa över detta och konfigurera OAuth eller IMAP senare.</p>
            <label>E-postadress</label>
            <input type="email" value={emailAddress} onChange={e => setEmailAddress(e.target.value)} />
            <label>IMAP-server</label>
            <input value={imapHost} onChange={e => setImapHost(e.target.value)} />
            <label>Applösenord eller IMAP-lösenord</label>
            <input type="password" value={emailPassword} onChange={e => setEmailPassword(e.target.value)} />
            <div className="wizard-actions">
              <button type="button" className="secondary" onClick={() => setStep(3)}>Hoppa över</button>
              <button disabled={busy}>{busy ? 'Sparar…' : 'Spara och fortsätt'}</button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={saveStorage}>
            <h2>Välj första lagringsmål</h2>
            {destinationId ? (
              <div className="success">En lokal destination finns redan och kommer att användas.</div>
            ) : (
              <>
                <label>Namn</label>
                <input required value={storageName} onChange={e => setStorageName(e.target.value)} />
                <label>Lokal sökväg</label>
                <input required value={storagePath} onChange={e => setStoragePath(e.target.value)} />
              </>
            )}
            <button disabled={busy}>{busy ? 'Sparar…' : 'Fortsätt'}</button>
          </form>
        )}

        {step === 4 && (
          <form onSubmit={saveRule}>
            <h2>Skapa första regeln</h2>
            <p className="muted">Standardregeln sparar PDF-bilagor i mappar efter år, månad och avsändare.</p>
            <label>Regelnamn</label>
            <input required value={ruleName} onChange={e => setRuleName(e.target.value)} />
            <label>Filnamnsmönster</label>
            <input value={filenamePattern} onChange={e => setFilenamePattern(e.target.value)} />
            <label>Mappmall</label>
            <input required value={folderTemplate} onChange={e => setFolderTemplate(e.target.value)} />
            <div className="wizard-actions">
              <button type="button" className="secondary" onClick={() => setStep(5)}>Hoppa över</button>
              <button disabled={busy || !destinationId}>{busy ? 'Sparar…' : 'Spara och fortsätt'}</button>
            </div>
          </form>
        )}

        {step === 5 && (
          <section>
            <h2>Installationen är redo</h2>
            <div className="setup-summary">
              <p><strong>Språk:</strong> {language}</p>
              <p><strong>Tidszon:</strong> {timezone}</p>
              <p><strong>E-post:</strong> {emailAddress || (status?.has_email_account ? 'Redan konfigurerad' : 'Konfigureras senare')}</p>
              <p><strong>Lagring:</strong> {destinationId ? 'Konfigurerad' : 'Konfigureras senare'}</p>
              <p><strong>Regel:</strong> {ruleName || 'Konfigureras senare'}</p>
            </div>
            <div className="success">
              Spara filen <code>/root/mailhub-credentials.txt</code> säkert och testa backup innan produktionsdrift.
            </div>
            <button disabled={busy} onClick={finish}>{busy ? 'Slutför…' : 'Slutför installationen'}</button>
          </section>
        )}
      </section>
    </main>
  )
}
