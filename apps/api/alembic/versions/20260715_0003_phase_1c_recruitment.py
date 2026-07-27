"""Phase 1C recruitment postings, applications, and candidate documents.

Revision ID: 20260715_0003
Revises: 20260714_0002
Create Date: 2026-07-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260715_0003"
down_revision: str | None = "20260714_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recruitment_postings",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    for name in [
        "created_by_user_id",
        "updated_by_user_id",
        "published_by_user_id",
        "closed_by_user_id",
        "archived_by_user_id",
    ]:
        op.add_column("recruitment_postings", sa.Column(name, sa.Uuid(), nullable=True))
        op.create_foreign_key(
            f"fk_recruitment_postings_{name}_users",
            "recruitment_postings",
            "users",
            [name],
            ["id"],
        )
    op.add_column(
        "recruitment_postings", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "recruitment_postings", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        "ix_recruitment_postings_publication",
        "recruitment_postings",
        ["status", "published_at", "id"],
    )

    op.drop_constraint(
        "candidate_applications_recruitment_posting_id_fkey",
        "candidate_applications",
        type_="foreignkey",
    )
    op.drop_constraint(
        "candidate_applications_candidate_id_revision_key",
        "candidate_applications",
        type_="unique",
    )
    op.add_column(
        "candidate_applications",
        sa.Column("attempt_number", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column("candidate_applications", sa.Column("source_posting_slug", sa.String(100)))
    op.add_column("candidate_applications", sa.Column("source_posting_title", sa.String(160)))
    op.add_column("candidate_applications", sa.Column("source_posting_version", sa.Integer()))
    op.add_column(
        "candidate_applications",
        sa.Column(
            "schema_version",
            sa.String(80),
            server_default="candidate-application-2026-07-15-v1",
            nullable=False,
        ),
    )
    op.add_column("candidate_applications", sa.Column("status", sa.String(48)))
    op.add_column("candidate_applications", sa.Column("email", sa.String(254)))
    for name, length in [
        ("given_name", 70),
        ("family_name", 70),
        ("preferred_name", 70),
        ("phone", 16),
        ("city", 100),
        ("region", 100),
        ("country_code", 2),
        ("preferred_contact_method", 20),
        ("referral_source", 40),
        ("referral_detail", 120),
        ("interest_statement", 2000),
        ("relevant_experience", 2000),
    ]:
        op.add_column("candidate_applications", sa.Column(name, sa.String(length), nullable=True))
    op.add_column("candidate_applications", sa.Column("available_from", sa.Date(), nullable=True))
    op.add_column(
        "candidate_applications",
        sa.Column("privacy_acknowledged", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "candidate_applications",
        sa.Column(
            "information_accuracy_confirmed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "candidate_applications",
        sa.Column("privacy_disclosure_version", sa.String(80), nullable=True),
    )
    op.add_column(
        "candidate_applications",
        sa.Column("privacy_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "candidate_applications",
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        """
        UPDATE candidate_applications AS application
        SET source_posting_slug = posting.slug,
            source_posting_title = posting.title,
            source_posting_version = 1
        FROM recruitment_postings AS posting
        WHERE application.recruitment_posting_id = posting.id
        """
    )
    op.execute(
        """
        UPDATE candidate_applications AS application
        SET email = app_user.email
        FROM candidates AS candidate
        JOIN users AS app_user ON app_user.id = candidate.user_id
        WHERE application.candidate_id = candidate.id
        """
    )
    op.execute(
        """
        UPDATE candidate_applications
        SET status = CASE
            WHEN state = 'submitted' THEN 'application_submitted'
            WHEN state = 'withdrawn' THEN 'withdrawn'
            ELSE 'application_started'
        END
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM candidate_applications
            WHERE recruitment_posting_id IS NULL
               OR source_posting_slug IS NULL
               OR source_posting_title IS NULL
               OR source_posting_version IS NULL
               OR email IS NULL
          ) THEN
            RAISE EXCEPTION 'Phase 1C cannot invent provenance for a legacy candidate application';
          END IF;
        END $$
        """
    )
    for name in [
        "recruitment_posting_id",
        "source_posting_slug",
        "source_posting_title",
        "source_posting_version",
        "status",
        "email",
    ]:
        op.alter_column("candidate_applications", name, nullable=False)
    op.create_foreign_key(
        "fk_candidate_applications_recruitment_posting_id",
        "candidate_applications",
        "recruitment_postings",
        ["recruitment_posting_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_candidate_application_status",
        "candidate_applications",
        "status IN ('application_started', 'application_submitted', 'withdrawn', 'declined')",
    )
    op.create_unique_constraint(
        "uq_candidate_application_attempt",
        "candidate_applications",
        ["candidate_id", "recruitment_posting_id", "attempt_number"],
    )
    op.create_index(
        "ix_candidate_applications_candidate_created",
        "candidate_applications",
        ["candidate_id", "created_at", "id"],
    )
    op.create_index(
        "ix_candidate_applications_recruitment_posting_id",
        "candidate_applications",
        ["recruitment_posting_id"],
    )
    op.create_index(
        "uq_candidate_application_nonterminal_posting",
        "candidate_applications",
        ["candidate_id", "recruitment_posting_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('application_started', 'application_submitted')"),
    )

    op.create_table(
        "candidate_employment_entries",
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
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("employer_name", sa.String(160), nullable=False),
        sa.Column("role_title", sa.String(160), nullable=False),
        sa.Column("start_month", sa.String(7), nullable=False),
        sa.Column("currently_employed", sa.Boolean(), nullable=False),
        sa.Column("end_month", sa.String(7), nullable=True),
        sa.Column("summary", sa.String(1000), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"], ["candidate_applications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", "position"),
    )
    op.create_index(
        "ix_candidate_employment_entries_application_id",
        "candidate_employment_entries",
        ["application_id"],
    )
    op.create_table(
        "candidate_education_entries",
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
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("institution_name", sa.String(160), nullable=False),
        sa.Column("program_name", sa.String(160), nullable=False),
        sa.Column("completion_year", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"], ["candidate_applications.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", "position"),
    )
    op.create_index(
        "ix_candidate_education_entries_application_id",
        "candidate_education_entries",
        ["application_id"],
    )
    op.add_column("candidate_status_history", sa.Column("application_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_candidate_status_history_application_id",
        "candidate_status_history",
        "candidate_applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_candidate_status_history_application_id",
        "candidate_status_history",
        ["application_id"],
    )

    op.add_column("candidate_documents", sa.Column("application_id", sa.Uuid(), nullable=True))
    op.add_column(
        "candidate_documents",
        sa.Column("category", sa.String(32), server_default="resume", nullable=False),
    )
    op.add_column(
        "candidate_documents", sa.Column("detected_content_type", sa.String(100), nullable=True)
    )
    op.add_column(
        "candidate_documents",
        sa.Column("is_current", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM candidate_documents) THEN
            RAISE EXCEPTION 'Phase 1C cannot invent application linkage or detected MIME for legacy candidate documents';
          END IF;
        END $$
        """
    )
    op.alter_column("candidate_documents", "application_id", nullable=False)
    op.alter_column("candidate_documents", "detected_content_type", nullable=False)
    op.create_foreign_key(
        "fk_candidate_documents_application_id",
        "candidate_documents",
        "candidate_applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_candidate_document_category",
        "candidate_documents",
        "category IN ('resume', 'cover_letter')",
    )
    op.create_index(
        "ix_candidate_documents_application_id", "candidate_documents", ["application_id"]
    )
    op.create_index(
        "ix_candidate_documents_application_category",
        "candidate_documents",
        ["application_id", "category", "created_at"],
    )
    op.execute(
        """
        INSERT INTO roles (id, code, description, created_at, updated_at)
        VALUES ('00000000-0000-4000-8000-00000000c001', 'candidate',
                'Candidate portal access', now(), now())
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_documents_application_category", table_name="candidate_documents")
    op.drop_index("ix_candidate_documents_application_id", table_name="candidate_documents")
    op.drop_constraint("ck_candidate_document_category", "candidate_documents", type_="check")
    op.drop_constraint(
        "fk_candidate_documents_application_id", "candidate_documents", type_="foreignkey"
    )
    for name in ["is_current", "detected_content_type", "category", "application_id"]:
        op.drop_column("candidate_documents", name)
    op.drop_index(
        "ix_candidate_status_history_application_id", table_name="candidate_status_history"
    )
    op.drop_constraint(
        "fk_candidate_status_history_application_id", "candidate_status_history", type_="foreignkey"
    )
    op.drop_column("candidate_status_history", "application_id")
    op.drop_table("candidate_education_entries")
    op.drop_table("candidate_employment_entries")
    op.drop_index(
        "uq_candidate_application_nonterminal_posting", table_name="candidate_applications"
    )
    op.drop_index(
        "ix_candidate_applications_recruitment_posting_id", table_name="candidate_applications"
    )
    op.drop_index(
        "ix_candidate_applications_candidate_created", table_name="candidate_applications"
    )
    op.drop_constraint("uq_candidate_application_attempt", "candidate_applications", type_="unique")
    op.drop_constraint("ck_candidate_application_status", "candidate_applications", type_="check")
    op.drop_constraint(
        "fk_candidate_applications_recruitment_posting_id",
        "candidate_applications",
        type_="foreignkey",
    )
    op.alter_column("candidate_applications", "recruitment_posting_id", nullable=True)
    op.create_foreign_key(
        "candidate_applications_recruitment_posting_id_fkey",
        "candidate_applications",
        "recruitment_postings",
        ["recruitment_posting_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "candidate_applications_candidate_id_revision_key",
        "candidate_applications",
        ["candidate_id", "revision"],
    )
    for name in [
        "withdrawn_at",
        "privacy_acknowledged_at",
        "privacy_disclosure_version",
        "information_accuracy_confirmed",
        "privacy_acknowledged",
        "available_from",
        "relevant_experience",
        "interest_statement",
        "referral_detail",
        "referral_source",
        "preferred_contact_method",
        "country_code",
        "region",
        "city",
        "phone",
        "preferred_name",
        "family_name",
        "given_name",
        "email",
        "status",
        "schema_version",
        "source_posting_version",
        "source_posting_title",
        "source_posting_slug",
        "attempt_number",
    ]:
        op.drop_column("candidate_applications", name)
    op.drop_index("ix_recruitment_postings_publication", table_name="recruitment_postings")
    for name in [
        "archived_by_user_id",
        "closed_by_user_id",
        "published_by_user_id",
        "updated_by_user_id",
        "created_by_user_id",
    ]:
        op.drop_constraint(
            f"fk_recruitment_postings_{name}_users",
            "recruitment_postings",
            type_="foreignkey",
        )
    for name in [
        "archived_at",
        "closed_at",
        "archived_by_user_id",
        "closed_by_user_id",
        "published_by_user_id",
        "updated_by_user_id",
        "created_by_user_id",
        "version",
    ]:
        op.drop_column("recruitment_postings", name)
