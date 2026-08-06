from datetime import datetime
from pydantic import BaseModel, Field


class StorageDestinationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: str = Field(default="local", pattern="^[a-z0-9_-]+$")
    base_path: str = Field(default="/data/routed", min_length=1)
    is_enabled: bool = True


class StorageDestinationResponse(BaseModel):
    id: str
    name: str
    provider: str
    base_path: str
    is_enabled: bool


class AttachmentRuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email_account_id: str | None = None
    priority: int = Field(default=100, ge=0, le=100000)
    is_enabled: bool = True
    stop_processing: bool = False
    sender_pattern: str | None = None
    recipient_pattern: str | None = None
    subject_pattern: str | None = None
    filename_pattern: str | None = None
    content_type_pattern: str | None = None
    min_size_bytes: int | None = Field(default=None, ge=0)
    max_size_bytes: int | None = Field(default=None, ge=0)
    folder_template: str = "{year}/{month}/{sender}"
    destination_ids: list[str] = Field(min_length=1)


class AttachmentRuleResponse(BaseModel):
    id: str
    name: str
    email_account_id: str | None
    priority: int
    is_enabled: bool
    stop_processing: bool
    sender_pattern: str | None
    recipient_pattern: str | None
    subject_pattern: str | None
    filename_pattern: str | None
    content_type_pattern: str | None
    min_size_bytes: int | None
    max_size_bytes: int | None
    folder_template: str
    destination_ids: list[str]


class RuleSimulationRequest(BaseModel):
    email_account_id: str
    sender: str = ""
    recipients: str = ""
    subject: str = ""
    filename: str
    content_type: str = "application/octet-stream"
    size_bytes: int = Field(default=0, ge=0)
    sent_at: datetime | None = None


class RuleSimulationResult(BaseModel):
    rule_id: str
    rule_name: str
    matched: bool
    reasons: list[str]
    rendered_folder: str | None = None
    destination_ids: list[str]
