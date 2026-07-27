"""Candidate authentication and onboarding completion remediation.

Revision ID: 20260717_0006
Revises: 20260717_0005
Create Date: 2026-07-17

Adds application-specific review/onboarding provenance and exact controlled-
document version assignment without rewriting the issued Phase 1C/1D
migrations. Historical rows whose application relationship cannot be proved
remain nullable and are not eligible for new mutation operations.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0006"
down_revision: str | None = "20260717_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPLICATION_STATUSES = (
    "application_started",
    "application_submitted",
    "under_review",
    "more_information_required",
    "interview",
    "conditionally_selected",
    "declined",
    "withdrawn",
    "onboarding_in_progress",
    "pending_fsra_authorization",
    "pending_system_provisioning",
    "active",
    "suspended",
    "offboarding",
    "offboarded",
)


def upgrade() -> None:
    op.drop_index(
        "uq_candidate_application_nonterminal_posting",
        table_name="candidate_applications",
    )
    op.drop_constraint("ck_candidate_application_status", "candidate_applications", type_="check")
    allowed = ", ".join(f"'{status}'" for status in APPLICATION_STATUSES)
    op.create_check_constraint(
        "ck_candidate_application_status",
        "candidate_applications",
        f"status IN ({allowed})",
    )
    op.create_index(
        "uq_candidate_application_nonterminal_posting",
        "candidate_applications",
        ["candidate_id", "recruitment_posting_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('withdrawn', 'declined')"),
    )

    op.add_column(
        "candidate_applications", sa.Column("interview_status", sa.String(32), nullable=True)
    )
    op.add_column(
        "candidate_applications", sa.Column("interview_notes", sa.String(1000), nullable=True)
    )
    op.add_column(
        "candidate_applications",
        sa.Column("interview_recorded_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "candidate_information_requests",
        sa.Column("application_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidate_information_requests_application_id",
        "candidate_information_requests",
        "candidate_applications",
        ["application_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_candidate_information_requests_application_id",
        "candidate_information_requests",
        ["application_id"],
    )

    op.add_column(
        "candidate_onboarding_assignments",
        sa.Column("application_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidate_onboarding_assignments_application_id",
        "candidate_onboarding_assignments",
        "candidate_applications",
        ["application_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_candidate_onboarding_assignments_application_id",
        "candidate_onboarding_assignments",
        ["application_id"],
    )
    op.create_index(
        "uq_candidate_onboarding_assignment_active_application",
        "candidate_onboarding_assignments",
        ["application_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active' AND application_id IS NOT NULL"),
    )

    op.add_column(
        "candidate_onboarding_tasks", sa.Column("assignment_id", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_candidate_onboarding_tasks_assignment_id",
        "candidate_onboarding_tasks",
        "candidate_onboarding_assignments",
        ["assignment_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_candidate_onboarding_tasks_assignment_id",
        "candidate_onboarding_tasks",
        ["assignment_id"],
    )
    op.drop_constraint(
        "candidate_onboarding_tasks_candidate_id_onboarding_task_id_key",
        "candidate_onboarding_tasks",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_candidate_onboarding_tasks_assignment_task",
        "candidate_onboarding_tasks",
        ["assignment_id", "onboarding_task_id"],
    )

    op.create_table(
        "candidate_onboarding_document_versions",
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
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignment_id"],
            ["candidate_onboarding_assignments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id",
            "document_version_id",
            name="uq_candidate_onboarding_document_version",
        ),
    )
    op.create_index(
        "ix_candidate_onboarding_document_versions_assignment_id",
        "candidate_onboarding_document_versions",
        ["assignment_id"],
    )
    op.create_index(
        "ix_candidate_onboarding_document_versions_document_version_id",
        "candidate_onboarding_document_versions",
        ["document_version_id"],
    )

    op.add_column("policy_acknowledgements", sa.Column("assignment_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_policy_acknowledgements_assignment_id",
        "policy_acknowledgements",
        "candidate_onboarding_assignments",
        ["assignment_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_policy_acknowledgements_assignment_id",
        "policy_acknowledgements",
        ["assignment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_policy_acknowledgements_assignment_id", table_name="policy_acknowledgements")
    op.drop_constraint(
        "fk_policy_acknowledgements_assignment_id",
        "policy_acknowledgements",
        type_="foreignkey",
    )
    op.drop_column("policy_acknowledgements", "assignment_id")

    op.drop_index(
        "ix_candidate_onboarding_document_versions_document_version_id",
        table_name="candidate_onboarding_document_versions",
    )
    op.drop_index(
        "ix_candidate_onboarding_document_versions_assignment_id",
        table_name="candidate_onboarding_document_versions",
    )
    op.drop_table("candidate_onboarding_document_versions")

    op.drop_constraint(
        "uq_candidate_onboarding_tasks_assignment_task",
        "candidate_onboarding_tasks",
        type_="unique",
    )
    op.create_unique_constraint(
        "candidate_onboarding_tasks_candidate_id_onboarding_task_id_key",
        "candidate_onboarding_tasks",
        ["candidate_id", "onboarding_task_id"],
    )
    op.drop_index(
        "ix_candidate_onboarding_tasks_assignment_id",
        table_name="candidate_onboarding_tasks",
    )
    op.drop_constraint(
        "fk_candidate_onboarding_tasks_assignment_id",
        "candidate_onboarding_tasks",
        type_="foreignkey",
    )
    op.drop_column("candidate_onboarding_tasks", "assignment_id")

    op.drop_index(
        "uq_candidate_onboarding_assignment_active_application",
        table_name="candidate_onboarding_assignments",
    )
    op.drop_index(
        "ix_candidate_onboarding_assignments_application_id",
        table_name="candidate_onboarding_assignments",
    )
    op.drop_constraint(
        "fk_candidate_onboarding_assignments_application_id",
        "candidate_onboarding_assignments",
        type_="foreignkey",
    )
    op.drop_column("candidate_onboarding_assignments", "application_id")

    op.drop_index(
        "ix_candidate_information_requests_application_id",
        table_name="candidate_information_requests",
    )
    op.drop_constraint(
        "fk_candidate_information_requests_application_id",
        "candidate_information_requests",
        type_="foreignkey",
    )
    op.drop_column("candidate_information_requests", "application_id")

    op.drop_column("candidate_applications", "interview_recorded_at")
    op.drop_column("candidate_applications", "interview_notes")
    op.drop_column("candidate_applications", "interview_status")
    op.drop_index(
        "uq_candidate_application_nonterminal_posting",
        table_name="candidate_applications",
    )
    op.drop_constraint("ck_candidate_application_status", "candidate_applications", type_="check")
    op.create_check_constraint(
        "ck_candidate_application_status",
        "candidate_applications",
        "status IN ('application_started', 'application_submitted', 'withdrawn', 'declined')",
    )
    op.create_index(
        "uq_candidate_application_nonterminal_posting",
        "candidate_applications",
        ["candidate_id", "recruitment_posting_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('application_started', 'application_submitted')"),
    )
