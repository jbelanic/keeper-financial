"""Phase 1E brokerage-controlled agent profiles.

Revision ID: 20260717_0005
Revises: 20260716_0004
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0005"
down_revision: str | None = "20260716_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_profiles",
        sa.Column(
            "languages",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "agent_profiles",
        sa.Column(
            "service_areas",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "agent_profiles",
        sa.Column(
            "specialties",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column("agent_profiles", sa.Column("photo_url", sa.String(2048), nullable=True))
    op.add_column("agent_profiles", sa.Column("photo_alt_text", sa.String(300), nullable=True))
    op.add_column("agent_profiles", sa.Column("public_email", sa.String(320), nullable=True))
    op.add_column("agent_profiles", sa.Column("public_phone", sa.String(32), nullable=True))
    op.add_column(
        "agent_profiles",
        sa.Column(
            "social_links",
            sa.JSON(),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
    )
    op.add_column(
        "agent_profiles",
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.create_index(
        "ix_agent_profiles_publication",
        "agent_profiles",
        ["status", "published_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_profiles_publication", table_name="agent_profiles")
    op.drop_column("agent_profiles", "version")
    op.drop_column("agent_profiles", "social_links")
    op.drop_column("agent_profiles", "public_phone")
    op.drop_column("agent_profiles", "public_email")
    op.drop_column("agent_profiles", "photo_alt_text")
    op.drop_column("agent_profiles", "photo_url")
    op.drop_column("agent_profiles", "specialties")
    op.drop_column("agent_profiles", "service_areas")
    op.drop_column("agent_profiles", "languages")
