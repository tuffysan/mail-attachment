"""Create system metadata table.

Revision ID: 0001
Revises: None
Create Date: 2026-08-06
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "system_metadata",
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_system_metadata"),
        sa.UniqueConstraint("key", name="uq_system_metadata_key"),
    )
    op.create_index("ix_system_metadata_key", "system_metadata", ["key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_system_metadata_key", table_name="system_metadata")
    op.drop_table("system_metadata")
