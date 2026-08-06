from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mailhub.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "system_metadata"
    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class EmailAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "email_accounts"
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email_address: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=993, server_default="993")
    username: Mapped[str] = mapped_column(String(320), nullable=False)
    encrypted_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    mailbox: Mapped[str] = mapped_column(String(255), nullable=False, default="INBOX", server_default="INBOX")
    use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    auth_type: Mapped[str] = mapped_column(String(20), nullable=False, default="password", server_default="password")
    oauth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    encrypted_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_uid: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class OAuthState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "oauth_states"
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MailMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mail_messages"
    email_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mailbox: Mapped[str] = mapped_column(String(255), nullable=False)
    uid: Mapped[int] = mapped_column(Integer, nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(998), nullable=True, index=True)
    sender: Mapped[str | None] = mapped_column(String(998), nullable=True)
    recipients: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class Attachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachments"
    mail_message_id: Mapped[UUID] = mapped_column(
        ForeignKey("mail_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    safe_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    local_path: Mapped[str] = mapped_column(Text, nullable=False)
    archive_parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="SET NULL"), nullable=True
    )


class SyncRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sync_runs"
    email_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    messages_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    attachments_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ActivityEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "activity_events"
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="info", server_default="info")
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    email_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class StorageDestination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "storage_destinations"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="local", server_default="local")
    base_path: Mapped[str] = mapped_column(Text, nullable=False, default="/data/routed", server_default="/data/routed")
    encrypted_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class AttachmentRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachment_rules"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email_account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    stop_processing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    sender_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipient_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    filename_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    folder_template: Mapped[str] = mapped_column(
        Text, nullable=False, default="{year}/{month}/{sender}", server_default="{year}/{month}/{sender}"
    )


class RuleDestination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rule_destinations"

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("attachment_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destination_id: Mapped[UUID] = mapped_column(
        ForeignKey("storage_destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )


class RuleExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rule_executions"

    rule_id: Mapped[UUID] = mapped_column(
        ForeignKey("attachment_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attachment_id: Mapped[UUID] = mapped_column(
        ForeignKey("attachments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destination_id: Mapped[UUID] = mapped_column(
        ForeignKey("storage_destinations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    target_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
