"""repair derived policy gates for active exact assignments

Revision ID: 20260722_0009
Revises: 20260719_0008
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0009"
down_revision: str | None = "20260719_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # `policy_acknowledgement` is derived from exact assignment evidence. An
    # assignment with no required issued policy versions is satisfied by the
    # same predicate used by the application service: there is no required
    # assigned version lacking an exact-assignment acknowledgement. Repair only
    # active, ownership-consistent assignments; do not rewrite historical rows
    # or create fabricated PolicyAcknowledgement evidence.
    op.execute(
        sa.text(
            """
            UPDATE programmatic_gates AS gate
            SET status = 'satisfied',
                satisfied_at = COALESCE(gate.satisfied_at, now()),
                satisfied_by_user_id = NULL,
                updated_at = now()
            FROM candidate_onboarding_assignments AS assignment
            WHERE gate.assignment_id = assignment.id
              AND gate.candidate_id = assignment.candidate_id
              AND assignment.status = 'active'
              AND gate.code = 'policy_acknowledgement'
              AND gate.status = 'open'
              AND NOT EXISTS (
                  SELECT 1
                  FROM candidate_onboarding_document_versions AS assigned_version
                  JOIN document_versions AS version
                    ON version.id = assigned_version.document_version_id
                  JOIN controlled_documents AS controlled_document
                    ON controlled_document.id = version.controlled_document_id
                  WHERE assigned_version.assignment_id = assignment.id
                    AND controlled_document.requires_acknowledgement IS TRUE
                    AND version.issued_at IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM policy_acknowledgements AS acknowledgement
                        WHERE acknowledgement.assignment_id = assignment.id
                          AND acknowledgement.candidate_id = assignment.candidate_id
                          AND acknowledgement.document_version_id = version.id
                    )
              )
            """
        )
    )


def downgrade() -> None:
    # Irreversible data repair: reopening these gates could erase valid derived
    # state established by acknowledgements recorded after this upgrade.
    pass
