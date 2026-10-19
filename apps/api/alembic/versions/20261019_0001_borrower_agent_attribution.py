"""agent referral links and borrower agent attribution

Revision ID: 20261019_0001
Revises: 20260728_0001
Create Date: 2026-10-19

Adds the per-agent referral code that makes an application link self-attributing,
the resolved attribution columns on borrower applications, and the free-text
preferred agent name on lead inquiries.

Attribution is resolved server-side only: the code maps to an eligible agent
account (active user, `agent` role, active candidate relationship), independent of
whether that agent has a published profile. Client-supplied user identifiers are
never accepted.

No data backfill: referral codes are minted lazily when an agent or administrator
first views the link, and at onboarding completion for new agents.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261019_0001"
down_revision = "20260728_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_referral_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_agent_referral_links_code", "agent_referral_links", ["code"])

    op.add_column(
        "borrower_applications",
        sa.Column("attribution_agent_user_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "borrower_applications",
        sa.Column("attribution_referral_link_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_borrower_applications_attribution_agent",
        "borrower_applications",
        "users",
        ["attribution_agent_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_borrower_applications_attribution_link",
        "borrower_applications",
        "agent_referral_links",
        ["attribution_referral_link_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_borrower_applications_attribution_agent_id",
        "borrower_applications",
        ["attribution_agent_user_id"],
    )

    op.add_column(
        "lead_inquiries",
        sa.Column("preferred_agent_name", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lead_inquiries", "preferred_agent_name")

    op.drop_index(
        "ix_borrower_applications_attribution_agent_id", table_name="borrower_applications"
    )
    op.drop_constraint(
        "fk_borrower_applications_attribution_link",
        "borrower_applications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_borrower_applications_attribution_agent",
        "borrower_applications",
        type_="foreignkey",
    )
    op.drop_column("borrower_applications", "attribution_referral_link_id")
    op.drop_column("borrower_applications", "attribution_agent_user_id")

    op.drop_index("ix_agent_referral_links_code", table_name="agent_referral_links")
    op.drop_table("agent_referral_links")
