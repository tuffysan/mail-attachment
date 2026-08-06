import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ApiError, createRule, deleteRule, listEmailAccounts,
  listRules, listStorageDestinations, simulateRules
} from '../api'
import type {
  AttachmentRule, EmailAccount, RuleSimulationResult, StorageDestination
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

export function RulesPage() {
  const [rules, setRules] = useState<AttachmentRule[]>([])
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [destinations, setDestinations] = useState<StorageDestination[]>([])
  const [form, setForm] = useState(initial)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [simulation, setSimulation] = useState<RuleSimulationResult[]>([])

  async function reload() {
    const [ruleRows, accountRows, destinationRows] = await Promise.all([
      listRules(), listEmailAccounts(), listStorageDestinations()
    ])
    setRules(ruleRows)
    setAccounts(accountRows)
    setDestinations(destinationRows)
    if (form.destination_ids.length === 0 && destinationRows[0]) {
      setForm(current => ({...current, destination_ids: [destinationRows[0].id]}))
    }
  }

  useEffect(() => { void reload().catch(() => setError('Reglerna kunde inte läsas.')) }, [])

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setNotice('')
    try {
      await createRule({
        ...form,
        email_account_id: form.email_account_id || null,
        min_size_bytes: form.min_size_bytes === '' ? null : Number(form.min_size_bytes),
        max_size_bytes: form.max_size_bytes === '' ? null : Number(form.max_size_bytes),
        is_enabled: true,
      })
      setNotice('Regeln sparades.')
      setForm({...initial, destination_ids: destinations[0] ? [destinations[0].id] : []})
      await reload()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Regeln kunde inte sparas.')
    }
  }

  async function simulate() {
    setError('')
    try {
      const result = await simulateRules({
        email_account_id: form.email_account_id || accounts[0]?.id || '',
        sender: 'invoice@example.com',
        recipients: 'accounts@example.com',
        subject: 'Faktura augusti',
        filename: 'invoice-123.pdf',
        content_type: 'application/pdf',
        size_bytes: 250000,
      })
      setSimulation(result)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Simuleringen misslyckades.')
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">Mail Attachment Hub</p><h1>Regler</h1></div>
        <Link className="button-link secondary" to="/">Till översikten</Link>
      </header>
      <main className="content two-column">
        <section className="panel">
          <p className="eyebrow">Regelbyggare</p>
          <h2>Skapa bilageregel</h2>
          <p className="muted">Fälten använder reguljära uttryck. Tomma filter matchar allt.</p>
          {error && <div className="alert">{error}</div>}
          {notice && <div className="success">{notice}</div>}
          <form onSubmit={submit}>
            <label>Namn</label>
            <input required value={form.name} onChange={e => setForm({...form, name:e.target.value})} />

            <label>E-postkonto</label>
            <select value={form.email_account_id} onChange={e => setForm({...form, email_account_id:e.target.value})}>
              <option value="">Alla konton</option>
              {accounts.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select>

            <div className="form-row">
              <div><label>Prioritet</label><input type="number" value={form.priority} onChange={e => setForm({...form, priority:Number(e.target.value)})}/></div>
              <label className="checkbox-row"><input type="checkbox" checked={form.stop_processing} onChange={e => setForm({...form, stop_processing:e.target.checked})}/>Stoppa efter match</label>
            </div>

            <label>Avsändare</label>
            <input value={form.sender_pattern} onChange={e => setForm({...form, sender_pattern:e.target.value})} placeholder="@leverantor\.se$" />
            <label>Ämne</label>
            <input value={form.subject_pattern} onChange={e => setForm({...form, subject_pattern:e.target.value})} placeholder="faktura|invoice" />
            <label>Filnamn</label>
            <input value={form.filename_pattern} onChange={e => setForm({...form, filename_pattern:e.target.value})} placeholder="\.pdf$" />
            <label>Innehållstyp</label>
            <input value={form.content_type_pattern} onChange={e => setForm({...form, content_type_pattern:e.target.value})} placeholder="application/pdf" />

            <label>Mappmall</label>
            <input value={form.folder_template} onChange={e => setForm({...form, folder_template:e.target.value})} />

            <label>Destinationer</label>
            <div className="destination-grid">
              {destinations.map(destination => (
                <label className="checkbox-row" key={destination.id}>
                  <input
                    type="checkbox"
                    checked={form.destination_ids.includes(destination.id)}
                    onChange={e => setForm({
                      ...form,
                      destination_ids: e.target.checked
                        ? [...form.destination_ids, destination.id]
                        : form.destination_ids.filter(id => id !== destination.id)
                    })}
                  />
                  {destination.name}
                </label>
              ))}
            </div>

            <div className="card-actions">
              <button disabled={form.destination_ids.length === 0}>Spara regel</button>
              <button type="button" className="secondary" onClick={simulate}>Simulera exempel</button>
            </div>
          </form>

          {simulation.length > 0 && (
            <div className="simulation">
              <h3>Simuleringsresultat</h3>
              {simulation.map(result => (
                <div key={result.rule_id} className={result.matched ? 'simulation-row matched' : 'simulation-row'}>
                  <strong>{result.rule_name}</strong>
                  <span>{result.matched ? `Matchar → ${result.rendered_folder}` : `Matchar inte: ${result.reasons.join(', ')}`}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section>
          <p className="eyebrow">Aktiva regler</p>
          <h2>{rules.length} regel{rules.length === 1 ? '' : 'er'}</h2>
          <div className="account-list">
            {rules.map(rule => (
              <article className="account-card" key={rule.id}>
                <div>
                  <div className="account-title"><h3>{rule.name}</h3><span className="status-pill ok">Prioritet {rule.priority}</span></div>
                  <p>{rule.filename_pattern || 'Alla filer'} → {rule.folder_template}</p>
                  <p className="muted">{rule.destination_ids.length} destination{rule.destination_ids.length === 1 ? '' : 'er'}</p>
                </div>
                <button className="danger" onClick={async () => { await deleteRule(rule.id); await reload() }}>Ta bort</button>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
