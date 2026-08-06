import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '../api'

export function AdminPage() {
  const [stats,setStats]=useState<Record<string,number>>({})
  const [audit,setAudit]=useState<Array<Record<string,unknown>>>([])
  useEffect(()=>{ void Promise.all([
    request<Record<string,number>>('/api/v1/admin/stats'),
    request<Array<Record<string,unknown>>>('/api/v1/admin/audit')
  ]).then(([s,a])=>{setStats(s);setAudit(a)}) },[])
  return <div className="app-shell">
    <header className="topbar"><div><p className="eyebrow">Mail Attachment Hub</p><h1>Administration</h1></div><Link className="button-link secondary" to="/">Till översikten</Link></header>
    <main className="content">
      <section className="status-grid">
        {Object.entries(stats).map(([k,v])=><article className="status-card" key={k}><p className="eyebrow">{k.replaceAll('_',' ')}</p><strong>{v}</strong></article>)}
      </section>
      <section className="panel"><h2>Audit-logg</h2>
        <div className="account-list">{audit.map((x,i)=><div className="account-card" key={i}><code>{String(x.action)}</code><span>{String(x.created_at)}</span></div>)}</div>
      </section>
    </main>
  </div>
}
