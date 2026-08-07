from datetime import datetime

from pydantic import BaseModel


class OperationsCounts(BaseModel):
    email_accounts: int
    enabled_email_accounts: int
    messages: int
    attachments: int
    successful_routes: int
    failed_routes: int
    pending_routes: int
    healthy_storage_destinations: int
    failed_storage_destinations: int


class OperationsHealthCheck(BaseModel):
    status: str
    detail: str
    latency_ms: float | None = None


class OperationsWorker(BaseModel):
    name: str
    state: str
    started_at: datetime | None
    heartbeat_at: datetime | None
    last_activity_at: datetime | None
    processed_cycles: int
    failures: int
    last_error: str | None


class OperationsActivity(BaseModel):
    id: str
    level: str
    event_type: str
    message: str
    created_at: datetime


class OperationsFailure(BaseModel):
    id: str
    kind: str
    subject: str
    detail: str
    created_at: datetime


class StorageHealthItem(BaseModel):
    id: str
    name: str
    provider: str
    enabled: bool
    status: str
    message: str | None
    checked_at: datetime | None




class OperationsSystemResources(BaseModel):
    cpu_count: int
    load_1m: float | None
    load_5m: float | None
    load_15m: float | None
    memory_total_bytes: int
    memory_available_bytes: int
    memory_used_percent: float
    disk_total_bytes: int
    disk_free_bytes: int
    disk_used_percent: float
    uptime_seconds: float | None


class OperationsBackupSummary(BaseModel):
    count: int
    latest_id: str | None
    latest_created_at: datetime | None
    latest_size_bytes: int
    total_size_bytes: int
    status: str
    message: str | None


class OperationsRecentSync(BaseModel):
    id: str
    email_account_id: str
    account_name: str
    email_address: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    messages_seen: int
    messages_created: int
    attachments_created: int
    error_message: str | None

class OperationsDashboardResponse(BaseModel):
    generated_at: datetime
    overall_status: str
    counts: OperationsCounts
    health: dict[str, OperationsHealthCheck]
    workers: list[OperationsWorker]
    storage: list[StorageHealthItem]
    recent_activity: list[OperationsActivity]
    recent_failures: list[OperationsFailure]
    recent_syncs: list[OperationsRecentSync]
    system: OperationsSystemResources
    backups: OperationsBackupSummary
