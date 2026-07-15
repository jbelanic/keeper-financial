from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from keeper_api.db.base import Base
from keeper_api.models.statuses import AgentProfileStatus, CandidateStatus, DocumentStatus


def status_check(column: str, values: list[str], name: str) -> CheckConstraint:
    allowed = ", ".join(f"'{value}'" for value in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)


class IdTimestampsMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(IdTimestampsMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserIdentity(IdTimestampsMixin, Base):
    __tablename__ = "user_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_subject"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="supabase")
    provider_subject: Mapped[str] = mapped_column(String(255))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Role(IdTimestampsMixin, Base):
    __tablename__ = "roles"

    code: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(255))


class UserRole(IdTimestampsMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class Candidate(IdTimestampsMixin, Base):
    __tablename__ = "candidates"
    __table_args__ = (
        status_check("status", [item.value for item in CandidateStatus], "ck_candidate_status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(48), default=CandidateStatus.PROSPECT.value)


class RecruitmentPosting(IdTimestampsMixin, Base):
    __tablename__ = "recruitment_postings"
    __table_args__ = (
        status_check("status", ["draft", "published", "closed", "archived"], "ck_posting_status"),
    )

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CandidateApplication(IdTimestampsMixin, Base):
    __tablename__ = "candidate_applications"
    __table_args__ = (
        status_check(
            "state", ["draft", "submitted", "reopened", "withdrawn"], "ck_application_state"
        ),
        UniqueConstraint("candidate_id", "revision"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    recruitment_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recruitment_postings.id", ondelete="SET NULL")
    )
    revision: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(20), default="draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CandidateStatusHistory(IdTimestampsMixin, Base):
    __tablename__ = "candidate_status_history"

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    previous_status: Mapped[str | None] = mapped_column(String(48))
    new_status: Mapped[str] = mapped_column(String(48))
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reason: Mapped[str | None] = mapped_column(String(1000))


class OnboardingPlan(IdTimestampsMixin, Base):
    __tablename__ = "onboarding_plans"

    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(1000), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class OnboardingTask(IdTimestampsMixin, Base):
    __tablename__ = "onboarding_tasks"
    __table_args__ = (UniqueConstraint("plan_id", "sequence"),)

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_plans.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(160))
    instructions: Mapped[str] = mapped_column(String(2000), default="")
    sequence: Mapped[int] = mapped_column(Integer)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)


class CandidateOnboardingTask(IdTimestampsMixin, Base):
    __tablename__ = "candidate_onboarding_tasks"
    __table_args__ = (
        status_check(
            "status", [item.value for item in DocumentStatus], "ck_candidate_onboarding_task_status"
        ),
        UniqueConstraint("candidate_id", "onboarding_task_id"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    onboarding_task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("onboarding_tasks.id"))
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.REQUIRED.value)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class ControlledDocument(IdTimestampsMixin, Base):
    __tablename__ = "controlled_documents"

    key: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")


class DocumentVersion(IdTimestampsMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("controlled_document_id", "version_label"),)

    controlled_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("controlled_documents.id", ondelete="CASCADE")
    )
    version_label: Mapped[str] = mapped_column(String(64))
    object_key: Mapped[str] = mapped_column(String(255), unique=True)
    sha256_digest: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CandidateDocument(IdTimestampsMixin, Base):
    __tablename__ = "candidate_documents"
    __table_args__ = (
        status_check(
            "status", [item.value for item in DocumentStatus], "ck_candidate_document_status"
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    object_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256_digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.UPLOADED.value)
    scan_status: Mapped[str] = mapped_column(String(32), default="pending")


class PolicyAcknowledgement(IdTimestampsMixin, Base):
    __tablename__ = "policy_acknowledgements"
    __table_args__ = (UniqueConstraint("candidate_id", "document_version_id"),)

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"))
    wording: Mapped[str] = mapped_column(String(1000))
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AgentProfile(IdTimestampsMixin, Base):
    __tablename__ = "agent_profiles"
    __table_args__ = (
        status_check(
            "status", [item.value for item in AgentProfileStatus], "ck_agent_profile_status"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    licensed_name: Mapped[str] = mapped_column(String(160))
    approved_title: Mapped[str] = mapped_column(String(160))
    licence_number: Mapped[str] = mapped_column(String(80))
    biography: Mapped[str] = mapped_column(String(3000), default="")
    status: Mapped[str] = mapped_column(String(32), default=AgentProfileStatus.DRAFT.value)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeadInquiry(IdTimestampsMixin, Base):
    __tablename__ = "lead_inquiries"
    __table_args__ = (
        status_check("status", ["new", "assigned", "contacted", "closed"], "ck_lead_status"),
        Index("ix_lead_inquiries_created_at_id", "created_at", "id"),
        Index("ix_lead_inquiries_status_created_at_id", "status", "created_at", "id"),
    )

    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(320))
    telephone: Mapped[str] = mapped_column(String(32))
    mortgage_objective: Mapped[str] = mapped_column(String(40))
    preferred_contact_method: Mapped[str] = mapped_column(String(20))
    preferred_agent_slug: Mapped[str | None] = mapped_column(String(100))
    message: Mapped[str | None] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(100), default="website_apply")
    status: Mapped[str] = mapped_column(String(20), default="new")


class ConsentRecord(IdTimestampsMixin, Base):
    __tablename__ = "consent_records"
    __table_args__ = (
        CheckConstraint(
            "lead_inquiry_id IS NOT NULL OR user_id IS NOT NULL",
            name="ck_consent_record_subject",
        ),
    )

    lead_inquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("lead_inquiries.id", ondelete="RESTRICT")
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    purpose: Mapped[str] = mapped_column(String(80))
    wording_version: Mapped[str] = mapped_column(String(80))
    privacy_notice_version: Mapped[str] = mapped_column(String(80))
    capture_source: Mapped[str] = mapped_column(String(100))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(IdTimestampsMixin, Base):
    __tablename__ = "audit_events"

    event_type: Mapped[str] = mapped_column(String(120), index=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    request_id: Mapped[str | None] = mapped_column(String(100))
    safe_metadata: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


__all__ = [
    "AgentProfile",
    "AuditEvent",
    "Candidate",
    "CandidateApplication",
    "CandidateDocument",
    "CandidateOnboardingTask",
    "CandidateStatusHistory",
    "ConsentRecord",
    "ControlledDocument",
    "DocumentVersion",
    "LeadInquiry",
    "OnboardingPlan",
    "OnboardingTask",
    "PolicyAcknowledgement",
    "RecruitmentPosting",
    "Role",
    "User",
    "UserIdentity",
    "UserRole",
]
