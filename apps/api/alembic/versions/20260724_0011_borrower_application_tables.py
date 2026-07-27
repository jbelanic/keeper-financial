"""add borrower application tables and indexes

Revision ID: 20260724_0011
Revises: 20260722_0010
Create Date: 2026-07-24
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0011"
down_revision: str | None = "20260722_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "borrower_applications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("capability_digest", sa.Text(), unique=True, index=True),
        sa.Column("capability_session_id", sa.Uuid(), nullable=False),
        sa.Column("capability_revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "lifecycle_status",
            sa.String(32),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload_revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "last_activity_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("draft_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retention_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "assigned_agent_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attribution_source", sa.String(32), nullable=True),
        sa.Column("attribution_agent_slug", sa.String(128), nullable=True),
        sa.Column("attribution_resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "submission_coordination_state",
            sa.String(32),
            nullable=False,
            server_default="idle",
        ),
        sa.CheckConstraint(
            "lifecycle_status IN ('draft', 'submitted', 'under_review', 'completed', 'withdrawn', 'expired')",
            name="ck_borrower_application_lifecycle_status",
        ),
        sa.CheckConstraint(
            "revision >= 0",
            name="ck_borrower_application_revision_non_negative",
        ),
        sa.CheckConstraint(
            "payload_revision >= 0",
            name="ck_borrower_application_payload_revision_non_negative",
        ),
    )
    op.create_index(
        "ix_borrower_applications_lifecycle_status",
        "borrower_applications",
        ["lifecycle_status"],
    )
    op.create_index(
        "ix_borrower_applications_assigned_agent_id",
        "borrower_applications",
        ["assigned_agent_id"],
    )

    op.create_table(
        "borrower_application_payloads",
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
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(32), nullable=False),
        sa.Column("key_id", sa.String(64), nullable=False),
        sa.Column("nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("has_sin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("has_co_borrower", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("encrypted_sin_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("encrypted_sin_nonce", sa.LargeBinary(12), nullable=True),
        sa.UniqueConstraint("application_id", "revision", name="uq_borrower_payload_app_revision"),
        sa.CheckConstraint(
            "revision > 0",
            name="ck_borrower_payload_revision_positive",
        ),
        sa.CheckConstraint(
            "octet_length(nonce) = 12",
            name="ck_borrower_payload_nonce_length",
        ),
    )
    op.create_index(
        "ix_borrower_application_payloads_application_id",
        "borrower_application_payloads",
        ["application_id"],
    )

    op.create_table(
        "borrower_application_status_history",
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
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_source", sa.String(32), nullable=False),
        sa.Column("reason_category", sa.String(64), nullable=True),
        sa.Column("reason_detail", sa.String(512), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("capability_session_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_borrower_status_history_application_id",
        "borrower_application_status_history",
        ["application_id"],
    )

    op.create_table(
        "borrower_assignment_history",
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
        sa.Column("agent_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("actor_source", sa.String(32), nullable=False),
        sa.Column("reason_category", sa.String(64), nullable=False),
        sa.Column("reason_detail", sa.String(512), nullable=True),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_borrower_assignment_history_application_id",
        "borrower_assignment_history",
        ["application_id"],
    )

    op.create_table(
        "borrower_consent_records",
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
        sa.Column("submission_revision", sa.Integer(), nullable=False),
        sa.Column("consent_version", sa.String(128), nullable=False),
        sa.Column("wording_digest", sa.String(128), nullable=False),
        sa.Column("borrower_coverage", sa.String(32), nullable=False),
        sa.Column("borrower_count", sa.Integer(), nullable=False),
        sa.Column("capture_source", sa.String(64), nullable=False),
        sa.Column("capability_session_id", sa.Uuid(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_borrower_consent_records_application_id",
        "borrower_consent_records",
        ["application_id"],
    )

    op.create_table(
        "borrower_application_snapshots",
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
        sa.Column("submission_revision", sa.Integer(), nullable=False),
        sa.Column("key_id", sa.String(64), nullable=False),
        sa.Column("nonce", sa.LargeBinary(12), nullable=False),
        sa.Column("ciphertext_hash", sa.String(128), nullable=False),
        sa.Column("plaintext_hash", sa.String(128), nullable=False),
        sa.Column("object_key", sa.String(256), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
    )
    op.create_index(
        "ix_borrower_application_snapshots_application_id",
        "borrower_application_snapshots",
        ["application_id"],
        unique=True,
    )

    op.create_table(
        "borrower_legal_holds",
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
        sa.Column("placed_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "placed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("released_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason_category", sa.String(64), nullable=False),
        sa.Column("reason_detail", sa.String(512), nullable=True),
    )
    op.create_index(
        "ix_borrower_legal_holds_application_id",
        "borrower_legal_holds",
        ["application_id"],
    )

    op.create_table(
        "borrower_sin_reveal_audit",
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
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("actor_role", sa.String(32), nullable=False),
        sa.Column("assurance_level", sa.String(8), nullable=False),
        sa.Column("selector", sa.String(32), nullable=False),
        sa.Column("reason_category", sa.String(64), nullable=False),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("safe_reason_code", sa.String(64), nullable=False),
    )
    op.create_index(
        "ix_borrower_sin_reveal_audit_application_id",
        "borrower_sin_reveal_audit",
        ["application_id"],
    )


def downgrade() -> None:
    op.drop_table("borrower_sin_reveal_audit")
    op.drop_table("borrower_legal_holds")
    op.drop_table("borrower_application_snapshots")
    op.drop_table("borrower_consent_records")
    op.drop_table("borrower_assignment_history")
    op.drop_table("borrower_application_status_history")
    op.drop_table("borrower_application_payloads")
    op.drop_table("borrower_applications")
