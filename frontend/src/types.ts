export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface User {
  id: string
  email: string
  display_name: string
  is_admin: boolean
  is_active: boolean
}

export interface ReadyResponse {
  status: 'ok' | 'degraded'
  checks: Record<string, { status: 'ok' | 'failed'; detail: string }>
}
