"""configure the existing agent role required by onboarding completion

Revision ID: 20260722_0010
Revises: 20260722_0009
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0010"
down_revision: str | None = "20260722_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Completion grants only this preconfigured role. Configure the role itself
    # without granting it to any user; the AAL2 completion transaction remains
    # the sole authority for the candidate-to-agent role grant.
    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, code, description, created_at, updated_at)
            VALUES (
                '00000000-0000-4000-8000-00000000a001',
                'agent',
                'Agent portal access',
                now(),
                now()
            )
            ON CONFLICT (code) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    # Irreversible configuration repair: the role may receive authorized grants
    # after upgrade, so downgrade must not delete it or those relationships.
    pass
