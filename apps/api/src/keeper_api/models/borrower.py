from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from keeper_api.db.base import Base
from keeper_api.models.domain import IdTimestampsMixin


class BorrowerApplicationLifecycleStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class BorrowerAttributionSource(StrEnum):
    PUBLIC_SLUG = "public_slug"
    ADMINISTRATOR = "administrator"
    SYSTEM = "system"


class BorrowerSubmissionCoordinationState(StrEnum):
    IDLE = "idle"
    SUBMITTING = "submitting"
    COMPLETED = "completed"
    FAILED = "failed"


class BorrowerApplication(IdTimestampsMixin, Base):
    __tablename__ = "borrower_applications"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN ('draft', 'submitted', 'under_review', 'completed', 'withdrawn', 'expired')",
            name="ck_borrower_application_lifecycle_status",
        ),
        CheckConstraint(
            "revision >= 0",
            name="ck_borrower_application_revision_non_negative",
        ),
        CheckConstraint(
            "payload_revision >= 0",
            name="ck_borrower_application_payload_revision_non_negative",
        ),
        Index(
            "ix_borrower_applications_lifecycle_status",
            "lifecycle_status",
        ),
        Index(
            "ix_borrower_applications_assigned_agent_id",
            "assigned_agent_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    capability_digest: Mapped[str | None] = mapped_column(
        Text, nullable=True, unique=True, index=True
    )

    capability_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, default=uuid.uuid4, nullable=False
    )

    capability_revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    lifecycle_status: Mapped[str] = mapped_column(
        String(32),
        default=BorrowerApplicationLifecycleStatus.DRAFT.value,
        nullable=False,
    )

    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    payload_revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    draft_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    retention_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    assigned_agent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )

    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attribution_source: Mapped[str | None] = mapped_column(String(32), nullable=True)

    attribution_agent_slug: Mapped[str | None] = mapped_column(String(128), nullable=True)

    attribution_resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    submission_coordination_state: Mapped[str] = mapped_column(
        String(32),
        default=BorrowerSubmissionCoordinationState.IDLE.value,
        nullable=False,
    )

    application_payload: Mapped[BorrowerApplicationPayload | None] = relationship(
        "BorrowerApplicationPayload",
        primaryjoin="and_(BorrowerApplication.id==BorrowerApplicationPayload.application_id, "
        "BorrowerApplication.payload_revision==BorrowerApplicationPayload.revision)",
        foreign_keys="BorrowerApplicationPayload.application_id",
        uselist=False,
        lazy="select",
    )

    status_history: Mapped[list[BorrowerApplicationStatusHistory]] = relationship(
        "BorrowerApplicationStatusHistory",
        primaryjoin="BorrowerApplication.id==BorrowerApplicationStatusHistory.application_id",
        foreign_keys="BorrowerApplicationStatusHistory.application_id",
        order_by="BorrowerApplicationStatusHistory.created_at",
        lazy="dynamic",
    )

    assignment_history: Mapped[list[BorrowerAssignmentHistory]] = relationship(
        "BorrowerAssignmentHistory",
        primaryjoin="BorrowerApplication.id==BorrowerAssignmentHistory.application_id",
        foreign_keys="BorrowerAssignmentHistory.application_id",
        order_by="BorrowerAssignmentHistory.created_at",
        lazy="dynamic",
    )


class BorrowerApplicationPayload(IdTimestampsMixin, Base):
    __tablename__ = "borrower_application_payloads"
    __table_args__ = (
        UniqueConstraint("application_id", "revision", name="uq_borrower_payload_app_revision"),
        CheckConstraint(
            "revision > 0",
            name="ck_borrower_payload_revision_positive",
        ),
        CheckConstraint(
            "octet_length(nonce) = 12",
            name="ck_borrower_payload_nonce_length",
        ),
        Index(
            "ix_borrower_application_payloads_application_id",
            "application_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    revision: Mapped[int] = mapped_column(Integer, nullable=False)

    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)

    key_id: Mapped[str] = mapped_column(String(64), nullable=False)

    nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)

    ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    has_sin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    has_co_borrower: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    encrypted_sin_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    encrypted_sin_nonce: Mapped[bytes | None] = mapped_column(LargeBinary(12), nullable=True)


class BorrowerApplicationStatusHistory(IdTimestampsMixin, Base):
    __tablename__ = "borrower_application_status_history"
    __table_args__ = (
        Index(
            "ix_borrower_status_history_application_id",
            "application_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    to_status: Mapped[str] = mapped_column(String(32), nullable=False)

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    actor_source: Mapped[str] = mapped_column(String(32), nullable=False)

    reason_category: Mapped[str | None] = mapped_column(String(64), nullable=True)

    reason_detail: Mapped[str | None] = mapped_column(String(512), nullable=True)

    revision: Mapped[int] = mapped_column(Integer, nullable=False)

    capability_session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class BorrowerAssignmentHistory(IdTimestampsMixin, Base):
    __tablename__ = "borrower_assignment_history"
    __table_args__ = (
        Index(
            "ix_borrower_assignment_history_application_id",
            "application_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    agent_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    actor_source: Mapped[str] = mapped_column(String(32), nullable=False)

    reason_category: Mapped[str] = mapped_column(String(64), nullable=False)

    reason_detail: Mapped[str | None] = mapped_column(String(512), nullable=True)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class BorrowerConsentRecord(IdTimestampsMixin, Base):
    __tablename__ = "borrower_consent_records"
    __table_args__ = (
        Index(
            "ix_borrower_consent_records_application_id",
            "application_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    submission_revision: Mapped[int] = mapped_column(Integer, nullable=False)

    consent_version: Mapped[str] = mapped_column(String(128), nullable=False)

    wording_digest: Mapped[str] = mapped_column(String(128), nullable=False)

    borrower_coverage: Mapped[str] = mapped_column(String(32), nullable=False)

    borrower_count: Mapped[int] = mapped_column(Integer, nullable=False)

    capture_source: Mapped[str] = mapped_column(String(64), nullable=False)

    capability_session_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class BorrowerApplicationSnapshot(IdTimestampsMixin, Base):
    __tablename__ = "borrower_application_snapshots"
    __table_args__ = (
        Index(
            "ix_borrower_application_snapshots_application_id",
            "application_id",
            unique=True,
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    submission_revision: Mapped[int] = mapped_column(Integer, nullable=False)

    key_id: Mapped[str] = mapped_column(String(64), nullable=False)

    nonce: Mapped[bytes] = mapped_column(LargeBinary(12), nullable=False)

    ciphertext_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    plaintext_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    object_key: Mapped[str] = mapped_column(String(256), nullable=False)

    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)


class BorrowerLegalHold(IdTimestampsMixin, Base):
    __tablename__ = "borrower_legal_holds"
    __table_args__ = (
        Index(
            "ix_borrower_legal_holds_application_id",
            "application_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    placed_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    released_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reason_category: Mapped[str] = mapped_column(String(64), nullable=False)

    reason_detail: Mapped[str | None] = mapped_column(String(512), nullable=True)


class BorrowerSinRevealAudit(IdTimestampsMixin, Base):
    __tablename__ = "borrower_sin_reveal_audit"
    __table_args__ = (
        Index(
            "ix_borrower_sin_reveal_audit_application_id",
            "application_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    application_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("borrower_applications.id", ondelete="CASCADE"),
        nullable=False,
    )

    actor_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    actor_role: Mapped[str] = mapped_column(String(32), nullable=False)

    assurance_level: Mapped[str] = mapped_column(String(8), nullable=False)

    selector: Mapped[str] = mapped_column(String(32), nullable=False)

    reason_category: Mapped[str] = mapped_column(String(64), nullable=False)

    result: Mapped[str] = mapped_column(String(16), nullable=False)

    safe_reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
