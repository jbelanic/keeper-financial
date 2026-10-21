"""lead inquiries owned by an onboarded agent

Revision ID: 20261020_0016
Revises: 20261019_0001
Create Date: 2026-10-20

A lead inquiry now has exactly one owning agent account. The owner is resolved
server-side at capture from an opaque referral code or a published profile slug
(both mapped onto an eligible agent account: active user, `agent` role, active
candidate relationship), or set explicitly by an administrator from the lead
queue. An agent can read only the inquiries assigned to them.

The legacy applicant-supplied `preferred_agent_slug` / `preferred_agent_name`
columns are retained for historical rows and are no longer accepted from
clients; the free-text "are you working with an agent?" field is removed from
the public form (owner decision 53).

No backfill: existing rows keep `assigned_agent_user_id = NULL` and stay in the
administrator queue until an administrator assigns them.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261020_0016"
down_revision = "20261019_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lead_inquiries",
        sa.Column("assigned_agent_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "lead_inquiries",
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "lead_inquiries",
        sa.Column("assigned_by_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "lead_inquiries",
        sa.Column("attribution_source", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "lead_inquiries",
        sa.Column("attributed_referral_link_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lead_inquiries_assigned_agent_user_id",
        "lead_inquiries",
        "users",
        ["assigned_agent_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_lead_inquiries_assigned_by_user_id",
        "lead_inquiries",
        "users",
        ["assigned_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_lead_inquiries_attributed_referral_link_id",
        "lead_inquiries",
        "agent_referral_links",
        ["attributed_referral_link_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_lead_inquiries_agent_created_at_id",
        "lead_inquiries",
        ["assigned_agent_user_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_lead_inquiries_agent_created_at_id", table_name="lead_inquiries")
    op.drop_constraint(
        "fk_lead_inquiries_attributed_referral_link_id",
        "lead_inquiries",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_lead_inquiries_assigned_by_user_id",
        "lead_inquiries",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_lead_inquiries_assigned_agent_user_id",
        "lead_inquiries",
        type_="foreignkey",
    )
    op.drop_column("lead_inquiries", "attributed_referral_link_id")
    op.drop_column("lead_inquiries", "attribution_source")
    op.drop_column("lead_inquiries", "assigned_by_user_id")
    op.drop_column("lead_inquiries", "assigned_at")
    op.drop_column("lead_inquiries", "assigned_agent_user_id")
