from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class EmailAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email_address: EmailStr
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=993, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)
    mailbox: str = Field(default="INBOX", min_length=1, max_length=255)
    use_ssl: bool = True
    is_enabled: bool = True


class EmailAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email_address: EmailStr | None = None
    host: str | None = Field(default=None, min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = Field(default=None, min_length=1, max_length=320)
    password: str | None = Field(default=None, min_length=1, max_length=1024)
    mailbox: str | None = Field(default=None, min_length=1, max_length=255)
    use_ssl: bool | None = None
    is_enabled: bool | None = None


class EmailAccountResponse(BaseModel):
    id: str
    name: str
    email_address: EmailStr
    host: str
    port: int
    username: str
    mailbox: str
    use_ssl: bool
    is_enabled: bool
    auth_type: str
    oauth_provider: str | None
    last_test_status: str | None
    last_test_message: str | None
    last_sync_at: datetime | None
    sync_interval_seconds: int | None
    created_at: datetime
    updated_at: datetime


class ConnectionTestResponse(BaseModel):
    status: str
    message: str
    mailbox: str
    message_count: int | None = None


class EmailAccountConnectionTestRequest(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=993, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)
    mailbox: str = Field(default="INBOX", min_length=1, max_length=255)
    use_ssl: bool = True


class EmailAccountScheduleUpdate(BaseModel):
    sync_interval_seconds: int | None = Field(
        default=None,
        ge=60,
        le=86400,
        description="Per-account sync interval. Null uses the global worker interval.",
    )
    is_enabled: bool | None = None


class SyncRunResponse(BaseModel):
    id: str
    email_account_id: str
    status: str
    attempt: int
    started_at: datetime
    finished_at: datetime | None
    messages_seen: int
    messages_created: int
    attachments_created: int
    error_message: str | None
