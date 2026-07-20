"""assignment-bound operator evidence and durable public slugs

Revision ID: 20260719_0008
Revises: 20260718_0007
Create Date: 2026-07-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_0008"
down_revision: str | None = "20260718_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    duplicate_legacy_envelope = op.get_bind().scalar(
        sa.text(
            """
            SELECT 1
            FROM candidate_esign_envelopes
            WHERE envelope_id IS NOT NULL
            GROUP BY envelope_id
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    )
    if duplicate_legacy_envelope is not None:
        raise RuntimeError(
            "duplicate legacy e-sign envelope identifiers require owner-reviewed remediation"
        )

    # Preserve candidate-scoped legacy rows without guessing an assignment. New
    # runtime evidence always supplies assignment_id and ignores NULL legacy rows.
    op.add_column(
        "programmatic_gates",
        sa.Column("assignment_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_programmatic_gates_assignment_id",
        "programmatic_gates",
        "candidate_onboarding_assignments",
        ["assignment_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "programmatic_gates_candidate_id_code_key",
        "programmatic_gates",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_programmatic_gates_assignment_code",
        "programmatic_gates",
        ["assignment_id", "code"],
    )
    op.create_index(
        "ix_programmatic_gates_assignment",
        "programmatic_gates",
        ["assignment_id", "created_at", "id"],
    )

    op.create_table(
        "gate_evidence_events",
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
        sa.Column("gate_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("verified_on", sa.Date(), nullable=True),
        sa.Column("evidence_source", sa.String(120), nullable=True),
        sa.Column("evidence_reference", sa.String(160), nullable=True),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["gate_id"], ["programmatic_gates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "event_type IN ('satisfied', 'reopened')",
            name="ck_gate_evidence_event_type",
        ),
    )
    op.create_index(
        "ix_gate_evidence_events_gate",
        "gate_evidence_events",
        ["gate_id", "created_at", "id"],
    )

    op.add_column(
        "candidate_esign_envelopes",
        sa.Column("assignment_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "candidate_esign_envelopes",
        sa.Column(
            "provider",
            sa.String(32),
            server_default="documenso",
            nullable=False,
        ),
    )
    op.add_column(
        "candidate_esign_envelopes",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidate_esign_envelopes",
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidate_esign_envelopes",
        sa.Column("replacement_envelope_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidate_esign_envelopes_assignment_id",
        "candidate_esign_envelopes",
        "candidate_onboarding_assignments",
        ["assignment_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_candidate_esign_envelopes_replacement_id",
        "candidate_esign_envelopes",
        "candidate_esign_envelopes",
        ["replacement_envelope_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "ck_candidate_esign_envelope_status",
        "candidate_esign_envelopes",
        type_="check",
    )
    op.create_check_constraint(
        "ck_candidate_esign_envelope_status",
        "candidate_esign_envelopes",
        "status IN ('sent', 'viewed', 'completed', 'voided', 'rejected')",
    )
    op.create_unique_constraint(
        "uq_esign_provider_envelope",
        "candidate_esign_envelopes",
        ["provider", "envelope_id"],
    )
    op.create_index(
        "ix_candidate_esign_envelopes_assignment",
        "candidate_esign_envelopes",
        ["assignment_id", "created_at", "id"],
    )
    op.create_index(
        "uq_candidate_esign_envelopes_active_assignment",
        "candidate_esign_envelopes",
        ["assignment_id"],
        unique=True,
        postgresql_where=sa.text("assignment_id IS NOT NULL AND superseded_at IS NULL"),
    )

    # New acknowledgements are exact-assignment evidence. NULL legacy assignment
    # rows are retained but cannot satisfy a current assignment.
    op.drop_constraint(
        "policy_acknowledgements_candidate_id_document_version_id_key",
        "policy_acknowledgements",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_policy_acknowledgements_assignment_version",
        "policy_acknowledgements",
        ["assignment_id", "document_version_id"],
    )

    op.add_column(
        "agent_profiles",
        sa.Column("slug_locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Existing profiles that have ever reached publication must retain their
    # public slug even when later suspended or edited back to pending approval.
    op.execute(
        sa.text(
            """
            UPDATE agent_profiles profiles
            SET slug_locked_at = COALESCE(
                profiles.published_at,
                profiles.approved_at,
                (
                    SELECT min(events.created_at)
                    FROM audit_events events
                    WHERE events.event_type = 'agent_profile.published'
                      AND events.target_type = 'agent_profile'
                      AND events.target_id = profiles.id
                ),
                profiles.updated_at
            )
            WHERE profiles.published_at IS NOT NULL
               OR profiles.status IN ('published', 'suspended')
               OR EXISTS (
                    SELECT 1
                    FROM audit_events events
                    WHERE events.event_type = 'agent_profile.published'
                      AND events.target_type = 'agent_profile'
                      AND events.target_id = profiles.id
               )
            """
        )
    )


def downgrade() -> None:
    rejected_envelope = op.get_bind().scalar(
        sa.text("SELECT 1 FROM candidate_esign_envelopes WHERE status = 'rejected' LIMIT 1")
    )
    if rejected_envelope is not None:
        raise RuntimeError(
            "rejected e-sign envelope evidence cannot be represented before revision 20260719_0008"
        )

    op.drop_column("agent_profiles", "slug_locked_at")

    # Downgrade can represent only one acknowledgement per candidate/version.
    op.execute(
        sa.text(
            """
            DELETE FROM policy_acknowledgements older
            USING policy_acknowledgements newer
            WHERE older.candidate_id = newer.candidate_id
              AND older.document_version_id = newer.document_version_id
              AND (older.created_at, older.id) > (newer.created_at, newer.id)
            """
        )
    )
    op.drop_constraint(
        "uq_policy_acknowledgements_assignment_version",
        "policy_acknowledgements",
        type_="unique",
    )
    op.create_unique_constraint(
        "policy_acknowledgements_candidate_id_document_version_id_key",
        "policy_acknowledgements",
        ["candidate_id", "document_version_id"],
    )

    op.drop_index(
        "uq_candidate_esign_envelopes_active_assignment",
        table_name="candidate_esign_envelopes",
    )
    op.drop_index(
        "ix_candidate_esign_envelopes_assignment",
        table_name="candidate_esign_envelopes",
    )
    op.drop_constraint(
        "uq_esign_provider_envelope",
        "candidate_esign_envelopes",
        type_="unique",
    )
    op.drop_constraint(
        "ck_candidate_esign_envelope_status",
        "candidate_esign_envelopes",
        type_="check",
    )
    op.create_check_constraint(
        "ck_candidate_esign_envelope_status",
        "candidate_esign_envelopes",
        "status IN ('sent', 'viewed', 'completed', 'voided')",
    )
    op.drop_constraint(
        "fk_candidate_esign_envelopes_replacement_id",
        "candidate_esign_envelopes",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_candidate_esign_envelopes_assignment_id",
        "candidate_esign_envelopes",
        type_="foreignkey",
    )
    op.drop_column("candidate_esign_envelopes", "replacement_envelope_id")
    op.drop_column("candidate_esign_envelopes", "superseded_at")
    op.drop_column("candidate_esign_envelopes", "last_synced_at")
    op.drop_column("candidate_esign_envelopes", "provider")
    op.drop_column("candidate_esign_envelopes", "assignment_id")

    op.drop_index("ix_gate_evidence_events_gate", table_name="gate_evidence_events")
    op.drop_table("gate_evidence_events")

    # Assignment-specific gates cannot be represented by the legacy candidate
    # uniqueness rule. Remove only new assignment-bound rows during downgrade;
    # NULL legacy records are preserved.
    op.execute(sa.text("DELETE FROM programmatic_gates WHERE assignment_id IS NOT NULL"))
    op.drop_index("ix_programmatic_gates_assignment", table_name="programmatic_gates")
    op.drop_constraint(
        "uq_programmatic_gates_assignment_code",
        "programmatic_gates",
        type_="unique",
    )
    op.create_unique_constraint(
        "programmatic_gates_candidate_id_code_key",
        "programmatic_gates",
        ["candidate_id", "code"],
    )
    op.drop_constraint(
        "fk_programmatic_gates_assignment_id",
        "programmatic_gates",
        type_="foreignkey",
    )
    op.drop_column("programmatic_gates", "assignment_id")
