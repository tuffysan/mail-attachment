"""Add storage health state.

Revision ID: 0006
Revises: 0005
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("storage_destinations", sa.Column("last_test_status", sa.String(32), nullable=True))
    op.add_column("storage_destinations", sa.Column("last_test_message", sa.Text(), nullable=True))
    op.add_column("storage_destinations", sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("storage_destinations", "last_test_at")
    op.drop_column("storage_destinations", "last_test_message")
    op.drop_column("storage_destinations", "last_test_status")
