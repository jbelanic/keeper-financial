from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from keeper_api.models.domain import (
    Candidate,
    CandidateApplication,
    CandidateInformationRequest,
    CandidateStatusHistory,
    User,
)
from keeper_api.models.statuses import CandidateStatus, InterviewStatus
from keeper_api.services.audit import AuditService

# Review queue states that carry an active application under brokerage
# consideration (REV-001). Terminal and pre-application states are excluded.
REVIEW_QUEUE_STATUSES: frozenset[CandidateStatus] = frozenset(
    {
        CandidateStatus.APPLICATION_SUBMITTED,
        CandidateStatus.UNDER_REVIEW,
        CandidateStatus.MORE_INFORMATION_REQUIRED,
        CandidateStatus.INTERVIEW,
        CandidateStatus.CONDITIONALLY_SELECTED,
        CandidateStatus.ONBOARDING_IN_PROGRESS,
        CandidateStatus.PENDING_FSRA_AUTHORIZATION,
        CandidateStatus.PENDING_SYSTEM_PROVISIONING,
    }
)

# Candidate lifecycle states that must be denied all candidate-portal and
# review access (docs/00 §7). Mirrors the B1 enforcement in provision_application.
DENIED_CANDIDATE_STATUSES: frozenset[CandidateStatus] = frozenset(
    {
        CandidateStatus.SUSPENDED,
        CandidateStatus.OFFBOARDING,
        CandidateStatus.OFFBOARDED,
    }
)

# Decisions that an authorized admin may record against a candidate (REV-004).
DECISION_ALLOWED: frozenset[CandidateStatus] = frozenset(
    {
        CandidateStatus.UNDER_REVIEW,
        CandidateStatus.MORE_INFORMATION_REQUIRED,
        CandidateStatus.INTERVIEW,
        CandidateStatus.CONDITIONALLY_SELECTED,
        CandidateStatus.DECLINED,
        CandidateStatus.WITHDRAWN,
    }
)

REASON_REQUIRED_FOR_DECISION: frozenset[CandidateStatus] = frozenset(
    {
        CandidateStatus.DECLINED,
        CandidateStatus.WITHDRAWN,
    }
)


class ReviewError(ValueError):
    pass


class CandidateLifecycleService:
    """Candidate portal + review access authorization (docs/00 §7, B1 pattern)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def assert_admin_accessible(self, candidate: Candidate) -> None:
        """Raise if the candidate lifecycle must deny review access (§7 / B1)."""
        status = CandidateStatus(candidate.status)
        if status in DENIED_CANDIDATE_STATUSES:
            raise PermissionError("candidate access is unavailable")


def _candidate_email(db: Session, candidate: Candidate) -> str:
    user = db.get(User, candidate.user_id)
    return user.email if user is not None else ""


@dataclass
class CandidateProfileView:
    given_name: str | None
    family_name: str | None
    email: str


def candidate_profile(db: Session, candidate: Candidate) -> CandidateProfileView:
    """Name/email for review display, sourced from the latest submitted application."""
    application = db.scalar(
        select(CandidateApplication)
        .where(CandidateApplication.candidate_id == candidate.id)
        .order_by(CandidateApplication.created_at.desc(), CandidateApplication.id.desc())
    )
    user = db.get(User, candidate.user_id)
    return CandidateProfileView(
        given_name=application.given_name if application else None,
        family_name=application.family_name if application else None,
        email=user.email if user is not None else "",
    )


def candidate_review_queue(
    db: Session, *, limit: int, offset: int, status: CandidateStatus | None = None
) -> tuple[list[Candidate], int]:
    from sqlalchemy.sql import ColumnElement

    condition: ColumnElement[bool] = Candidate.status.in_([s.value for s in REVIEW_QUEUE_STATUSES])
    if status is not None:
        condition = condition & (Candidate.status == status.value)
    total = db.scalar(select(func.count()).select_from(Candidate).where(condition)) or 0
    rows = list(
        db.scalars(
            select(Candidate)
            .where(condition)
            .order_by(Candidate.created_at.desc(), Candidate.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return rows, total


def get_review_candidate(db: Session, candidate_id: uuid.UUID) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise LookupError("candidate not found")
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    return candidate


def record_interview_status(
    db: Session,
    *,
    candidate: Candidate,
    interview_status: InterviewStatus,
    notes: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> Candidate:
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    if CandidateStatus(candidate.status) not in REVIEW_QUEUE_STATUSES:
        raise ReviewError("interview status is only recorded during active review")
    candidate.interview_status = interview_status.value
    candidate.interview_notes = notes
    candidate.interview_recorded_at = datetime.now(UTC)
    AuditService(db).record(
        "candidate.interview_status_recorded",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "interview_status": interview_status.value,
            "candidate_status": candidate.status,
        },
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def request_information(
    db: Session,
    *,
    candidate: Candidate,
    message: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateInformationRequest:
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    if CandidateStatus(candidate.status) not in REVIEW_QUEUE_STATUSES:
        raise ReviewError("information requests are only open during active review")
    request = CandidateInformationRequest(
        candidate_id=candidate.id,
        requested_by_user_id=actor_user_id,
        message=message,
        status="open",
    )
    db.add(request)
    AuditService(db).record(
        "candidate.information_requested",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"request_id": str(request.id)},
    )
    db.commit()
    db.refresh(request)
    return request


def _transition(
    db: Session,
    *,
    candidate: Candidate,
    target: CandidateStatus,
    actor_user_id: uuid.UUID,
    reason: str | None,
    request_id: str | None,
) -> Candidate:
    current = CandidateStatus(candidate.status)
    if target not in DECISION_ALLOWED:
        raise ReviewError(f"decision to {target.value} is not permitted from the review queue")
    if target in REASON_REQUIRED_FOR_DECISION and not (reason and reason.strip()):
        raise ReviewError(f"a reason is required to record {target.value}")
    candidate.status = target.value
    db.add(
        CandidateStatusHistory(
            candidate_id=candidate.id,
            previous_status=current.value,
            new_status=target.value,
            actor_user_id=actor_user_id,
            reason=reason.strip() if reason else None,
        )
    )
    AuditService(db).record(
        "candidate.status_changed",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"previous_status": current.value, "new_status": target.value},
    )
    db.commit()
    db.refresh(candidate)
    return candidate


def decide_candidate(
    db: Session,
    *,
    candidate: Candidate,
    decision: CandidateStatus,
    reason: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> Candidate:
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    return _transition(
        db,
        candidate=candidate,
        target=decision,
        actor_user_id=actor_user_id,
        reason=reason,
        request_id=request_id,
    )


def record_withdrawal(
    db: Session,
    *,
    candidate: Candidate,
    reason: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> Candidate:
    """REV-005: withdrawal records actor, timestamp, prior/new state, and reason."""
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    return _transition(
        db,
        candidate=candidate,
        target=CandidateStatus.WITHDRAWN,
        actor_user_id=actor_user_id,
        reason=reason,
        request_id=request_id,
    )


__all__ = [
    "DECISION_ALLOWED",
    "DENIED_CANDIDATE_STATUSES",
    "REASON_REQUIRED_FOR_DECISION",
    "REVIEW_QUEUE_STATUSES",
    "CandidateLifecycleService",
    "CandidateProfileView",
    "ReviewError",
    "candidate_profile",
    "candidate_review_queue",
    "decide_candidate",
    "get_review_candidate",
    "record_interview_status",
    "record_withdrawal",
    "request_information",
]
