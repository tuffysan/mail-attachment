"""Complete email engine schema.

Revision ID: 0004
Revises: 0003
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.alter_column("email_accounts", "encrypted_password", existing_type=sa.Text(), nullable=True)
    op.add_column("email_accounts", sa.Column("auth_type", sa.String(20), server_default="password", nullable=False))
    op.add_column("email_accounts", sa.Column("oauth_provider", sa.String(20), nullable=True))
    op.add_column("email_accounts", sa.Column("encrypted_refresh_token", sa.Text(), nullable=True))
    op.add_column("email_accounts", sa.Column("encrypted_access_token", sa.Text(), nullable=True))
    op.add_column("email_accounts", sa.Column("access_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("email_accounts", sa.Column("last_uid", sa.Integer(), server_default="0", nullable=False))
    op.add_column("email_accounts", sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("state_hash", sa.String(128), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth_states")),
        sa.UniqueConstraint("state_hash", name=op.f("uq_oauth_states_state_hash")),
    )
    op.create_index(op.f("ix_oauth_states_state_hash"), "oauth_states", ["state_hash"], unique=True)

    op.create_table(
        "mail_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email_account_id", sa.Uuid(), nullable=False),
        sa.Column("mailbox", sa.String(255), nullable=False),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(998), nullable=True),
        sa.Column("sender", sa.String(998), nullable=True),
        sa.Column("recipients", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("raw_size", sa.Integer(), server_default="0", nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(["email_account_id"], ["email_accounts.id"], ondelete="CASCADE", name=op.f("fk_mail_messages_email_account_id_email_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mail_messages")),
        sa.UniqueConstraint("email_account_id", "mailbox", "uid", name="uq_mail_message_account_mailbox_uid"),
    )
    op.create_index(op.f("ix_mail_messages_email_account_id"), "mail_messages", ["email_account_id"], unique=False)
    op.create_index(op.f("ix_mail_messages_message_id"), "mail_messages", ["message_id"], unique=False)
    op.create_index(op.f("ix_mail_messages_content_sha256"), "mail_messages", ["content_sha256"], unique=False)

    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mail_message_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("safe_filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("local_path", sa.Text(), nullable=False),
        sa.Column("archive_parent_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["archive_parent_id"], ["attachments.id"], ondelete="SET NULL", name=op.f("fk_attachments_archive_parent_id_attachments")),
        sa.ForeignKeyConstraint(["mail_message_id"], ["mail_messages.id"], ondelete="CASCADE", name=op.f("fk_attachments_mail_message_id_mail_messages")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attachments")),
        sa.UniqueConstraint("mail_message_id", "sha256", "safe_filename", name="uq_attachment_message_hash_name"),
    )
    op.create_index(op.f("ix_attachments_mail_message_id"), "attachments", ["mail_message_id"], unique=False)
    op.create_index(op.f("ix_attachments_sha256"), "attachments", ["sha256"], unique=False)

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("email_account_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("attempt", sa.Integer(), server_default="1", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("messages_seen", sa.Integer(), server_default="0", nullable=False),
        sa.Column("messages_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attachments_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["email_account_id"], ["email_accounts.id"], ondelete="CASCADE", name=op.f("fk_sync_runs_email_account_id_email_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_runs")),
    )
    op.create_index(op.f("ix_sync_runs_email_account_id"), "sync_runs", ["email_account_id"], unique=False)

    op.create_table(
        "activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(20), server_default="info", nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("email_account_id", sa.Uuid(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["email_account_id"], ["email_accounts.id"], ondelete="SET NULL", name=op.f("fk_activity_events_email_account_id_email_accounts")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_activity_events")),
    )
    op.create_index(op.f("ix_activity_events_event_type"), "activity_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_activity_events_email_account_id"), "activity_events", ["email_account_id"], unique=False)

def downgrade() -> None:
    op.drop_table("activity_events")
    op.drop_table("sync_runs")
    op.drop_table("attachments")
    op.drop_table("mail_messages")
    op.drop_table("oauth_states")
    for name in ["last_sync_at","last_uid","access_token_expires_at","encrypted_access_token","encrypted_refresh_token","oauth_provider","auth_type"]:
        op.drop_column("email_accounts", name)
    op.alter_column("email_accounts", "encrypted_password", existing_type=sa.Text(), nullable=False)
