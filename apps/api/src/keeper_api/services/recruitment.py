from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keeper_api.models.domain import RecruitmentPosting
from keeper_api.schemas.recruitment import PostingCreate, PostingUpdate
from keeper_api.services.audit import AuditService


class PostingConflict(ValueError):
    pass


POSTING_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"published", "archived"},
    "published": {"closed"},
    "closed": {"archived"},
    "archived": set(),
}


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise PostingConflict("posting slug is already in use") from exc


def create_posting(
    db: Session,
    payload: PostingCreate,
    *,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> RecruitmentPosting:
    posting = RecruitmentPosting(
        **payload.model_dump(),
        status="draft",
        version=1,
        created_by_user_id=actor_user_id,
        updated_by_user_id=actor_user_id,
    )
    db.add(posting)
    db.flush()
    AuditService(db).record(
        "recruitment_posting.created",
        "recruitment_posting",
        posting.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"status": "draft", "source": "admin"},
    )
    _commit(db)
    db.refresh(posting)
    return posting


def update_posting(
    db: Session,
    posting: RecruitmentPosting,
    payload: PostingUpdate,
    *,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> RecruitmentPosting:
    if posting.status not in {"draft", "published"}:
        raise PostingConflict("closed or archived postings cannot be edited")
    changes = payload.model_dump(exclude_none=True)
    if not changes:
        raise PostingConflict("at least one posting field must change")
    for field, value in changes.items():
        setattr(posting, field, value)
    posting.version += 1
    posting.updated_by_user_id = actor_user_id
    AuditService(db).record(
        "recruitment_posting.updated",
        "recruitment_posting",
        posting.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"status": posting.status, "version": posting.version},
    )
    _commit(db)
    db.refresh(posting)
    return posting


def transition_posting(
    db: Session,
    posting: RecruitmentPosting,
    target: str,
    *,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> RecruitmentPosting:
    previous = posting.status
    if target not in POSTING_TRANSITIONS[previous]:
        raise PostingConflict(f"transition from {previous} to {target} is not allowed")
    now = datetime.now(UTC)
    posting.status = target
    posting.updated_by_user_id = actor_user_id
    if target == "published":
        posting.published_at = now
        posting.published_by_user_id = actor_user_id
    elif target == "closed":
        posting.closed_at = now
        posting.closed_by_user_id = actor_user_id
    else:
        posting.archived_at = now
        posting.archived_by_user_id = actor_user_id
    AuditService(db).record(
        f"recruitment_posting.{target}",
        "recruitment_posting",
        posting.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"previous_status": previous, "new_status": target, "source": "admin"},
    )
    db.commit()
    db.refresh(posting)
    return posting


def public_postings(
    db: Session, *, limit: int, offset: int
) -> tuple[list[RecruitmentPosting], int]:
    condition = RecruitmentPosting.status == "published"
    total = db.scalar(select(func.count()).select_from(RecruitmentPosting).where(condition)) or 0
    rows = list(
        db.scalars(
            select(RecruitmentPosting)
            .where(condition)
            .order_by(RecruitmentPosting.published_at.desc(), RecruitmentPosting.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return rows, total
