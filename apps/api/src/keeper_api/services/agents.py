from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement, Select

from keeper_api.models.domain import AgentProfile, Candidate, Role, User, UserRole
from keeper_api.models.statuses import AgentProfileStatus, CandidateStatus
from keeper_api.schemas.agents import AgentProfileCreate, AgentProfileUpdate
from keeper_api.services.audit import AuditService


class InvalidAgentProfileTransition(ValueError):
    pass


class AgentProfileConflict(ValueError):
    pass


ALLOWED_AGENT_TRANSITIONS: dict[AgentProfileStatus, set[AgentProfileStatus]] = {
    AgentProfileStatus.DRAFT: {AgentProfileStatus.PENDING_APPROVAL, AgentProfileStatus.ARCHIVED},
    AgentProfileStatus.PENDING_APPROVAL: {AgentProfileStatus.DRAFT, AgentProfileStatus.PUBLISHED},
    AgentProfileStatus.PUBLISHED: {AgentProfileStatus.SUSPENDED, AgentProfileStatus.ARCHIVED},
    AgentProfileStatus.SUSPENDED: {AgentProfileStatus.PUBLISHED, AgentProfileStatus.ARCHIVED},
    AgentProfileStatus.ARCHIVED: set(),
}


def _eligible_profile_condition() -> ColumnElement[bool]:
    return (
        User.is_active.is_(True)
        & (Role.code == "agent")
        & or_(Candidate.id.is_(None), Candidate.status == CandidateStatus.ACTIVE.value)
    )


def _eligible_profiles_statement() -> Select[tuple[AgentProfile]]:
    return (
        select(AgentProfile)
        .join(User, User.id == AgentProfile.user_id)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .outerjoin(Candidate, Candidate.user_id == User.id)
        .where(_eligible_profile_condition())
    )


def assert_agent_account_eligible(db: Session, user_id: uuid.UUID) -> None:
    eligible = db.scalar(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .outerjoin(Candidate, Candidate.user_id == User.id)
        .where(User.id == user_id, _eligible_profile_condition())
    )
    if eligible is None:
        raise LookupError("active agent relationship not found")


def get_admin_profile(
    db: Session, profile_id: uuid.UUID, *, lock: bool = False
) -> AgentProfile | None:
    statement = _eligible_profiles_statement().where(AgentProfile.id == profile_id)
    if lock:
        statement = statement.with_for_update(of=AgentProfile)
    return db.scalar(statement)


def admin_profiles(db: Session, *, limit: int, offset: int) -> tuple[list[AgentProfile], int]:
    eligible_ids = _eligible_profiles_statement().with_only_columns(AgentProfile.id).subquery()
    condition = AgentProfile.id.in_(select(eligible_ids.c.id))
    total = db.scalar(select(func.count()).select_from(AgentProfile).where(condition)) or 0
    rows = list(
        db.scalars(
            select(AgentProfile)
            .where(condition)
            .order_by(AgentProfile.created_at.desc(), AgentProfile.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return rows, total


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AgentProfileConflict("agent profile user or slug is already in use") from exc


def create_profile(
    db: Session,
    payload: AgentProfileCreate,
    *,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> AgentProfile:
    assert_agent_account_eligible(db, payload.user_id)
    values = payload.model_dump()
    values["social_links"] = [item.model_dump() for item in payload.social_links]
    profile = AgentProfile(
        **values,
        status=AgentProfileStatus.DRAFT.value,
        version=1,
    )
    try:
        db.add(profile)
        db.flush()
        AuditService(db).record(
            "agent_profile.created",
            "agent_profile",
            profile.id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={"status": AgentProfileStatus.DRAFT.value, "source": "admin"},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AgentProfileConflict("agent profile user or slug is already in use") from exc
    except Exception:
        db.rollback()
        raise
    db.refresh(profile)
    return profile


def update_profile(
    db: Session,
    profile: AgentProfile,
    payload: AgentProfileUpdate,
    *,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> AgentProfile:
    if profile.status == AgentProfileStatus.ARCHIVED.value:
        raise AgentProfileConflict("archived profiles cannot be edited")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise AgentProfileConflict("at least one profile field must change")
    nonnullable = {
        "slug",
        "licensed_name",
        "approved_title",
        "licence_number",
        "biography",
        "languages",
        "service_areas",
        "specialties",
        "social_links",
    }
    if any(field in nonnullable and value is None for field, value in changes.items()):
        raise AgentProfileConflict("required profile fields cannot be null")
    if "social_links" in changes and changes["social_links"] is not None:
        changes["social_links"] = [item.model_dump() for item in payload.social_links or []]
    for field, value in changes.items():
        setattr(profile, field, value)
    if (profile.photo_url is None) != (profile.photo_alt_text is None):
        raise AgentProfileConflict("photo URL and photo alternative text must be supplied together")
    previous_status = profile.status
    if profile.status == AgentProfileStatus.PUBLISHED.value:
        profile.status = AgentProfileStatus.PENDING_APPROVAL.value
        profile.approved_by_user_id = None
        profile.approved_at = None
        profile.published_at = None
    profile.version += 1
    AuditService(db).record(
        "agent_profile.updated",
        "agent_profile",
        profile.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "previous_status": previous_status,
            "new_status": profile.status,
            "version": profile.version,
        },
    )
    _commit(db)
    db.refresh(profile)
    return profile


def public_profiles(db: Session, *, limit: int, offset: int) -> tuple[list[AgentProfile], int]:
    eligible_ids = _eligible_profiles_statement().with_only_columns(AgentProfile.id).subquery()
    condition = (AgentProfile.status == AgentProfileStatus.PUBLISHED.value) & AgentProfile.id.in_(
        select(eligible_ids.c.id)
    )
    total = db.scalar(select(func.count()).select_from(AgentProfile).where(condition)) or 0
    rows = list(
        db.scalars(
            select(AgentProfile)
            .where(condition)
            .order_by(AgentProfile.published_at.desc(), AgentProfile.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return rows, total


def public_profile_by_slug(db: Session, slug: str) -> AgentProfile | None:
    return db.scalar(
        _eligible_profiles_statement().where(
            AgentProfile.slug == slug,
            AgentProfile.status == AgentProfileStatus.PUBLISHED.value,
        )
    )


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
        reason: str | None = None,
        request_id: str | None = None,
    ) -> AgentProfile:
        current = AgentProfileStatus(profile.status)
        if target not in ALLOWED_AGENT_TRANSITIONS[current]:
            raise InvalidAgentProfileTransition(
                f"transition from {current.value} to {target.value} is not allowed"
            )
        if target is AgentProfileStatus.SUSPENDED and not (reason and reason.strip()):
            raise InvalidAgentProfileTransition("a reason is required for suspended")
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
            safe_metadata={
                "previous_status": current.value,
                "new_status": target.value,
                "reason_provided": bool(reason and reason.strip()),
            },
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile
