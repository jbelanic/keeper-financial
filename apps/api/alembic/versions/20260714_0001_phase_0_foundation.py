"""Phase 0 durable foundation models.

Revision ID: 20260714_0001
Revises:
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CANDIDATE_STATUSES = [
    "prospect",
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
]
AGENT_STATUSES = ["draft", "pending_approval", "published", "suspended", "archived"]
DOCUMENT_STATUSES = [
    "required",
    "available",
    "viewed",
    "acknowledged",
    "sent_for_signature",
    "signed",
    "uploaded",
    "accepted",
    "rejected",
    "expired",
    "superseded",
]


def checks(column: str, values: list[str], name: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(
        f"{column} IN ({', '.join(repr(value) for value in values)})",
        name=name,
    )


def identity_columns() -> list[sa.Column[object]]:
    return [
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
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        *identity_columns(),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "user_identities",
        *identity_columns(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_subject", sa.String(255), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider", "provider_subject"),
    )
    op.create_index("ix_user_identities_user_id", "user_identities", ["user_id"])
    op.create_table(
        "roles",
        *identity_columns(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "user_roles",
        *identity_columns(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("granted_by_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id", "role_id"),
    )
    op.create_table(
        "candidates",
        *identity_columns(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(48), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        checks("status", CANDIDATE_STATUSES, "ck_candidate_status"),
    )
    op.create_index("ix_candidates_user_id", "candidates", ["user_id"], unique=True)
    op.create_table(
        "recruitment_postings",
        *identity_columns(),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("summary", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        checks("status", ["draft", "published", "closed", "archived"], "ck_posting_status"),
    )
    op.create_index("ix_recruitment_postings_slug", "recruitment_postings", ["slug"], unique=True)
    op.create_table(
        "candidate_applications",
        *identity_columns(),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("recruitment_posting_id", sa.Uuid(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["recruitment_posting_id"], ["recruitment_postings.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("candidate_id", "revision"),
        checks("state", ["draft", "submitted", "reopened", "withdrawn"], "ck_application_state"),
    )
    op.create_table(
        "candidate_status_history",
        *identity_columns(),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("previous_status", sa.String(48), nullable=True),
        sa.Column("new_status", sa.String(48), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.String(1000), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "onboarding_plans",
        *identity_columns(),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "onboarding_tasks",
        *identity_columns(),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("instructions", sa.String(2000), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["onboarding_plans.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("plan_id", "sequence"),
    )
    op.create_table(
        "candidate_onboarding_tasks",
        *identity_columns(),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("onboarding_task_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["onboarding_task_id"], ["onboarding_tasks.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("candidate_id", "onboarding_task_id"),
        checks("status", DOCUMENT_STATUSES, "ck_candidate_onboarding_task_status"),
    )
    op.create_table(
        "controlled_documents",
        *identity_columns(),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.UniqueConstraint("key"),
    )
    op.create_table(
        "document_versions",
        *identity_columns(),
        sa.Column("controlled_document_id", sa.Uuid(), nullable=False),
        sa.Column("version_label", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(255), nullable=False),
        sa.Column("sha256_digest", sa.String(64), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["controlled_document_id"], ["controlled_documents.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("controlled_document_id", "version_label"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_table(
        "candidate_documents",
        *identity_columns(),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("object_key", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_digest", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("scan_status", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("object_key"),
        checks("status", DOCUMENT_STATUSES, "ck_candidate_document_status"),
    )
    op.create_index("ix_candidate_documents_candidate_id", "candidate_documents", ["candidate_id"])
    op.create_table(
        "policy_acknowledgements",
        *identity_columns(),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("wording", sa.String(1000), nullable=False),
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"]),
        sa.UniqueConstraint("candidate_id", "document_version_id"),
    )
    op.create_table(
        "agent_profiles",
        *identity_columns(),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("licensed_name", sa.String(160), nullable=False),
        sa.Column("approved_title", sa.String(160), nullable=False),
        sa.Column("licence_number", sa.String(80), nullable=False),
        sa.Column("biography", sa.String(3000), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("approved_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id"),
        checks("status", AGENT_STATUSES, "ck_agent_profile_status"),
    )
    op.create_index("ix_agent_profiles_slug", "agent_profiles", ["slug"], unique=True)
    op.create_table(
        "lead_inquiries",
        *identity_columns(),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("telephone", sa.String(32), nullable=False),
        sa.Column("mortgage_objective", sa.String(40), nullable=False),
        sa.Column("preferred_contact_method", sa.String(20), nullable=False),
        sa.Column("preferred_agent_slug", sa.String(100), nullable=True),
        sa.Column("message", sa.String(1000), nullable=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        checks("status", ["new", "assigned", "contacted", "closed"], "ck_lead_status"),
    )
    op.create_table(
        "consent_records",
        *identity_columns(),
        sa.Column("lead_inquiry_id", sa.Uuid(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("purpose", sa.String(80), nullable=False),
        sa.Column("wording_version", sa.String(80), nullable=False),
        sa.Column("privacy_notice_version", sa.String(80), nullable=False),
        sa.Column("capture_source", sa.String(100), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["lead_inquiry_id"], ["lead_inquiries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "lead_inquiry_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_consent_record_subject",
        ),
    )
    op.create_table(
        "audit_events",
        *identity_columns(),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("target_type", sa.String(80), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("safe_metadata", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])


def downgrade() -> None:
    for table in [
        "audit_events",
        "consent_records",
        "lead_inquiries",
        "agent_profiles",
        "policy_acknowledgements",
        "candidate_documents",
        "document_versions",
        "controlled_documents",
        "candidate_onboarding_tasks",
        "onboarding_tasks",
        "onboarding_plans",
        "candidate_status_history",
        "candidate_applications",
        "recruitment_postings",
        "candidates",
        "user_roles",
        "roles",
        "user_identities",
        "users",
    ]:
        op.drop_table(table)
