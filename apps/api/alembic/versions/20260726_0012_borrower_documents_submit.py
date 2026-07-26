"""add borrower documents and consent catalog

Revision ID: 20260726_0012
Revises: 20260724_0011
Create Date: 2026-07-26
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "20260726_0012"
down_revision = "20260724_0011"
branch_labels = None
depends_on = None

PLACEHOLDER_WORDING = "[PLACEHOLDER — owner legal to replace]"
PLACEHOLDER_DIGEST = hashlib.sha256(PLACEHOLDER_WORDING.encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.create_table(
        "borrower_consent_catalog",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("consent_version", sa.String(128), nullable=False),
        sa.Column("wording_digest", sa.String(128), nullable=False),
        sa.Column("wording_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "consent_version",
            "wording_digest",
            name="uq_borrower_consent_catalog_version_digest",
        ),
    )
    op.create_index(
        "ix_borrower_consent_catalog_active",
        "borrower_consent_catalog",
        ["consent_version", "is_active"],
    )
    op.bulk_insert(
        sa.table(
            "borrower_consent_catalog",
            sa.column("id", sa.Uuid()),
            sa.column("consent_version", sa.String()),
            sa.column("wording_digest", sa.String()),
            sa.column("wording_text", sa.Text()),
            sa.column("is_active", sa.Boolean()),
            sa.column("effective_from", sa.DateTime(timezone=True)),
        ),
        [
            {
                "id": uuid.uuid4(),
                "consent_version": "v1-draft",
                "wording_digest": PLACEHOLDER_DIGEST,
                "wording_text": PLACEHOLDER_WORDING,
                "is_active": True,
                "effective_from": datetime.now(UTC),
            }
        ],
    )

    op.create_table(
        "borrower_documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "application_id",
            sa.Uuid(),
            sa.ForeignKey("borrower_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("minio_object_key", sa.String(256), nullable=False, unique=True),
        sa.Column("encryption_key_id", sa.String(64), nullable=False),
        sa.Column("encryption_nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("scan_status", sa.String(32), nullable=False),
        sa.Column("scan_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("uploaded_by", sa.String(32), nullable=False),
        sa.Column("capability_session_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("size_bytes > 0", name="ck_borrower_document_size_positive"),
        sa.CheckConstraint("scan_status IN ('clean')", name="ck_borrower_document_scan_status"),
        sa.CheckConstraint("uploaded_by IN ('borrower')", name="ck_borrower_document_uploaded_by"),
        sa.CheckConstraint(
            "octet_length(encryption_nonce) = 12", name="ck_borrower_document_nonce_length"
        ),
    )
    op.create_index(
        "ix_borrower_documents_application_id",
        "borrower_documents",
        ["application_id"],
    )
    op.create_index(
        "ix_borrower_documents_capability_session_id",
        "borrower_documents",
        ["capability_session_id"],
    )

    op.add_column(
        "borrower_application_snapshots",
        sa.Column("payload_revision", sa.Integer(), nullable=True),
    )
    op.add_column(
        "borrower_application_snapshots",
        sa.Column("schema_version", sa.String(32), nullable=True),
    )
    op.add_column(
        "borrower_application_snapshots",
        sa.Column("ciphertext", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "borrower_application_snapshots",
        sa.Column("consent_record_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_borrower_snapshot_consent_record",
        "borrower_application_snapshots",
        "borrower_consent_records",
        ["consent_record_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_borrower_application_snapshots_consent_record_id",
        "borrower_application_snapshots",
        ["consent_record_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_borrower_application_snapshots_consent_record_id",
        "borrower_application_snapshots",
        type_="unique",
    )
    op.drop_constraint(
        "fk_borrower_snapshot_consent_record",
        "borrower_application_snapshots",
        type_="foreignkey",
    )
    op.drop_column("borrower_application_snapshots", "consent_record_id")
    op.drop_column("borrower_application_snapshots", "ciphertext")
    op.drop_column("borrower_application_snapshots", "schema_version")
    op.drop_column("borrower_application_snapshots", "payload_revision")
    op.drop_index("ix_borrower_documents_capability_session_id", table_name="borrower_documents")
    op.drop_index("ix_borrower_documents_application_id", table_name="borrower_documents")
    op.drop_table("borrower_documents")
    op.drop_index("ix_borrower_consent_catalog_active", table_name="borrower_consent_catalog")
    op.drop_table("borrower_consent_catalog")
