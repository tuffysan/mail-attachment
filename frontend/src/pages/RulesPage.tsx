import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError,
  createRule,
  deleteRule,
  listEmailAccounts,
  listRules,
  listStorageDestinations,
  simulateRules,
} from '../api'
import type {
  AttachmentRule,
  EmailAccount,
  RuleSimulationResult,
  StorageDestination,
} from '../types'

const initial = {
  name: '',
  email_account_id: '',
  priority: 100,
  stop_processing: false,
  sender_pattern: '',
  recipient_pattern: '',
  subject_pattern: '',
  filename_pattern: '',
  content_type_pattern: '',
  min_size_bytes: '',
  max_size_bytes: '',
  folder_template: '{year}/{month}/{sender}',
  destination_ids: [] as string[],
}

const regexFields = [
  ['sender_pattern', 'Avsändare'],
  ['recipient_pattern', 'Mottagare'],
  ['subject_pattern', 'Ämne'],
  ['filename_pattern', 'Filnamn'],
  ['content_type_pattern', 'Innehållstyp'],
] as const

function validateRegex(value: string, label: string): string | null {
  if (!value) return null

  try {
    new RegExp(value)
    return null
  } catch (caught) {
    return `${label}: ${
      caught instanceof Error ? caught.message : 'ogiltigt reguljärt uttryck'
    }`
  }
}

export function RulesPage() {
  const [rules, setRules] = useState<AttachmentRule[]>([])
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [destinations, setDestinations] = useState<StorageDestination[]>([])
  const [form, setForm] = useState(initial)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [simulation, setSimulation] = useState<RuleSimulationResult[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [simulating, setSimulating] = useState(false)
  const [deletingId, setDeletingId] = useState('')

  const [simulationSender, setSimulationSender] =
    useState('invoice@example.com')
  const [simulationRecipients, setSimulationRecipients] =
    useState('accounts@example.com')
  const [simulationSubject, setSimulationSubject] =
    useState('Faktura augusti')
  const [simulationFilename, setSimulationFilename] =
    useState('invoice-123.pdf')
  const [simulationContentType, setSimulationContentType] =
    useState('application/pdf')
  const [simulationSize, setSimulationSize] = useState(250000)

  async function reload() {
    setLoading(true)
    setError('')

    try {
      const [ruleRows, accountRows, destinationRows] = await Promise.all([
        listRules(),
        listEmailAccounts(),
        listStorageDestinations(),
      ])

      setRules(ruleRows)
      setAccounts(accountRows)
      setDestinations(destinationRows)

      setForm(current => {
        if (current.destination_ids.length > 0 || !destinationRows[0]) {
          return current
        }
        return {
          ...current,
          destination_ids: [destinationRows[0].id],
        }
      })
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Regler och beroenden kunde inte läsas.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void reload()
  }, [])

  function validateRule(): string | null {
    if (!form.name.trim()) {
      return 'Regeln måste ha ett namn.'
    }

    if (!form.folder_template.trim()) {
      return 'Mappmall får inte vara tom.'
    }

    if (form.destination_ids.length === 0) {
      return 'Välj minst en destination.'
    }

    for (const [field, label] of regexFields) {
      const regexError = validateRegex(form[field], label)
      if (regexError) return regexError
    }

    const min =
      form.min_size_bytes === '' ? null : Number(form.min_size_bytes)
    const max =
      form.max_size_bytes === '' ? null : Number(form.max_size_bytes)

    if (min !== null && (!Number.isFinite(min) || min < 0)) {
      return 'Minsta storlek måste vara 0 eller större.'
    }

    if (max !== null && (!Number.isFinite(max) || max < 0)) {
      return 'Största storlek måste vara 0 eller större.'
    }

    if (min !== null && max !== null && min > max) {
      return 'Minsta storlek kan inte vara större än största storlek.'
    }

    return null
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setNotice('')

    const validationError = validateRule()
    if (validationError) {
      setError(validationError)
      return
    }

    setSaving(true)

    try {
      await createRule({
        ...form,
        name: form.name.trim(),
        email_account_id: form.email_account_id || null,
        sender_pattern: form.sender_pattern || null,
        recipient_pattern: form.recipient_pattern || null,
        subject_pattern: form.subject_pattern || null,
        filename_pattern: form.filename_pattern || null,
        content_type_pattern: form.content_type_pattern || null,
        min_size_bytes:
          form.min_size_bytes === '' ? null : Number(form.min_size_bytes),
        max_size_bytes:
          form.max_size_bytes === '' ? null : Number(form.max_size_bytes),
        folder_template: form.folder_template.trim(),
        is_enabled: true,
      })

      setNotice('Regeln sparades.')
      setSimulation([])
      setForm({
        ...initial,
        destination_ids: destinations[0] ? [destinations[0].id] : [],
      })
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Regeln kunde inte sparas.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function simulate() {
    setError('')
    setNotice('')
    setSimulation([])

    if (!accounts.length) {
      setError(
        'Lägg till minst ett e-postkonto innan en regelsimulering körs.',
      )
      return
    }

    if (!simulationSender.trim() || !simulationFilename.trim()) {
      setError('Avsändare och filnamn krävs för simuleringen.')
      return
    }

    if (!Number.isFinite(simulationSize) || simulationSize < 0) {
      setError('Simulerad filstorlek måste vara 0 eller större.')
      return
    }

    setSimulating(true)

    try {
      const result = await simulateRules({
        email_account_id: form.email_account_id || accounts[0].id,
        sender: simulationSender.trim(),
        recipients: simulationRecipients.trim(),
        subject: simulationSubject,
        filename: simulationFilename.trim(),
        content_type: simulationContentType.trim(),
        size_bytes: simulationSize,
      })

      setSimulation(result)

      if (!result.some(item => item.matched)) {
        setNotice('Ingen aktiv regel matchade testbilagan.')
      }
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Simuleringen misslyckades.',
      )
    } finally {
      setSimulating(false)
    }
  }

  async function removeRule(rule: AttachmentRule) {
    if (!window.confirm(`Ta bort regeln "${rule.name}"?`)) {
      return
    }

    setDeletingId(rule.id)
    setError('')
    setNotice('')

    try {
      await deleteRule(rule.id)
      setNotice(`Regeln "${rule.name}" togs bort.`)
      await reload()
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'Regeln kunde inte tas bort.',
      )
    } finally {
      setDeletingId('')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Mail Attachment Hub</p>
          <h1>Regler</h1>
        </div>
        <Link className="button-link secondary" to="/">
          Till översikten
        </Link>
      </header>

      <main className="content two-column">
        <section className="panel">
          <p className="eyebrow">Regelbyggare</p>
          <h2>Skapa bilageregel</h2>
          <p className="muted">
            Filterfälten använder reguljära uttryck. Tomma filter matchar allt.
          </p>

          {error && <div className="alert" role="alert">{error}</div>}
          {notice && <div className="success">{notice}</div>}

          {!destinations.length && !loading && (
            <div className="alert">
              Ingen lagringsdestination finns.{' '}
              <Link to="/storage">Skapa en destination först.</Link>
            </div>
          )}

          <form onSubmit={submit}>
            <label>Namn</label>
            <input
              required
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
            />

            <label>E-postkonto</label>
            <select
              value={form.email_account_id}
              onChange={e =>
                setForm({ ...form, email_account_id: e.target.value })
              }
            >
              <option value="">Alla konton</option>
              {accounts.map(account => (
                <option key={account.id} value={account.id}>
                  {account.name} · {account.email_address}
                </option>
              ))}
            </select>

            <div className="form-row">
              <div>
                <label>Prioritet</label>
                <input
                  type="number"
                  min="0"
                  value={form.priority}
                  onChange={e =>
                    setForm({
                      ...form,
                      priority: Number(e.target.value),
                    })
                  }
                />
              </div>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={form.stop_processing}
                  onChange={e =>
                    setForm({
                      ...form,
                      stop_processing: e.target.checked,
                    })
                  }
                />
                Stoppa efter match
              </label>
            </div>

            <label>Avsändare</label>
            <input
              value={form.sender_pattern}
              onChange={e =>
                setForm({ ...form, sender_pattern: e.target.value })
              }
              placeholder="@leverantor\.se$"
            />

            <label>Mottagare</label>
            <input
              value={form.recipient_pattern}
              onChange={e =>
                setForm({ ...form, recipient_pattern: e.target.value })
              }
              placeholder="@foretag\.se$"
            />

            <label>Ämne</label>
            <input
              value={form.subject_pattern}
              onChange={e =>
                setForm({ ...form, subject_pattern: e.target.value })
              }
              placeholder="faktura|invoice"
            />

            <label>Filnamn</label>
            <input
              value={form.filename_pattern}
              onChange={e =>
                setForm({ ...form, filename_pattern: e.target.value })
              }
              placeholder="\.pdf$"
            />

            <label>Innehållstyp</label>
            <input
              value={form.content_type_pattern}
              onChange={e =>
                setForm({
                  ...form,
                  content_type_pattern: e.target.value,
                })
              }
              placeholder="application/pdf"
            />

            <div className="form-row">
              <div>
                <label>Minsta storlek (bytes)</label>
                <input
                  type="number"
                  min="0"
                  value={form.min_size_bytes}
                  onChange={e =>
                    setForm({
                      ...form,
                      min_size_bytes: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <label>Största storlek (bytes)</label>
                <input
                  type="number"
                  min="0"
                  value={form.max_size_bytes}
                  onChange={e =>
                    setForm({
                      ...form,
                      max_size_bytes: e.target.value,
                    })
                  }
                />
              </div>
            </div>

            <label>Mappmall</label>
            <input
              required
              value={form.folder_template}
              onChange={e =>
                setForm({ ...form, folder_template: e.target.value })
              }
            />

            <label>Destinationer</label>
            <div className="destination-grid">
              {destinations.map(destination => (
                <label className="checkbox-row" key={destination.id}>
                  <input
                    type="checkbox"
                    checked={form.destination_ids.includes(destination.id)}
                    onChange={e =>
                      setForm({
                        ...form,
                        destination_ids: e.target.checked
                          ? [...form.destination_ids, destination.id]
                          : form.destination_ids.filter(
                              id => id !== destination.id,
                            ),
                      })
                    }
                  />
                  {destination.name}
                </label>
              ))}
            </div>

            <button
              disabled={
                saving ||
                loading ||
                form.destination_ids.length === 0
              }
            >
              {saving ? 'Sparar…' : 'Spara regel'}
            </button>
          </form>

          <div className="simulation">
            <p className="eyebrow">Testdata</p>
            <h3>Simulera regler</h3>
            <p className="muted">
              Kör befintliga aktiva regler mot en testbilaga utan att spara
              eller routa någon fil.
            </p>

            <label>Avsändare</label>
            <input
              value={simulationSender}
              onChange={e => setSimulationSender(e.target.value)}
            />

            <label>Mottagare</label>
            <input
              value={simulationRecipients}
              onChange={e => setSimulationRecipients(e.target.value)}
            />

            <label>Ämne</label>
            <input
              value={simulationSubject}
              onChange={e => setSimulationSubject(e.target.value)}
            />

            <label>Filnamn</label>
            <input
              value={simulationFilename}
              onChange={e => setSimulationFilename(e.target.value)}
            />

            <div className="form-row">
              <div>
                <label>Innehållstyp</label>
                <input
                  value={simulationContentType}
                  onChange={e => setSimulationContentType(e.target.value)}
                />
              </div>
              <div>
                <label>Storlek (bytes)</label>
                <input
                  type="number"
                  min="0"
                  value={simulationSize}
                  onChange={e =>
                    setSimulationSize(Number(e.target.value))
                  }
                />
              </div>
            </div>

            <button
              type="button"
              className="secondary"
              disabled={simulating || !accounts.length}
              onClick={() => void simulate()}
            >
              {simulating ? 'Simulerar…' : 'Simulera aktiva regler'}
            </button>

            {simulation.length > 0 && (
              <div className="simulation-results">
                <h3>Simuleringsresultat</h3>
                {simulation.map(result => (
                  <div
                    key={result.rule_id}
                    className={
                      result.matched
                        ? 'simulation-row matched'
                        : 'simulation-row'
                    }
                  >
                    <strong>{result.rule_name}</strong>
                    <span>
                      {result.matched
                        ? `Matchar → ${result.rendered_folder ?? '(rot)'}`
                        : `Matchar inte: ${
                            result.reasons.join(', ') || 'inga detaljer'
                          }`}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Aktiva regler</p>
              <h2>
                {rules.length} regel{rules.length === 1 ? '' : 'er'}
              </h2>
            </div>
            <button
              className="secondary"
              disabled={loading}
              onClick={() => void reload()}
            >
              {loading ? 'Läser…' : 'Uppdatera'}
            </button>
          </div>

          <div className="account-list">
            {!rules.length && !loading && (
              <div className="empty-state">
                Inga regler är skapade ännu.
              </div>
            )}

            {rules.map(rule => (
              <article className="account-card" key={rule.id}>
                <div>
                  <div className="account-title">
                    <h3>{rule.name}</h3>
                    <span
                      className={`status-pill ${
                        rule.is_enabled ? 'ok' : 'pending'
                      }`}
                    >
                      {rule.is_enabled ? 'Aktiv' : 'Inaktiv'}
                    </span>
                  </div>

                  <p>
                    Prioritet {rule.priority} ·{' '}
                    {rule.filename_pattern || 'Alla filer'} →{' '}
                    {rule.folder_template}
                  </p>

                  <p className="muted">
                    {rule.destination_ids.length} destination
                    {rule.destination_ids.length === 1 ? '' : 'er'}
                    {rule.stop_processing ? ' · stoppar efter match' : ''}
                  </p>
                </div>

                <button
                  className="danger"
                  disabled={deletingId === rule.id}
                  onClick={() => void removeRule(rule)}
                >
                  {deletingId === rule.id ? 'Tar bort…' : 'Ta bort'}
                </button>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
