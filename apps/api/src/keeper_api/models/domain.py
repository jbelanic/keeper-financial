from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from keeper_api.db.base import Base
from keeper_api.models.statuses import (
    AgentProfileStatus,
    CandidateStatus,
    DocumentStatus,
    EsignEnvelopeStatus,
    GateStatus,
    InformationRequestStatus,
    OnboardingAssignmentStatus,
    OnboardingTaskStatus,
)


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
    # Phase 1D review support
    interview_status: Mapped[str | None] = mapped_column(String(32), default=None)
    interview_notes: Mapped[str | None] = mapped_column(String(1000), default=None)
    interview_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    assigned_onboarding_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("onboarding_plans.id", ondelete="SET NULL"), default=None, index=True
    )
    assigned_onboarding_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class RecruitmentPosting(IdTimestampsMixin, Base):
    __tablename__ = "recruitment_postings"
    __table_args__ = (
        status_check("status", ["draft", "published", "closed", "archived"], "ck_posting_status"),
        Index("ix_recruitment_postings_publication", "status", "published_at", "id"),
    )

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    published_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CandidateApplication(IdTimestampsMixin, Base):
    __tablename__ = "candidate_applications"
    __table_args__ = (
        status_check(
            "state", ["draft", "submitted", "reopened", "withdrawn"], "ck_application_state"
        ),
        status_check(
            "status",
            [item.value for item in CandidateStatus if item != CandidateStatus.PROSPECT],
            "ck_candidate_application_status",
        ),
        UniqueConstraint(
            "candidate_id",
            "recruitment_posting_id",
            "attempt_number",
            name="uq_candidate_application_attempt",
        ),
        Index("ix_candidate_applications_candidate_created", "candidate_id", "created_at", "id"),
        Index(
            "uq_candidate_application_nonterminal_posting",
            "candidate_id",
            "recruitment_posting_id",
            unique=True,
            postgresql_where=text("status NOT IN ('withdrawn', 'declined')"),
            sqlite_where=text("status NOT IN ('withdrawn', 'declined')"),
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    recruitment_posting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recruitment_postings.id", ondelete="RESTRICT"), index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    source_posting_slug: Mapped[str] = mapped_column(String(100))
    source_posting_title: Mapped[str] = mapped_column(String(160))
    source_posting_version: Mapped[int] = mapped_column(Integer)
    schema_version: Mapped[str] = mapped_column(
        String(80), default="candidate-application-2026-07-15-v1"
    )
    revision: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String(20), default="draft")
    status: Mapped[str] = mapped_column(String(48), default="application_started")
    email: Mapped[str] = mapped_column(String(254))
    given_name: Mapped[str | None] = mapped_column(String(70))
    family_name: Mapped[str | None] = mapped_column(String(70))
    preferred_name: Mapped[str | None] = mapped_column(String(70))
    phone: Mapped[str | None] = mapped_column(String(16))
    city: Mapped[str | None] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    country_code: Mapped[str | None] = mapped_column(String(2))
    preferred_contact_method: Mapped[str | None] = mapped_column(String(20))
    available_from: Mapped[date | None] = mapped_column(Date)
    referral_source: Mapped[str | None] = mapped_column(String(40))
    referral_detail: Mapped[str | None] = mapped_column(String(120))
    interest_statement: Mapped[str | None] = mapped_column(String(2000))
    relevant_experience: Mapped[str | None] = mapped_column(String(2000))
    privacy_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    information_accuracy_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    privacy_disclosure_version: Mapped[str | None] = mapped_column(String(80))
    privacy_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interview_status: Mapped[str | None] = mapped_column(String(32), default=None)
    interview_notes: Mapped[str | None] = mapped_column(String(1000), default=None)
    interview_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class CandidateEmploymentEntry(IdTimestampsMixin, Base):
    __tablename__ = "candidate_employment_entries"
    __table_args__ = (UniqueConstraint("application_id", "position"),)

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    employer_name: Mapped[str] = mapped_column(String(160))
    role_title: Mapped[str] = mapped_column(String(160))
    start_month: Mapped[str] = mapped_column(String(7))
    currently_employed: Mapped[bool] = mapped_column(Boolean)
    end_month: Mapped[str | None] = mapped_column(String(7))
    summary: Mapped[str | None] = mapped_column(String(1000))


class CandidateEducationEntry(IdTimestampsMixin, Base):
    __tablename__ = "candidate_education_entries"
    __table_args__ = (UniqueConstraint("application_id", "position"),)

    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    institution_name: Mapped[str] = mapped_column(String(160))
    program_name: Mapped[str] = mapped_column(String(160))
    completion_year: Mapped[int | None] = mapped_column(Integer)


class CandidateStatusHistory(IdTimestampsMixin, Base):
    __tablename__ = "candidate_status_history"

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="CASCADE"), index=True
    )
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

    tasks: Mapped[list[OnboardingTask]] = relationship(
        "OnboardingTask", back_populates="plan", order_by="OnboardingTask.sequence"
    )


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

    plan: Mapped[OnboardingPlan] = relationship("OnboardingPlan", back_populates="tasks")


class CandidateOnboardingTask(IdTimestampsMixin, Base):
    __tablename__ = "candidate_onboarding_tasks"
    __table_args__ = (
        status_check(
            "status",
            [item.value for item in OnboardingTaskStatus],
            "ck_candidate_onboarding_task_status",
        ),
        UniqueConstraint(
            "assignment_id",
            "onboarding_task_id",
            name="uq_candidate_onboarding_tasks_assignment_task",
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("candidate_onboarding_assignments.id", ondelete="CASCADE"),
        index=True,
        default=None,
    )
    onboarding_task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_tasks.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(32), default=OnboardingTaskStatus.REQUIRED.value)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    evidence: Mapped[str | None] = mapped_column(String(2000), default=None)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_notes: Mapped[str | None] = mapped_column(String(1000), default=None)


class CandidateOnboardingAssignment(IdTimestampsMixin, Base):
    __tablename__ = "candidate_onboarding_assignments"
    __table_args__ = (
        status_check(
            "status",
            [item.value for item in OnboardingAssignmentStatus],
            "ck_candidate_onboarding_assignment_status",
        ),
        UniqueConstraint("candidate_id", "onboarding_plan_id", "generation"),
        Index(
            "uq_candidate_onboarding_assignment_active_application",
            "application_id",
            unique=True,
            postgresql_where=text("status = 'active' AND application_id IS NOT NULL"),
            sqlite_where=text("status = 'active' AND application_id IS NOT NULL"),
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="RESTRICT"), index=True, default=None
    )
    onboarding_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_plans.id", ondelete="RESTRICT")
    )
    generation: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default=OnboardingAssignmentStatus.ACTIVE.value)
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class CandidateOnboardingDocumentVersion(IdTimestampsMixin, Base):
    """Exact controlled-document version issued through one assignment."""

    __tablename__ = "candidate_onboarding_document_versions"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "document_version_id",
            name="uq_candidate_onboarding_document_version",
        ),
    )

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_onboarding_assignments.id", ondelete="CASCADE"), index=True
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="RESTRICT"), index=True
    )
    assigned_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class ControlledDocument(IdTimestampsMixin, Base):
    __tablename__ = "controlled_documents"

    key: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, default=True)

    versions: Mapped[list[DocumentVersion]] = relationship(
        "DocumentVersion", back_populates="document", order_by="DocumentVersion.issued_at"
    )


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

    document: Mapped[ControlledDocument] = relationship(
        "ControlledDocument", back_populates="versions"
    )


class CandidateDocument(IdTimestampsMixin, Base):
    __tablename__ = "candidate_documents"
    __table_args__ = (
        status_check(
            "status", [item.value for item in DocumentStatus], "ck_candidate_document_status"
        ),
        status_check("category", ["resume", "cover_letter"], "ck_candidate_document_category"),
        Index(
            "ix_candidate_documents_application_category",
            "application_id",
            "category",
            "created_at",
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(String(32), default="resume")
    object_key: Mapped[str] = mapped_column(String(255), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    detected_content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256_digest: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.UPLOADED.value)
    scan_status: Mapped[str] = mapped_column(String(32), default="pending")
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class PolicyAcknowledgement(IdTimestampsMixin, Base):
    __tablename__ = "policy_acknowledgements"
    __table_args__ = (UniqueConstraint("candidate_id", "document_version_id"),)

    candidate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"))
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("candidate_onboarding_assignments.id", ondelete="RESTRICT"),
        index=True,
        default=None,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_versions.id", ondelete="RESTRICT")
    )
    wording: Mapped[str] = mapped_column(String(1000))
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CandidateInformationRequest(IdTimestampsMixin, Base):
    __tablename__ = "candidate_information_requests"
    __table_args__ = (
        status_check(
            "status",
            [item.value for item in InformationRequestStatus],
            "ck_candidate_information_request_status",
        ),
        Index(
            "ix_candidate_information_requests_candidate_open",
            "candidate_id",
            "created_at",
            "id",
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="RESTRICT"), index=True, default=None
    )
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), default=InformationRequestStatus.OPEN.value)
    message: Mapped[str] = mapped_column(String(2000))
    response: Mapped[str | None] = mapped_column(String(2000), default=None)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CandidateEsignEnvelope(IdTimestampsMixin, Base):
    __tablename__ = "candidate_esign_envelopes"
    __table_args__ = (
        status_check(
            "status",
            [item.value for item in EsignEnvelopeStatus],
            "ck_candidate_esign_envelope_status",
        ),
        Index(
            "ix_candidate_esign_envelopes_candidate",
            "candidate_id",
            "created_at",
            "id",
        ),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_versions.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), default=EsignEnvelopeStatus.SENT.value)
    envelope_id: Mapped[str | None] = mapped_column(String(255), default=None)
    envelope_url: Mapped[str | None] = mapped_column(String(2048), default=None)


class ProgrammaticGate(IdTimestampsMixin, Base):
    __tablename__ = "programmatic_gates"
    __table_args__ = (
        status_check("status", [item.value for item in GateStatus], "ck_programmatic_gate_status"),
        UniqueConstraint("candidate_id", "code"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default=GateStatus.OPEN.value)
    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    satisfied_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class AgentProfile(IdTimestampsMixin, Base):
    __tablename__ = "agent_profiles"
    __table_args__ = (
        status_check(
            "status", [item.value for item in AgentProfileStatus], "ck_agent_profile_status"
        ),
        Index("ix_agent_profiles_publication", "status", "published_at", "id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    licensed_name: Mapped[str] = mapped_column(String(160))
    approved_title: Mapped[str] = mapped_column(String(160))
    licence_number: Mapped[str] = mapped_column(String(80))
    biography: Mapped[str] = mapped_column(String(3000), default="")
    languages: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    service_areas: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    specialties: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    photo_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    photo_alt_text: Mapped[str | None] = mapped_column(String(300), default=None)
    public_email: Mapped[str | None] = mapped_column(String(320), default=None)
    public_phone: Mapped[str | None] = mapped_column(String(32), default=None)
    social_links: Mapped[list[dict[str, str]]] = mapped_column(
        JSON, default=list, server_default="[]"
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
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
    "CandidateEducationEntry",
    "CandidateEmploymentEntry",
    "CandidateEsignEnvelope",
    "CandidateInformationRequest",
    "CandidateOnboardingAssignment",
    "CandidateOnboardingTask",
    "CandidateStatusHistory",
    "ConsentRecord",
    "ControlledDocument",
    "DocumentVersion",
    "LeadInquiry",
    "OnboardingPlan",
    "OnboardingTask",
    "PolicyAcknowledgement",
    "ProgrammaticGate",
    "RecruitmentPosting",
    "Role",
    "User",
    "UserIdentity",
    "UserRole",
]
