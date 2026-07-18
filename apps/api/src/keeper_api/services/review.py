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

DENIED_CANDIDATE_STATUSES: frozenset[CandidateStatus] = frozenset(
    {
        CandidateStatus.SUSPENDED,
        CandidateStatus.OFFBOARDING,
        CandidateStatus.OFFBOARDED,
    }
)

# Application-specific lifecycle authority. Assignment performs the sole
# conditionally_selected -> onboarding_in_progress transition in this phase.
APPLICATION_REVIEW_TRANSITIONS: dict[CandidateStatus, frozenset[CandidateStatus]] = {
    CandidateStatus.APPLICATION_SUBMITTED: frozenset(
        {
            CandidateStatus.UNDER_REVIEW,
            CandidateStatus.WITHDRAWN,
        }
    ),
    CandidateStatus.UNDER_REVIEW: frozenset(
        {
            CandidateStatus.MORE_INFORMATION_REQUIRED,
            CandidateStatus.INTERVIEW,
            CandidateStatus.CONDITIONALLY_SELECTED,
            CandidateStatus.DECLINED,
            CandidateStatus.WITHDRAWN,
        }
    ),
    CandidateStatus.MORE_INFORMATION_REQUIRED: frozenset(
        {
            CandidateStatus.UNDER_REVIEW,
            CandidateStatus.INTERVIEW,
            CandidateStatus.DECLINED,
            CandidateStatus.WITHDRAWN,
        }
    ),
    CandidateStatus.INTERVIEW: frozenset(
        {
            CandidateStatus.MORE_INFORMATION_REQUIRED,
            CandidateStatus.CONDITIONALLY_SELECTED,
            CandidateStatus.DECLINED,
            CandidateStatus.WITHDRAWN,
        }
    ),
    CandidateStatus.CONDITIONALLY_SELECTED: frozenset(
        {
            CandidateStatus.DECLINED,
            CandidateStatus.WITHDRAWN,
        }
    ),
}

DECISION_ALLOWED: frozenset[CandidateStatus] = frozenset(
    target for targets in APPLICATION_REVIEW_TRANSITIONS.values() for target in targets
)
REASON_REQUIRED_FOR_DECISION: frozenset[CandidateStatus] = frozenset(
    {CandidateStatus.DECLINED, CandidateStatus.WITHDRAWN}
)


class ReviewError(ValueError):
    pass


class CandidateLifecycleService:
    """Candidate relationship authorization; application state is separate."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def assert_admin_accessible(self, candidate: Candidate) -> None:
        if CandidateStatus(candidate.status) in DENIED_CANDIDATE_STATUSES:
            raise PermissionError("candidate access is unavailable")


@dataclass
class CandidateProfileView:
    given_name: str | None
    family_name: str | None
    email: str


def candidate_profile(
    db: Session, candidate: Candidate, application: CandidateApplication
) -> CandidateProfileView:
    user = db.get(User, candidate.user_id)
    return CandidateProfileView(
        given_name=application.given_name,
        family_name=application.family_name,
        email=user.email if user is not None else "",
    )


def candidate_review_queue(
    db: Session, *, limit: int, offset: int, status: CandidateStatus | None = None
) -> tuple[list[tuple[CandidateApplication, Candidate]], int]:
    if status is not None and status not in REVIEW_QUEUE_STATUSES:
        return [], 0
    application_statuses = (
        [status.value] if status is not None else [item.value for item in REVIEW_QUEUE_STATUSES]
    )
    denied_relationships = [item.value for item in DENIED_CANDIDATE_STATUSES]
    condition = CandidateApplication.status.in_(application_statuses) & Candidate.status.not_in(
        denied_relationships
    )
    total = (
        db.scalar(
            select(func.count())
            .select_from(CandidateApplication)
            .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
            .where(condition)
        )
        or 0
    )
    rows = [
        (application, candidate)
        for application, candidate in db.execute(
            select(CandidateApplication, Candidate)
            .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
            .where(condition)
            .order_by(CandidateApplication.created_at.desc(), CandidateApplication.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    ]
    return rows, total


def get_review_application(
    db: Session,
    candidate_id: uuid.UUID,
    application_id: uuid.UUID,
    *,
    lock: bool = False,
) -> tuple[Candidate, CandidateApplication]:
    statement = select(CandidateApplication).where(
        CandidateApplication.id == application_id,
        CandidateApplication.candidate_id == candidate_id,
    )
    if lock:
        statement = statement.with_for_update()
    application = db.scalar(statement)
    if application is None:
        raise LookupError("candidate application not found")
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise LookupError("candidate application not found")
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    return candidate, application


def get_review_candidate(db: Session, candidate_id: uuid.UUID) -> Candidate:
    """Relationship-level lookup retained for non-review onboarding controls."""
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise LookupError("candidate not found")
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    return candidate


def _transition_application(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    target: CandidateStatus,
    actor_user_id: uuid.UUID,
    reason: str | None,
    request_id: str | None,
) -> CandidateApplication:
    current = CandidateStatus(application.status)
    if target not in APPLICATION_REVIEW_TRANSITIONS.get(current, frozenset()):
        raise ReviewError(f"transition from {current.value} to {target.value} is not allowed")
    if target in REASON_REQUIRED_FOR_DECISION and not (reason and reason.strip()):
        raise ReviewError(f"a reason is required to record {target.value}")
    application.status = target.value
    if target == CandidateStatus.WITHDRAWN:
        application.state = "withdrawn"
        application.withdrawn_at = datetime.now(UTC)
    db.add(
        CandidateStatusHistory(
            candidate_id=candidate.id,
            application_id=application.id,
            previous_status=current.value,
            new_status=target.value,
            actor_user_id=actor_user_id,
            reason=reason.strip() if reason else None,
        )
    )
    AuditService(db).record(
        "candidate_application.status_changed",
        "candidate_application",
        application.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"previous_status": current.value, "new_status": target.value},
    )
    return application


def record_interview_status(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    interview_status: InterviewStatus,
    notes: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateApplication:
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    current = CandidateStatus(application.status)
    if current not in {
        CandidateStatus.UNDER_REVIEW,
        CandidateStatus.MORE_INFORMATION_REQUIRED,
        CandidateStatus.INTERVIEW,
    }:
        raise ReviewError("interview status is only recorded for the selected active application")
    application.interview_status = interview_status.value
    application.interview_notes = notes
    application.interview_recorded_at = datetime.now(UTC)
    if current != CandidateStatus.INTERVIEW and interview_status in {
        InterviewStatus.SCHEDULED,
        InterviewStatus.COMPLETED,
    }:
        _transition_application(
            db,
            candidate=candidate,
            application=application,
            target=CandidateStatus.INTERVIEW,
            actor_user_id=actor_user_id,
            reason=None,
            request_id=request_id,
        )
    AuditService(db).record(
        "candidate_application.interview_status_recorded",
        "candidate_application",
        application.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "interview_status": interview_status.value,
            "application_status": application.status,
        },
    )
    db.commit()
    db.refresh(application)
    return application


def request_information(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    message: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateInformationRequest:
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    if CandidateStatus(application.status) not in {
        CandidateStatus.UNDER_REVIEW,
        CandidateStatus.INTERVIEW,
    }:
        raise ReviewError("information may only be requested for the selected active application")
    record = CandidateInformationRequest(
        candidate_id=candidate.id,
        application_id=application.id,
        requested_by_user_id=actor_user_id,
        message=message,
        status="open",
    )
    db.add(record)
    db.flush()
    _transition_application(
        db,
        candidate=candidate,
        application=application,
        target=CandidateStatus.MORE_INFORMATION_REQUIRED,
        actor_user_id=actor_user_id,
        reason=None,
        request_id=request_id,
    )
    AuditService(db).record(
        "candidate_application.information_requested",
        "candidate_application",
        application.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"information_request_id": str(record.id)},
    )
    db.commit()
    db.refresh(record)
    return record


def decide_candidate(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    decision: CandidateStatus,
    reason: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateApplication:
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    application = _transition_application(
        db,
        candidate=candidate,
        application=application,
        target=decision,
        actor_user_id=actor_user_id,
        reason=reason,
        request_id=request_id,
    )
    db.commit()
    db.refresh(application)
    return application


def record_withdrawal(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    reason: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateApplication:
    return decide_candidate(
        db,
        candidate=candidate,
        application=application,
        decision=CandidateStatus.WITHDRAWN,
        reason=reason,
        actor_user_id=actor_user_id,
        request_id=request_id,
    )


__all__ = [
    "APPLICATION_REVIEW_TRANSITIONS",
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
    "get_review_application",
    "get_review_candidate",
    "record_interview_status",
    "record_withdrawal",
    "request_information",
]
