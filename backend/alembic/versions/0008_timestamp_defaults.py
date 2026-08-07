"""Align timestamp defaults with TimestampMixin.

Revision ID: 0008
Revises: 0007

The ORM TimestampMixin declares server_default=now() for created_at and
updated_at, but several historical migrations created those columns without
PostgreSQL defaults. SQLAlchemy therefore omitted the columns on INSERT while
PostgreSQL rejected the row with NOT NULL violations.

This migration repairs existing databases. Historical migrations are also
updated in Commit 002F so fresh installations are correct from the beginning.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TIMESTAMP_TABLES = (
    "email_accounts",
    "oauth_states",
    "mail_messages",
    "attachments",
    "sync_runs",
    "activity_events",
    "storage_destinations",
    "attachment_rules",
    "rule_destinations",
    "rule_executions",
    "api_keys",
    "notification_endpoints",
    "audit_logs",
)


def upgrade() -> None:
    for table_name in _TIMESTAMP_TABLES:
        op.alter_column(
            table_name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        )
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        )


def downgrade() -> None:
    for table_name in reversed(_TIMESTAMP_TABLES):
        op.alter_column(
            table_name,
            "updated_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=None,
        )
        op.alter_column(
            table_name,
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=None,
        )
