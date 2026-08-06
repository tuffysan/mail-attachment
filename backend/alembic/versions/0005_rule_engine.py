"""Add storage destinations and attachment rules.

Revision ID: 0005
Revises: 0004
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "storage_destinations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("provider", sa.String(40), server_default="local", nullable=False),
        sa.Column("base_path", sa.Text(), server_default="/data/routed", nullable=False),
        sa.Column("encrypted_config", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_storage_destinations")),
        sa.UniqueConstraint("name", name=op.f("uq_storage_destinations_name")),
    )

    op.create_table(
        "attachment_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("email_account_id", sa.Uuid(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("stop_processing", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sender_pattern", sa.Text(), nullable=True),
        sa.Column("recipient_pattern", sa.Text(), nullable=True),
        sa.Column("subject_pattern", sa.Text(), nullable=True),
        sa.Column("filename_pattern", sa.Text(), nullable=True),
        sa.Column("content_type_pattern", sa.Text(), nullable=True),
        sa.Column("min_size_bytes", sa.Integer(), nullable=True),
        sa.Column("max_size_bytes", sa.Integer(), nullable=True),
        sa.Column("folder_template", sa.Text(), server_default="{year}/{month}/{sender}", nullable=False),
        sa.ForeignKeyConstraint(
            ["email_account_id"], ["email_accounts.id"], ondelete="CASCADE",
            name=op.f("fk_attachment_rules_email_account_id_email_accounts")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attachment_rules")),
    )
    op.create_index(op.f("ix_attachment_rules_email_account_id"), "attachment_rules", ["email_account_id"], unique=False)

    op.create_table(
        "rule_destinations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("destination_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["rule_id"], ["attachment_rules.id"], ondelete="CASCADE",
            name=op.f("fk_rule_destinations_rule_id_attachment_rules")
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"], ["storage_destinations.id"], ondelete="CASCADE",
            name=op.f("fk_rule_destinations_destination_id_storage_destinations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rule_destinations")),
        sa.UniqueConstraint("rule_id", "destination_id", name="uq_rule_destination_pair"),
    )
    op.create_index(op.f("ix_rule_destinations_rule_id"), "rule_destinations", ["rule_id"], unique=False)
    op.create_index(op.f("ix_rule_destinations_destination_id"), "rule_destinations", ["destination_id"], unique=False)

    op.create_table(
        "rule_executions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("attachment_id", sa.Uuid(), nullable=False),
        sa.Column("destination_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("target_path", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["rule_id"], ["attachment_rules.id"], ondelete="CASCADE",
            name=op.f("fk_rule_executions_rule_id_attachment_rules")
        ),
        sa.ForeignKeyConstraint(
            ["attachment_id"], ["attachments.id"], ondelete="CASCADE",
            name=op.f("fk_rule_executions_attachment_id_attachments")
        ),
        sa.ForeignKeyConstraint(
            ["destination_id"], ["storage_destinations.id"], ondelete="CASCADE",
            name=op.f("fk_rule_executions_destination_id_storage_destinations")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rule_executions")),
        sa.UniqueConstraint("rule_id", "attachment_id", "destination_id", name="uq_rule_execution_triplet"),
    )
    op.create_index(op.f("ix_rule_executions_rule_id"), "rule_executions", ["rule_id"], unique=False)
    op.create_index(op.f("ix_rule_executions_attachment_id"), "rule_executions", ["attachment_id"], unique=False)
    op.create_index(op.f("ix_rule_executions_destination_id"), "rule_executions", ["destination_id"], unique=False)

    op.execute(
        """
        INSERT INTO storage_destinations
            (id, created_at, updated_at, name, provider, base_path, is_enabled)
        VALUES
            (gen_random_uuid(), now(), now(), 'Local routed files', 'local', '/data/routed', true)
        """
    )


def downgrade() -> None:
    op.drop_table("rule_executions")
    op.drop_table("rule_destinations")
    op.drop_table("attachment_rules")
    op.drop_table("storage_destinations")
