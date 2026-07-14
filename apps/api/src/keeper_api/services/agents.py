from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from keeper_api.models.domain import AgentProfile
from keeper_api.models.statuses import AgentProfileStatus
from keeper_api.services.audit import AuditService


class InvalidAgentProfileTransition(ValueError):
    pass


ALLOWED_AGENT_TRANSITIONS: dict[AgentProfileStatus, set[AgentProfileStatus]] = {
    AgentProfileStatus.DRAFT: {AgentProfileStatus.PENDING_APPROVAL, AgentProfileStatus.ARCHIVED},
    AgentProfileStatus.PENDING_APPROVAL: {AgentProfileStatus.DRAFT, AgentProfileStatus.PUBLISHED},
    AgentProfileStatus.PUBLISHED: {AgentProfileStatus.SUSPENDED, AgentProfileStatus.ARCHIVED},
    AgentProfileStatus.SUSPENDED: {AgentProfileStatus.PUBLISHED, AgentProfileStatus.ARCHIVED},
    AgentProfileStatus.ARCHIVED: set(),
}


class AgentProfileLifecycleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def transition(
        self,
        profile: AgentProfile,
        target: AgentProfileStatus,
        *,
        actor_user_id: uuid.UUID,
        actor_can_approve: bool,
        request_id: str | None = None,
    ) -> AgentProfile:
        current = AgentProfileStatus(profile.status)
        if target not in ALLOWED_AGENT_TRANSITIONS[current]:
            raise InvalidAgentProfileTransition(
                f"transition from {current.value} to {target.value} is not allowed"
            )
        if target is AgentProfileStatus.PUBLISHED:
            if not actor_can_approve:
                raise InvalidAgentProfileTransition(
                    "profile publication requires an authorized approver"
                )
            profile.approved_by_user_id = actor_user_id
            profile.approved_at = datetime.now(UTC)
            profile.published_at = datetime.now(UTC)
        profile.status = target.value
        AuditService(self.db).record(
            f"agent_profile.{target.value}",
            "agent_profile",
            profile.id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"previous_status": current.value, "new_status": target.value},
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile
