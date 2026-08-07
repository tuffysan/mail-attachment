import type { ReactNode } from 'react'
import { useCallback, useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { ApiError, getSetupStatus } from '../api'

type GuardState = 'loading' | 'ready' | 'setup' | 'error'

export function SetupGuard({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [state, setState] = useState<GuardState>('loading')
  const [message, setMessage] = useState('')

  const check = useCallback(async () => {
    setState('loading')
    setMessage('')

    try {
      const status = await getSetupStatus()
      setState(status.completed ? 'ready' : 'setup')
    } catch (caught) {
      setMessage(
        caught instanceof ApiError
          ? caught.message
          : 'Installationsstatus kunde inte läsas från backend.',
      )
      setState('error')
    }
  }, [])

  useEffect(() => {
    void check()
  }, [check, location.pathname])

  if (state === 'loading') {
    return (
      <main className="login-shell">
        <section className="login-card">
          <p className="eyebrow">Mail Attachment Hub</p>
          <h2>Kontrollerar installationen…</h2>
          <p className="muted">Läser första-start-status från backend.</p>
        </section>
      </main>
    )
  }

  if (state === 'error') {
    return (
      <main className="login-shell">
        <section className="login-card">
          <p className="eyebrow">Backend</p>
          <h2>Installationsstatus kunde inte verifieras</h2>
          <div className="alert" role="alert">{message}</div>
          <p className="muted">
            Av säkerhetsskäl fortsätter gränssnittet inte förrän backend kan
            bekräfta om första-start-guiden är slutförd.
          </p>
          <button onClick={() => void check()}>Försök igen</button>
        </section>
      </main>
    )
  }

  if (state === 'setup' && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />
  }

  return children
}
