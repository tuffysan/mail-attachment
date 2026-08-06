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


class OperationsDashboardResponse(BaseModel):
    generated_at: datetime
    overall_status: str
    counts: OperationsCounts
    health: dict[str, OperationsHealthCheck]
    workers: list[OperationsWorker]
    storage: list[StorageHealthItem]
    recent_activity: list[OperationsActivity]
    recent_failures: list[OperationsFailure]
