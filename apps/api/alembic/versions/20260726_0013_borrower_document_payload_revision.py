"""record borrower document encryption payload revision

Revision ID: 20260726_0013
Revises: 20260726_0012
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260726_0013"
down_revision = "20260726_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "borrower_documents",
        sa.Column("encryption_payload_revision", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("borrower_documents", "encryption_payload_revision")
