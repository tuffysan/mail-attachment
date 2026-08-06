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

export interface HealthCheck {
  status: string
  detail: string
}

export interface ReadyResponse {
  status: string
  checks: Record<string, HealthCheck>
}

export interface EmailAccount {
  id: string
  name: string
  email_address: string
  host: string
  port: number
  username: string
  mailbox: string
  use_ssl: boolean
  is_enabled: boolean
  last_test_status: string | null
  last_test_message: string | null
  created_at: string
  updated_at: string
}

export interface EmailAccountCreate {
  name: string
  email_address: string
  host: string
  port: number
  username: string
  password: string
  mailbox: string
  use_ssl: boolean
  is_enabled: boolean
}

export interface ConnectionTestResponse {
  status: string
  message: string
  mailbox: string
  message_count: number | null
}
