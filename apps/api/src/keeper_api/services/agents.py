from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement, Select

from keeper_api.models.domain import (
    AgentProfile,
    AgentReferralLink,
    Candidate,
    Role,
    User,
    UserRole,
)
from keeper_api.models.statuses import AgentProfileStatus, CandidateStatus
from keeper_api.schemas.agents import AgentProfileCreate, AgentProfileUpdate
from keeper_api.services.audit import AuditService


def _default_photo_alt_text(licensed_name: str | None) -> str:
    candidate = (licensed_name or "Agent").strip()
    return f"{candidate} profile photo" if candidate else "Agent profile photo"


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


_REFERRAL_CODE_ATTEMPTS = 5


def _new_referral_code() -> str:
    return secrets.token_hex(10)


def referral_eligible_condition() -> ColumnElement[bool]:
    """An agent who can actually open an attributed application.

    Mirrors `require_internal_agent_access`: active user, `agent` role, and an ACTIVE
    candidate relationship. Profile publication is deliberately excluded, so an
    onboarded agent has a working link without a published profile.
    """
    return (
        User.is_active.is_(True)
        & (Role.code == "agent")
        & (Candidate.status == CandidateStatus.ACTIVE.value)
    )


def assert_referral_agent_eligible(db: Session, user_id: uuid.UUID) -> None:
    eligible = db.scalar(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(Candidate, Candidate.user_id == User.id)
        .where(User.id == user_id, referral_eligible_condition())
    )
    if eligible is None:
        raise LookupError("active agent relationship not found")


def referral_link_for_user(db: Session, user_id: uuid.UUID) -> AgentReferralLink | None:
    return db.scalar(select(AgentReferralLink).where(AgentReferralLink.user_id == user_id))


def ensure_referral_link(
    db: Session, user_id: uuid.UUID, *, created_by_user_id: uuid.UUID | None = None
) -> AgentReferralLink:
    """Return this agent's link, minting one on first use."""
    existing = referral_link_for_user(db, user_id)
    if existing is not None:
        if existing.revoked_at is not None:
            existing.revoked_at = None
            db.commit()
            db.refresh(existing)
        return existing
    assert_referral_agent_eligible(db, user_id)
    for _ in range(_REFERRAL_CODE_ATTEMPTS):
        link = AgentReferralLink(
            user_id=user_id,
            code=_new_referral_code(),
            created_by_user_id=created_by_user_id,
        )
        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(link)
        return link
    raise AgentProfileConflict("referral code could not be minted")


def rotate_referral_link(
    db: Session,
    user_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID,
    request_id: str | None = None,
) -> AgentReferralLink:
    assert_referral_agent_eligible(db, user_id)
    link = ensure_referral_link(db, user_id, created_by_user_id=actor_user_id)
    for _ in range(_REFERRAL_CODE_ATTEMPTS):
        link.code = _new_referral_code()
        link.rotated_at = datetime.now(UTC)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        break
    else:
        raise AgentProfileConflict("referral code could not be rotated")
    AuditService(db).record(
        "agent.referral_link_rotated",
        "user",
        user_id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={},
    )
    db.commit()
    db.refresh(link)
    return link


def resolve_referral_code(db: Session, code: str) -> AgentReferralLink | None:
    """Resolve a public referral code to an eligible agent, or None.

    Unknown, revoked, and ineligible codes are indistinguishable from supplying no
    code at all, so a crafted link cannot probe the agent roster.
    """
    normalized = code.strip().lower()
    if not normalized or len(normalized) > 32:
        return None
    link = db.scalar(select(AgentReferralLink).where(AgentReferralLink.code == normalized))
    if link is None or link.revoked_at is not None:
        return None
    eligible = db.scalar(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(Candidate, Candidate.user_id == User.id)
        .where(User.id == link.user_id, referral_eligible_condition())
    )
    if eligible is None:
        return None
    return link


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


def eligible_agent_accounts(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .outerjoin(Candidate, Candidate.user_id == User.id)
            .outerjoin(AgentProfile, AgentProfile.user_id == User.id)
            .where(_eligible_profile_condition())
            .order_by(User.display_name, User.email, User.id)
        ).all()
    )


def slug_is_available(
    db: Session, slug: str, *, excluding_profile_id: uuid.UUID | None = None
) -> bool:
    conditions = [AgentProfile.slug == slug]
    if excluding_profile_id is not None:
        conditions.append(AgentProfile.id != excluding_profile_id)
    return db.scalar(select(AgentProfile.id).where(*conditions)) is None


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
    if values.get("photo_url") is not None and values.get("photo_alt_text") is None:
        values["photo_alt_text"] = _default_photo_alt_text(values.get("licensed_name"))
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
    if (
        "photo_url" in changes
        and changes["photo_url"] is not None
        and changes.get("photo_alt_text") is None
    ):
        changes["photo_alt_text"] = _default_photo_alt_text(
            changes.get("licensed_name") or profile.licensed_name
        )
    if profile.slug_locked_at is not None and "slug" in changes and changes["slug"] != profile.slug:
        raise AgentProfileConflict("published profile slugs cannot be changed")
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
            if profile.slug_locked_at is None:
                profile.slug_locked_at = datetime.now(UTC)
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
