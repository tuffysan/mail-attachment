import type { ConnectionTestResponse, EmailAccount, EmailAccountConnectionTest, EmailAccountCreate, ReadyResponse, TokenResponse, User } from './types'

const TOKEN_KEY = 'mailhub_access_token'

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem(TOKEN_KEY)
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body) headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    let detail = 'Begäran misslyckades.'
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string' && body.detail) {
        detail = body.detail
      }
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

export async function getReadiness(): Promise<ReadyResponse> {
  const response = await fetch('/health/ready', {
    headers: {
      Accept: 'application/json',
    },
  })
  if (response.status === 200 || response.status === 503) {
    return (await response.json()) as ReadyResponse
  }
  let detail = 'Statuskontrollen misslyckades.'
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string' && body.detail) {
      detail = body.detail
    }
  } catch {
    // Keep the generic message when the server did not return JSON.
  }
  throw new ApiError(detail, response.status)
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

export function validateEmailAccount(
  payload: EmailAccountConnectionTest,
): Promise<ConnectionTestResponse> {
  return request<ConnectionTestResponse>('/api/v1/email-accounts/validate', {
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

export function syncEmailAccount(id: string) {
  return request<import('./types').ManualSyncResponse>(
    `/api/v1/email-accounts/${id}/sync`,
    { method: 'POST' },
  )
}

export function retryEmailAccountSync(id: string) {
  return request<import('./types').ManualSyncResponse>(
    `/api/v1/email-accounts/${id}/sync/retry`,
    { method: 'POST' },
  )
}

export function listEmailAccountSyncRuns(id: string, limit = 20) {
  return request<import('./types').SyncRun[]>(
    `/api/v1/email-accounts/${id}/sync-runs?limit=${limit}`,
  )
}

export function updateEmailAccountSchedule(
  id: string,
  payload: { sync_interval_seconds: number | null; is_enabled?: boolean },
) {
  return request<import('./types').EmailAccount>(
    `/api/v1/email-accounts/${id}/schedule`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  )
}

export function startOAuth(provider: 'google' | 'microsoft'): Promise<{authorization_url:string}> {
  return request(`/api/v1/oauth/${provider}/start`)
}

export function listActivity(): Promise<Array<{id:string;level:string;event_type:string;message:string;created_at:string}>> {
  return request('/api/v1/activity')
}


export function listStorageDestinations() {
  return request<import('./types').StorageDestination[]>('/api/v1/storage-destinations')
}

export function listRules() {
  return request<import('./types').AttachmentRule[]>('/api/v1/rules')
}

export function createRule(payload: Record<string, unknown>) {
  return request<import('./types').AttachmentRule>('/api/v1/rules', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteRule(id: string) {
  return request<void>(`/api/v1/rules/${id}`, { method: 'DELETE' })
}

export function simulateRules(payload: Record<string, unknown>) {
  return request<import('./types').RuleSimulationResult[]>('/api/v1/rules/simulate', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}


export function listStorageProviders() {
  return request<import('./types').StorageProvider[]>('/api/v1/storage/providers')
}

export function listManagedStorageDestinations() {
  return request<import('./types').StorageDestination[]>('/api/v1/storage/destinations')
}

export function createStorageDestination(payload: Record<string, unknown>) {
  return request<import('./types').StorageDestination>('/api/v1/storage/destinations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteStorageDestination(id: string) {
  return request<void>(`/api/v1/storage/destinations/${id}`, { method: 'DELETE' })
}

export function testStorageDestination(id: string) {
  return request<{status:string;message:string}>(`/api/v1/storage/destinations/${id}/test`, {
    method: 'POST',
  })
}


export function getSetupStatus() {
  return request<import('./types').SetupStatus>('/api/v1/setup/status')
}

export function updateSetupPreferences(payload: {
  display_name: string
  language: string
  timezone: string
}) {
  return request<import('./types').SetupStatus>('/api/v1/setup/preferences', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function changeSetupPassword(payload: {
  current_password: string
  new_password: string
}) {
  return request<void>('/api/v1/setup/password', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function completeSetup() {
  return request<{completed:boolean}>('/api/v1/setup/complete', {
    method: 'POST',
    body: JSON.stringify({
      acknowledge_backup: true,
      acknowledge_secret_storage: true,
    }),
  })
}


export function getOperationsDashboard() {
  return request<import('./types').OperationsDashboard>('/api/v1/operations/dashboard')
}


export function getUpdateStatus() {
  return request<import('./types').UpdateStatus>('/api/v1/admin/update/status')
}

export function checkForUpdates() {
  return request<import('./types').UpdateStatus>('/api/v1/admin/update/check', {
    method: 'POST',
  })
}

export function applyUpdate() {
  return request<import('./types').UpdateStatus>('/api/v1/admin/update/apply', {
    method: 'POST',
  })
}


export function getLocalStoragePermissions(id: string) {
  return request<import('./types').LocalStoragePermissions>(
    `/api/v1/storage/destinations/${id}/permissions`
  )
}

export function updateLocalStoragePermissions(
  id: string,
  payload: { mode: string; recursive: boolean },
) {
  return request<import('./types').LocalStoragePermissions>(
    `/api/v1/storage/destinations/${id}/permissions`,
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  )
}


export function getGoogleOAuthConfig() {
  return request<import('./types').GoogleOAuthConfig>(
    '/api/v1/admin/oauth/google'
  )
}

export function saveGoogleOAuthConfig(payload: {
  client_id: string
  client_secret?: string | null
  public_base_url: string
}) {
  return request<import('./types').GoogleOAuthConfig>(
    '/api/v1/admin/oauth/google',
    {
      method: 'PUT',
      body: JSON.stringify(payload),
    },
  )
}

export function clearGoogleOAuthConfig() {
  return request<void>('/api/v1/admin/oauth/google', {
    method: 'DELETE',
  })
}


export function getBackups() {
  return request<import('./types').BackupOverview>('/api/v1/admin/backups')
}

export function refreshBackups() {
  return request<import('./types').BackupStatus>('/api/v1/admin/backups/refresh', {
    method: 'POST',
  })
}

export function createBackup() {
  return request<import('./types').BackupStatus>('/api/v1/admin/backups', {
    method: 'POST',
  })
}

export function restoreBackup(backupId: string, confirmation: string) {
  return request<import('./types').BackupStatus>('/api/v1/admin/backups/restore', {
    method: 'POST',
    body: JSON.stringify({
      backup_id: backupId,
      confirmation,
    }),
  })
}


export function changePassword(payload: {
  current_password: string
  new_password: string
}) {
  return request<void>('/api/v1/auth/password', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getAuditLog(limit = 100) {
  return request<import('./types').AuditLogItem[]>(
    `/api/v1/auth/audit?limit=${limit}`,
  )
}
