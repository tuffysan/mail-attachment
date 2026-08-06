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


export interface StorageDestination {
      id: string
      name: string
      provider: string
      base_path: string
      is_enabled: boolean
      configured_fields: string[]
      last_test_status: string | null
      last_test_message: string | null
      last_test_at: string | null
    }

export interface AttachmentRule {
  id: string
  name: string
  email_account_id: string | null
  priority: number
  is_enabled: boolean
  stop_processing: boolean
  sender_pattern: string | null
  recipient_pattern: string | null
  subject_pattern: string | null
  filename_pattern: string | null
  content_type_pattern: string | null
  min_size_bytes: number | null
  max_size_bytes: number | null
  folder_template: string
  destination_ids: string[]
}

export interface RuleSimulationResult {
  rule_id: string
  rule_name: string
  matched: boolean
  reasons: string[]
  rendered_folder: string | null
  destination_ids: string[]
}


export interface StorageProvider {
  key: string
  label: string
  fields: string[]
  secret_fields: string[]
}


export interface SetupStatus {
  completed: boolean
  language: string
  timezone: string
  has_email_account: boolean
  has_storage_destination: boolean
  has_rule: boolean
}


export interface OperationsDashboard {
  generated_at: string
  overall_status: 'ok' | 'degraded'
  counts: {
    email_accounts: number
    enabled_email_accounts: number
    messages: number
    attachments: number
    successful_routes: number
    failed_routes: number
    pending_routes: number
    healthy_storage_destinations: number
    failed_storage_destinations: number
  }
  health: Record<string, {
    status: string
    detail: string
    latency_ms: number | null
  }>
  workers: Array<{
    name: string
    state: string
    started_at: string | null
    heartbeat_at: string | null
    last_activity_at: string | null
    processed_cycles: number
    failures: number
    last_error: string | null
  }>
  storage: Array<{
    id: string
    name: string
    provider: string
    enabled: boolean
    status: string
    message: string | null
    checked_at: string | null
  }>
  recent_activity: Array<{
    id: string
    level: string
    event_type: string
    message: string
    created_at: string
  }>
  recent_failures: Array<{
    id: string
    kind: string
    subject: string
    detail: string
    created_at: string
  }>
}
