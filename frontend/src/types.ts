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
  auth_type: 'password' | 'oauth' | string
  oauth_provider: 'google' | 'microsoft' | string | null
  last_test_status: string | null
  last_test_message: string | null
  last_sync_at: string | null
  sync_interval_seconds: number | null
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


export interface EmailAccountConnectionTest {
  host: string
  port: number
  username: string
  password: string
  mailbox: string
  use_ssl: boolean
}



export interface SyncRun {
  id: string
  email_account_id: string
  status: 'running' | 'succeeded' | 'failed' | string
  attempt: number
  started_at: string
  finished_at: string | null
  messages_seen: number
  messages_created: number
  attachments_created: number
  error_message: string | null
}

export interface ManualSyncResponse {
  run_id: string
  status: string
  attempt: number
  messages_seen: number
  messages_created: number
  attachments_created: number
  error_message: string | null
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
  recent_syncs: Array<{
    id: string
    email_account_id: string
    account_name: string
    email_address: string
    status: string
    started_at: string
    finished_at: string | null
    messages_seen: number
    messages_created: number
    attachments_created: number
    error_message: string | null
  }>
  system: {
    cpu_count: number
    load_1m: number | null
    load_5m: number | null
    load_15m: number | null
    memory_total_bytes: number
    memory_available_bytes: number
    memory_used_percent: number
    disk_total_bytes: number
    disk_free_bytes: number
    disk_used_percent: number
    uptime_seconds: number | null
  }
  backups: {
    count: number
    latest_id: string | null
    latest_created_at: string | null
    latest_size_bytes: number
    total_size_bytes: number
    status: string
    message: string | null
  }
}


export interface UpdateStatus {
  state:
    | 'idle'
    | 'unavailable'
    | 'checking'
    | 'up_to_date'
    | 'update_available'
    | 'updating'
    | 'success'
    | 'error'
  installed_commit: string | null
  latest_commit: string | null
  update_available: boolean
  latest_message: string | null
  latest_date: string | null
  checked_at: string | null
  started_at: string | null
  finished_at: string | null
  message: string | null
}


export interface LocalStoragePermissions {
  path: string
  exists: boolean
  uid: number | null
  gid: number | null
  owner: string | null
  group: string | null
  mode: string | null
  writable: boolean
  executable: boolean
}


export interface GoogleOAuthConfig {
  configured: boolean
  client_id: string | null
  client_secret_configured: boolean
  public_base_url: string | null
  redirect_uri: string | null
  google_auth_overview_url: string
  google_clients_url: string
  gmail_api_url: string
}


export interface BackupItem {
  id: string
  created_at: string | null
  size_bytes: number
  database_bytes: number
  attachments_bytes: number
  routed_bytes: number
  has_environment: boolean
  sha256_verified: boolean | null
}

export interface BackupStatus {
  state: 'idle' | 'refreshing' | 'creating' | 'restoring' | 'success' | 'error'
  action: string | null
  backup_id: string | null
  started_at: string | null
  finished_at: string | null
  message: string | null
}

export interface BackupOverview {
  status: BackupStatus
  backups: BackupItem[]
}


export interface AuditLogItem {
  id: string
  action: string
  entity_type: string | null
  entity_id: string | null
  details_json: string | null
  remote_address: string | null
  created_at: string
}
