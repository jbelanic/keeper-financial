"""Resolve the bounded Phase 1F SQLAlchemy/Alembic schema drift.

Revision ID: 20260718_0007
Revises: 20260717_0006
Create Date: 2026-07-18

Preserves the candidate-history ordering indexes already created in Phase 1D,
removes one index duplicated exactly by a unique constraint, and makes three
evidence-retaining delete restrictions explicit. No row data is rewritten.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260718_0007"
down_revision: str | None = "20260717_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TASK_TEMPLATE_FK = "candidate_onboarding_tasks_onboarding_task_id_fkey"
TASK_REVIEWER_FK = "candidate_onboarding_tasks_reviewed_by_user_id_fkey"
ACKNOWLEDGEMENT_VERSION_FK = "policy_acknowledgements_document_version_id_fkey"
REDUNDANT_ASSIGNMENT_INDEX = "ix_candidate_onboarding_assignments_candidate_plan"


def upgrade() -> None:
    # The unique constraint on these same columns already owns a PostgreSQL
    # btree that supports candidate/plan lookup and generation ordering.
    op.drop_index(
        REDUNDANT_ASSIGNMENT_INDEX,
        table_name="candidate_onboarding_assignments",
    )

    op.drop_constraint(
        TASK_TEMPLATE_FK,
        "candidate_onboarding_tasks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        TASK_TEMPLATE_FK,
        "candidate_onboarding_tasks",
        "onboarding_tasks",
        ["onboarding_task_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        TASK_REVIEWER_FK,
        "candidate_onboarding_tasks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        TASK_REVIEWER_FK,
        "candidate_onboarding_tasks",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.drop_constraint(
        ACKNOWLEDGEMENT_VERSION_FK,
        "policy_acknowledgements",
        type_="foreignkey",
    )
    op.create_foreign_key(
        ACKNOWLEDGEMENT_VERSION_FK,
        "policy_acknowledgements",
        "document_versions",
        ["document_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        ACKNOWLEDGEMENT_VERSION_FK,
        "policy_acknowledgements",
        type_="foreignkey",
    )
    op.create_foreign_key(
        ACKNOWLEDGEMENT_VERSION_FK,
        "policy_acknowledgements",
        "document_versions",
        ["document_version_id"],
        ["id"],
    )

    op.drop_constraint(
        TASK_REVIEWER_FK,
        "candidate_onboarding_tasks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        TASK_REVIEWER_FK,
        "candidate_onboarding_tasks",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
    )

    op.drop_constraint(
        TASK_TEMPLATE_FK,
        "candidate_onboarding_tasks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        TASK_TEMPLATE_FK,
        "candidate_onboarding_tasks",
        "onboarding_tasks",
        ["onboarding_task_id"],
        ["id"],
    )

    op.create_index(
        REDUNDANT_ASSIGNMENT_INDEX,
        "candidate_onboarding_assignments",
        ["candidate_id", "onboarding_plan_id", "generation"],
    )
