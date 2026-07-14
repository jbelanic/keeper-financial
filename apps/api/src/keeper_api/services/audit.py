from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from keeper_api.models.domain import AuditEvent


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(
        self,
        event_type: str,
        target_type: str,
        target_id: uuid.UUID | None,
        *,
        actor_user_id: uuid.UUID | None = None,
        request_id: str | None = None,
        safe_metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            target_type=target_type,
            target_id=target_id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata=safe_metadata or {},
        )
        self.db.add(event)
        self.db.flush()
        return event
