"""Create email_accounts table.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email_address", sa.String(length=320), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), server_default="993", nullable=False),
        sa.Column("username", sa.String(length=320), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("mailbox", sa.String(length=255), server_default="INBOX", nullable=False),
        sa.Column("use_ssl", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_test_status", sa.String(length=32), nullable=True),
        sa.Column("last_test_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_accounts")),
    )
    op.create_index(op.f("ix_email_accounts_email_address"), "email_accounts", ["email_address"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_accounts_email_address"), table_name="email_accounts")
    op.drop_table("email_accounts")
