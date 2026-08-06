import type { ConnectionTestResponse, EmailAccount, EmailAccountCreate, ReadyResponse, TokenResponse, User } from './types'

const TOKEN_KEY = 'mailhub_access_token'

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem(TOKEN_KEY)
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let detail = 'Begäran misslyckades.'
    try {
      const body = (await response.json()) as { detail?: string }
      if (body.detail) detail = body.detail
    } catch {
      // Keep the generic message when the server did not return JSON.
    }
    throw new ApiError(detail, response.status)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY)
}

export function hasToken(): boolean {
  return Boolean(sessionStorage.getItem(TOKEN_KEY))
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getCurrentUser(): Promise<User> {
  return request<User>('/api/v1/auth/me')
}

export function getReadiness(): Promise<ReadyResponse> {
  return request<ReadyResponse>('/health/ready')
}


export function listEmailAccounts(): Promise<EmailAccount[]> {
  return request<EmailAccount[]>('/api/v1/email-accounts')
}

export function createEmailAccount(payload: EmailAccountCreate): Promise<EmailAccount> {
  return request<EmailAccount>('/api/v1/email-accounts', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteEmailAccount(id: string): Promise<void> {
  return request<void>(`/api/v1/email-accounts/${id}`, { method: 'DELETE' })
}

export function testEmailAccount(id: string): Promise<ConnectionTestResponse> {
  return request<ConnectionTestResponse>(`/api/v1/email-accounts/${id}/test`, { method: 'POST' })
}

export function syncEmailAccount(id: string): Promise<{status:string;messages_created:number;attachments_created:number}> {
  return request(`/api/v1/email-accounts/${id}/sync`, { method: 'POST' })
}

export function startOAuth(provider: 'google' | 'microsoft'): Promise<{authorization_url:string}> {
  return request(`/api/v1/oauth/${provider}/start`)
}

export function listActivity(): Promise<Array<{id:string;level:string;event_type:string;message:string;created_at:string}>> {
  return request('/api/v1/activity')
}
