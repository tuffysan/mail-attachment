import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { getSetupStatus } from '../api'

export function SetupGuard({ children }: { children: ReactNode }) {
  const location = useLocation()
  const [state, setState] = useState<'loading' | 'ready' | 'setup'>('loading')

  useEffect(() => {
    getSetupStatus()
      .then(status => setState(status.completed ? 'ready' : 'setup'))
      .catch(() => setState('ready'))
  }, [location.pathname])

  if (state === 'loading') {
    return <main className="login-shell"><p className="muted">Kontrollerar installationen…</p></main>
  }
  if (state === 'setup' && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />
  }
  return children
}
