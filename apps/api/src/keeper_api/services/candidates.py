from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from keeper_api.models.domain import Candidate, CandidateStatusHistory
from keeper_api.models.statuses import CandidateStatus
from keeper_api.services.audit import AuditService


class InvalidCandidateTransition(ValueError):
    pass


ALLOWED_CANDIDATE_TRANSITIONS: dict[CandidateStatus, set[CandidateStatus]] = {
    CandidateStatus.PROSPECT: {CandidateStatus.APPLICATION_STARTED, CandidateStatus.WITHDRAWN},
    CandidateStatus.APPLICATION_STARTED: {
        CandidateStatus.APPLICATION_SUBMITTED,
        CandidateStatus.WITHDRAWN,
    },
    CandidateStatus.APPLICATION_SUBMITTED: {
        CandidateStatus.UNDER_REVIEW,
        CandidateStatus.WITHDRAWN,
    },
    CandidateStatus.UNDER_REVIEW: {
        CandidateStatus.MORE_INFORMATION_REQUIRED,
        CandidateStatus.INTERVIEW,
        CandidateStatus.DECLINED,
        CandidateStatus.WITHDRAWN,
    },
    CandidateStatus.MORE_INFORMATION_REQUIRED: {
        CandidateStatus.UNDER_REVIEW,
        CandidateStatus.DECLINED,
        CandidateStatus.WITHDRAWN,
    },
    CandidateStatus.INTERVIEW: {
        CandidateStatus.CONDITIONALLY_SELECTED,
        CandidateStatus.DECLINED,
        CandidateStatus.WITHDRAWN,
    },
    CandidateStatus.CONDITIONALLY_SELECTED: {
        CandidateStatus.ONBOARDING_IN_PROGRESS,
        CandidateStatus.DECLINED,
        CandidateStatus.WITHDRAWN,
    },
    CandidateStatus.ONBOARDING_IN_PROGRESS: {CandidateStatus.PENDING_FSRA_AUTHORIZATION},
    CandidateStatus.PENDING_FSRA_AUTHORIZATION: {CandidateStatus.PENDING_SYSTEM_PROVISIONING},
    CandidateStatus.PENDING_SYSTEM_PROVISIONING: {CandidateStatus.ACTIVE},
    CandidateStatus.ACTIVE: {CandidateStatus.SUSPENDED, CandidateStatus.OFFBOARDING},
    CandidateStatus.SUSPENDED: {CandidateStatus.ACTIVE, CandidateStatus.OFFBOARDING},
    CandidateStatus.OFFBOARDING: {CandidateStatus.OFFBOARDED},
    CandidateStatus.DECLINED: set(),
    CandidateStatus.WITHDRAWN: set(),
    CandidateStatus.OFFBOARDED: set(),
}

REASON_REQUIRED = {
    CandidateStatus.DECLINED,
    CandidateStatus.SUSPENDED,
    CandidateStatus.OFFBOARDING,
}


class CandidateLifecycleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def transition(
        self,
        candidate: Candidate,
        target: CandidateStatus,
        *,
        actor_user_id: uuid.UUID,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> Candidate:
        current = CandidateStatus(candidate.status)
        if target not in ALLOWED_CANDIDATE_TRANSITIONS[current]:
            raise InvalidCandidateTransition(
                f"transition from {current.value} to {target.value} is not allowed"
            )
        if target in REASON_REQUIRED and not (reason and reason.strip()):
            raise InvalidCandidateTransition(f"a reason is required for {target.value}")

        candidate.status = target.value
        self.db.add(
            CandidateStatusHistory(
                candidate_id=candidate.id,
                previous_status=current.value,
                new_status=target.value,
                actor_user_id=actor_user_id,
                reason=reason.strip() if reason else None,
            )
        )
        AuditService(self.db).record(
            "candidate.status_changed",
            "candidate",
            candidate.id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"previous_status": current.value, "new_status": target.value},
        )
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
