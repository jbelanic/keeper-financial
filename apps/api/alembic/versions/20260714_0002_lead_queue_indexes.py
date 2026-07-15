"""add lead queue indexes

Revision ID: 20260714_0002
Revises: 20260714_0001
Create Date: 2026-07-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260714_0002"
down_revision: str | None = "20260714_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_lead_inquiries_created_at_id",
        "lead_inquiries",
        ["created_at", "id"],
    )
    op.create_index(
        "ix_lead_inquiries_status_created_at_id",
        "lead_inquiries",
        ["status", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_lead_inquiries_status_created_at_id",
        table_name="lead_inquiries",
    )
    op.drop_index("ix_lead_inquiries_created_at_id", table_name="lead_inquiries")
