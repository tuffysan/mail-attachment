"""Security hardening: token version.

Revision ID: 0010
Revises: 0009
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
    )

def downgrade() -> None:
    op.drop_column("users", "token_version")
