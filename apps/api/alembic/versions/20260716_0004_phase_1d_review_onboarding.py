"""Phase 1D candidate review and onboarding.

Revision ID: 20260716_0004
Revises: 20260715_0003
Create Date: 2026-07-16

Adds admin review support to candidates (interview, onboarding assignment
pointers) and the onboarding / controlled-document / information-request /
e-sign envelope / programmatic-gate tables required by Onboarding
ONB-001..ONB-010 and Review REV-001..REV-006.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_0004"
down_revision: str | None = "20260715_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Candidate review columns (REV-003) ---
    op.add_column("candidates", sa.Column("interview_status", sa.String(32), nullable=True))
    op.add_column("candidates", sa.Column("interview_notes", sa.String(1000), nullable=True))
    op.add_column(
        "candidates",
        sa.Column("interview_recorded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("assigned_onboarding_plan_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidates_assigned_onboarding_plan_id",
        "candidates",
        "onboarding_plans",
        ["assigned_onboarding_plan_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_candidates_assigned_onboarding_plan_id",
        "candidates",
        ["assigned_onboarding_plan_id"],
    )
    op.add_column(
        "candidates",
        sa.Column("assigned_onboarding_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Onboarding task lifecycle fields (ONB-003) ---
    op.drop_constraint(
        "ck_candidate_onboarding_task_status",
        "candidate_onboarding_tasks",
        type_="check",
    )
    op.create_check_constraint(
        "ck_candidate_onboarding_task_status",
        "candidate_onboarding_tasks",
        "status IN ('required', 'in_progress', 'submitted', 'completed', 'rejected')",
    )
    op.add_column(
        "candidate_onboarding_tasks",
        sa.Column("completed_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidate_onboarding_tasks_completed_by_user_id",
        "candidate_onboarding_tasks",
        "users",
        ["completed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "candidate_onboarding_tasks",
        sa.Column("evidence", sa.String(2000), nullable=True),
    )
    op.add_column(
        "candidate_onboarding_tasks",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidate_onboarding_tasks",
        sa.Column("review_notes", sa.String(1000), nullable=True),
    )

    # --- Controlled documents acknowledgement flag (ONB-006) ---
    op.add_column(
        "controlled_documents",
        sa.Column(
            "requires_acknowledgement", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
    )

    # --- Assignment of an onboarding plan to a selected candidate (ONB-002) ---
    op.create_table(
        "candidate_onboarding_assignments",
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
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("onboarding_plan_id", sa.Uuid(), nullable=False),
        sa.Column("generation", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            server_default="active",
            nullable=False,
        ),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["onboarding_plan_id"], ["onboarding_plans.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "onboarding_plan_id", "generation"),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'superseded')",
            name="ck_candidate_onboarding_assignment_status",
        ),
    )
    op.create_index(
        "ix_candidate_onboarding_assignments_candidate_plan",
        "candidate_onboarding_assignments",
        ["candidate_id", "onboarding_plan_id", "generation"],
    )

    # --- Information requests (REV-002) ---
    op.create_table(
        "candidate_information_requests",
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
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            server_default="open",
            nullable=False,
        ),
        sa.Column("message", sa.String(2000), nullable=False),
        sa.Column("response", sa.String(2000), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('open', 'responded')",
            name="ck_candidate_information_request_status",
        ),
        sa.Index(
            "ix_candidate_information_requests_candidate_open",
            "candidate_id",
            "created_at",
            "id",
        ),
    )

    # --- External e-sign envelope links (ONB-008), no embedded signature ---
    op.create_table(
        "candidate_esign_envelopes",
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
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("document_version_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.String(32),
            server_default="sent",
            nullable=False,
        ),
        sa.Column("envelope_id", sa.String(255), nullable=True),
        sa.Column("envelope_url", sa.String(2048), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "status IN ('sent', 'viewed', 'completed', 'voided')",
            name="ck_candidate_esign_envelope_status",
        ),
        sa.Index(
            "ix_candidate_esign_envelopes_candidate",
            "candidate_id",
            "created_at",
            "id",
        ),
    )

    # --- Programmatic activation gates (ONB-009) ---
    op.create_table(
        "programmatic_gates",
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
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column(
            "status",
            sa.String(32),
            server_default="open",
            nullable=False,
        ),
        sa.Column("satisfied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("satisfied_by_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["satisfied_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "code"),
        sa.CheckConstraint(
            "status IN ('open', 'satisfied')",
            name="ck_programmatic_gate_status",
        ),
        sa.Index(
            "ix_programmatic_gates_candidate",
            "candidate_id",
            "created_at",
            "id",
        ),
    )


def downgrade() -> None:
    op.drop_index("ix_programmatic_gates_candidate", table_name="programmatic_gates")
    op.drop_constraint("ck_programmatic_gate_status", "programmatic_gates", type_="check")
    op.drop_table("programmatic_gates")

    op.drop_index("ix_candidate_esign_envelopes_candidate", table_name="candidate_esign_envelopes")
    op.drop_constraint(
        "ck_candidate_esign_envelope_status", "candidate_esign_envelopes", type_="check"
    )
    op.drop_table("candidate_esign_envelopes")

    op.drop_index(
        "ix_candidate_information_requests_candidate_open",
        table_name="candidate_information_requests",
    )
    op.drop_constraint(
        "ck_candidate_information_request_status",
        "candidate_information_requests",
        type_="check",
    )
    op.drop_table("candidate_information_requests")

    op.drop_index(
        "ix_candidate_onboarding_assignments_candidate_plan",
        table_name="candidate_onboarding_assignments",
    )
    op.drop_constraint(
        "ck_candidate_onboarding_assignment_status",
        "candidate_onboarding_assignments",
        type_="check",
    )
    op.drop_table("candidate_onboarding_assignments")

    op.drop_column("controlled_documents", "requires_acknowledgement")

    op.drop_column("candidate_onboarding_tasks", "review_notes")
    op.drop_column("candidate_onboarding_tasks", "reviewed_at")
    op.drop_column("candidate_onboarding_tasks", "evidence")
    op.drop_constraint(
        "fk_candidate_onboarding_tasks_completed_by_user_id",
        "candidate_onboarding_tasks",
        type_="foreignkey",
    )
    op.drop_column("candidate_onboarding_tasks", "completed_by_user_id")
    op.drop_constraint(
        "ck_candidate_onboarding_task_status",
        "candidate_onboarding_tasks",
        type_="check",
    )
    op.create_check_constraint(
        "ck_candidate_onboarding_task_status",
        "candidate_onboarding_tasks",
        "status IN ('required', 'available', 'viewed', 'acknowledged', "
        "'sent_for_signature', 'signed', 'uploaded', 'accepted', 'rejected', "
        "'expired', 'superseded')",
    )

    op.drop_index("ix_candidates_assigned_onboarding_plan_id", table_name="candidates")
    op.drop_constraint(
        "fk_candidates_assigned_onboarding_plan_id",
        "candidates",
        type_="foreignkey",
    )
    op.drop_column("candidates", "assigned_onboarding_at")
    op.drop_column("candidates", "assigned_onboarding_plan_id")
    op.drop_column("candidates", "interview_recorded_at")
    op.drop_column("candidates", "interview_notes")
    op.drop_column("candidates", "interview_status")
