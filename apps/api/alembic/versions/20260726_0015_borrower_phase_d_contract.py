"""close the borrower Phase D document metadata contract

Revision ID: 20260726_0015
Revises: 20260726_0014
Create Date: 2026-07-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260726_0015"
down_revision = "20260726_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_document = op.get_bind().scalar(sa.text("SELECT 1 FROM borrower_documents LIMIT 1"))
    if existing_document is not None:
        raise RuntimeError(
            "borrower Phase D contract migration requires an empty borrower_documents "
            "table or owner-reviewed category reconciliation; category provenance "
            "must not be guessed"
        )
    op.add_column(
        "borrower_documents",
        sa.Column("category", sa.String(length=32), nullable=False),
    )
    op.add_column(
        "borrower_documents",
        sa.Column("description", sa.String(length=200), nullable=True),
    )
    op.add_column(
        "borrower_documents",
        sa.Column("deletion_pending_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_borrower_document_category",
        "borrower_documents",
        "category IN ('identification', 'income_employment', "
        "'banking_investment', 'down_payment', 'property', 'tax', "
        "'credit_liability', 'other')",
    )
    op.create_check_constraint(
        "ck_borrower_document_description",
        "borrower_documents",
        "(category = 'other' AND description IS NOT NULL AND length(trim(description)) > 0) "
        "OR (category <> 'other' AND description IS NULL)",
    )
    op.add_column(
        "borrower_consent_catalog",
        sa.Column(
            "real_data_approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("borrower_consent_catalog", "real_data_approved")
    op.drop_constraint(
        "ck_borrower_document_description",
        "borrower_documents",
        type_="check",
    )
    op.drop_constraint(
        "ck_borrower_document_category",
        "borrower_documents",
        type_="check",
    )
    op.drop_column("borrower_documents", "deletion_pending_at")
    op.drop_column("borrower_documents", "description")
    op.drop_column("borrower_documents", "category")
