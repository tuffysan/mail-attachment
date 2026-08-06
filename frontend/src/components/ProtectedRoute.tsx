import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { hasToken } from '../api'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  return hasToken() ? children : <Navigate to="/login" replace />
}
