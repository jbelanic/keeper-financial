"""refuse upgrades with borrower documents lacking encryption provenance

Revision ID: 20260726_0014
Revises: 20260726_0013
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260726_0014"
down_revision = "20260726_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    legacy_document = op.get_bind().scalar(
        sa.text(
            "SELECT 1 FROM borrower_documents WHERE encryption_payload_revision IS NULL LIMIT 1"
        )
    )
    if legacy_document is not None:
        raise RuntimeError(
            "borrower document migration requires owner-reviewed remediation before upgrade; "
            "existing documents lack provable encryption payload revision"
        )


def downgrade() -> None:
    pass
