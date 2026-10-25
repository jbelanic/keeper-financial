from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

from keeper_api.models.domain import (
    AgentProfile,
    AgentReferralLink,
    Candidate,
    ConsentRecord,
    LeadInquiry,
    Role,
    User,
    UserRole,
)
from keeper_api.models.statuses import AgentProfileStatus
from keeper_api.schemas.leads import LeadInquiryCreate
from keeper_api.services.agents import referral_eligible_condition
from keeper_api.services.audit import AuditService
from keeper_api.services.consent_registry import (
    MARKETING_CONSENT,
    PRIVACY_NOTICE_VERSION,
    SERVICE_CONTACT_CONSENT,
)

# How an inquiry came to be owned by an agent. The raw submitted reference is
# never stored as an identity: it is resolved to an agent account first.
ATTRIBUTION_AGENT_CODE = "agent_code"
ATTRIBUTION_AGENT_PROFILE_SLUG = "agent_profile_slug"
ATTRIBUTION_ADMINISTRATOR = "administrator"

LEAD_STATUSES = ("new", "assigned", "contacted", "closed")


class LeadMarketingConsentNotFound(ValueError):
    pass


class LeadInquiryNotFound(ValueError):
    pass


class LeadAssignmentInvalid(ValueError):
    pass


def eligible_agent_condition() -> ColumnElement[bool]:
    """An account that may own a lead: active, `agent` role, active relationship.

    Publication is deliberately excluded — same rule as the referral link.
    """
    return referral_eligible_condition()


def is_eligible_lead_agent(db: Session, user_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(User.id)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .join(Candidate, Candidate.user_id == User.id)
            .where(User.id == user_id, eligible_agent_condition())
        )
        is not None
    )


def resolve_agent_reference(
    db: Session, reference: str | None
) -> tuple[uuid.UUID, str, uuid.UUID | None] | None:
    """Map one opaque submitted reference to an eligible agent account.

    Accepts the current referral code and the legacy published-profile slug. An
    unknown, revoked, unpublished or ineligible reference resolves to nothing and
    is treated exactly like no reference at all, so a code cannot be probed for
    validity and the applicant is never blocked.
    """
    normalized = (reference or "").strip()
    if not normalized:
        return None
    link = db.scalar(select(AgentReferralLink).where(AgentReferralLink.code == normalized))
    if link is not None:
        if link.revoked_at is not None or not is_eligible_lead_agent(db, link.user_id):
            return None
        return link.user_id, ATTRIBUTION_AGENT_CODE, link.id
    profile_user_id = db.scalar(
        select(AgentProfile.user_id).where(
            AgentProfile.slug == normalized,
            AgentProfile.status == AgentProfileStatus.PUBLISHED.value,
        )
    )
    if profile_user_id is None or not is_eligible_lead_agent(db, profile_user_id):
        return None
    return profile_user_id, ATTRIBUTION_AGENT_PROFILE_SLUG, None


def _consents_for(
    db: Session, lead_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict[str, ConsentRecord]]:
    consent_by_lead: dict[uuid.UUID, dict[str, ConsentRecord]] = {}
    if not lead_ids:
        return consent_by_lead
    consents = db.scalars(
        select(ConsentRecord).where(
            ConsentRecord.lead_inquiry_id.in_(lead_ids),
            ConsentRecord.purpose.in_([SERVICE_CONTACT_CONSENT.purpose, MARKETING_CONSENT.purpose]),
        )
    ).all()
    for consent in consents:
        if consent.lead_inquiry_id is not None:
            consent_by_lead.setdefault(consent.lead_inquiry_id, {})[consent.purpose] = consent
    return consent_by_lead


def assigned_agent_names(db: Session, leads: list[LeadInquiry]) -> dict[uuid.UUID, str]:
    agent_ids = {lead.assigned_agent_user_id for lead in leads if lead.assigned_agent_user_id}
    if not agent_ids:
        return {}
    rows = db.execute(
        select(User.id, User.display_name, User.email).where(User.id.in_(agent_ids))
    ).all()
    return {row.id: (row.display_name or row.email) for row in rows}


def create_lead(
    db: Session,
    payload: LeadInquiryCreate,
    *,
    request_id: str | None = None,
) -> tuple[LeadInquiry, bool]:
    try:
        resolved = resolve_agent_reference(db, payload.agent_reference)
        lead = LeadInquiry(
            name=payload.name,
            email=str(payload.email),
            telephone=payload.telephone,
            mortgage_objective=payload.mortgage_objective,
            preferred_contact_method=payload.preferred_contact_method,
            message=payload.message,
            source=payload.source,
            status="assigned" if resolved else "new",
            assigned_agent_user_id=resolved[0] if resolved else None,
            assigned_at=datetime.now(UTC) if resolved else None,
            assigned_by_user_id=None,
            attribution_source=resolved[1] if resolved else None,
            attributed_referral_link_id=resolved[2] if resolved else None,
        )
        db.add(lead)
        db.flush()
        db.add(
            ConsentRecord(
                lead_inquiry_id=lead.id,
                purpose=SERVICE_CONTACT_CONSENT.purpose,
                wording_version=SERVICE_CONTACT_CONSENT.wording_version,
                privacy_notice_version=PRIVACY_NOTICE_VERSION,
                capture_source=payload.source,
            )
        )
        audit = AuditService(db)
        audit.record(
            "lead.created",
            "lead_inquiry",
            lead.id,
            request_id=request_id,
            safe_metadata={
                "status": lead.status,
                "source": lead.source,
                "assigned": resolved is not None,
            },
        )
        if resolved is not None:
            audit.record(
                "lead.assigned",
                "lead_inquiry",
                lead.id,
                request_id=request_id,
                safe_metadata={
                    "attribution_source": resolved[1],
                    "via": "capture",
                },
            )
        if payload.marketing_consent:
            marketing_record = ConsentRecord(
                lead_inquiry_id=lead.id,
                purpose=MARKETING_CONSENT.purpose,
                wording_version=MARKETING_CONSENT.wording_version,
                privacy_notice_version=PRIVACY_NOTICE_VERSION,
                capture_source=payload.source,
            )
            db.add(marketing_record)
            db.flush()
            audit.record(
                "marketing_consent.granted",
                "consent_record",
                marketing_record.id,
                request_id=request_id,
                safe_metadata={"capture_source": payload.source},
            )
        db.commit()
        db.refresh(lead)
        return lead, payload.marketing_consent
    except Exception:
        db.rollback()
        raise


def list_leads(
    db: Session,
    *,
    lead_status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[LeadInquiry], dict[uuid.UUID, dict[str, ConsentRecord]], int]:
    filters = [LeadInquiry.status == lead_status] if lead_status else []
    total = db.scalar(select(func.count()).select_from(LeadInquiry).where(*filters)) or 0
    leads = list(
        db.scalars(
            select(LeadInquiry)
            .where(*filters)
            .order_by(LeadInquiry.created_at.desc(), LeadInquiry.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return leads, _consents_for(db, [lead.id for lead in leads]), total


def list_agent_leads(
    db: Session,
    *,
    agent_user_id: uuid.UUID,
    limit: int,
    offset: int,
) -> tuple[list[LeadInquiry], dict[uuid.UUID, dict[str, ConsentRecord]], int]:
    """Only inquiries explicitly assigned to this exact agent account."""
    condition = LeadInquiry.assigned_agent_user_id == agent_user_id
    total = db.scalar(select(func.count()).select_from(LeadInquiry).where(condition)) or 0
    leads = list(
        db.scalars(
            select(LeadInquiry)
            .where(condition)
            .order_by(LeadInquiry.created_at.desc(), LeadInquiry.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return leads, _consents_for(db, [lead.id for lead in leads]), total


def get_agent_lead(
    db: Session,
    *,
    lead_id: uuid.UUID,
    agent_user_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> tuple[LeadInquiry, dict[str, ConsentRecord]]:
    """Read one assigned inquiry and append safe view evidence.

    A lead assigned to another agent is indistinguishable from a missing one, so
    assignment cannot be probed.
    """
    lead = db.scalar(
        select(LeadInquiry).where(
            LeadInquiry.id == lead_id,
            LeadInquiry.assigned_agent_user_id == agent_user_id,
        )
    )
    if lead is None:
        raise LeadInquiryNotFound
    AuditService(db).record(
        "agent_lead_viewed",
        "lead_inquiry",
        lead.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"status": lead.status},
    )
    db.commit()
    consents = _consents_for(db, [lead.id]).get(lead.id, {})
    return lead, consents


def list_assignable_agents(
    db: Session, *, limit: int = 200
) -> list[tuple[uuid.UUID, str, str, bool]]:
    """Onboarded agents an administrator can assign an inquiry to."""
    rows = db.execute(
        select(
            User.id,
            User.display_name,
            User.email,
            AgentReferralLink.id.is_not(None).label("has_link"),
        )
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(Candidate, Candidate.user_id == User.id)
        .outerjoin(AgentReferralLink, AgentReferralLink.user_id == User.id)
        .where(eligible_agent_condition())
        .order_by(User.display_name.asc(), User.id.asc())
        .limit(limit)
    ).all()
    return [(row.id, row.display_name or row.email, row.email, bool(row.has_link)) for row in rows]


def assign_lead(
    db: Session,
    *,
    lead_id: uuid.UUID,
    agent_user_id: uuid.UUID | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> LeadInquiry:
    """Assign, reassign, or clear the owning agent of one inquiry."""
    try:
        lead = db.scalar(select(LeadInquiry).where(LeadInquiry.id == lead_id).with_for_update())
        if lead is None:
            raise LeadInquiryNotFound
        if agent_user_id is not None and not is_eligible_lead_agent(db, agent_user_id):
            raise LeadAssignmentInvalid(
                "the selected account is not an onboarded agent with an active relationship"
            )
        previous_agent_id = lead.assigned_agent_user_id
        previous_status = lead.status
        if agent_user_id is None:
            if previous_agent_id is None:
                return lead
            lead.assigned_agent_user_id = None
            lead.assigned_at = None
            lead.assigned_by_user_id = None
            lead.attribution_source = None
            lead.attributed_referral_link_id = None
            if lead.status == "assigned":
                lead.status = "new"
            event = "lead.unassigned"
        else:
            if previous_agent_id == agent_user_id:
                return lead
            lead.assigned_agent_user_id = agent_user_id
            lead.assigned_at = datetime.now(UTC)
            lead.assigned_by_user_id = actor_user_id
            lead.attribution_source = ATTRIBUTION_ADMINISTRATOR
            lead.attributed_referral_link_id = None
            if lead.status == "new":
                lead.status = "assigned"
            event = "lead.assigned"
        AuditService(db).record(
            event,
            "lead_inquiry",
            lead.id,
            actor_user_id=actor_user_id,
            request_id=request_id,
            safe_metadata={
                "previous_status": previous_status,
                "status": lead.status,
                "via": "administrator",
                "reassigned": previous_agent_id is not None and agent_user_id is not None,
            },
        )
        db.commit()
        db.refresh(lead)
        return lead
    except Exception:
        db.rollback()
        raise


def withdraw_marketing_consent(
    db: Session,
    *,
    lead_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> ConsentRecord:
    try:
        lead_exists = db.scalar(select(LeadInquiry.id).where(LeadInquiry.id == lead_id))
        if lead_exists is None:
            raise LeadMarketingConsentNotFound
        consent = db.scalar(
            select(ConsentRecord)
            .where(
                ConsentRecord.lead_inquiry_id == lead_id,
                ConsentRecord.purpose == MARKETING_CONSENT.purpose,
            )
            .with_for_update()
        )
        if consent is None:
            raise LeadMarketingConsentNotFound
        if consent.withdrawn_at is None:
            consent.withdrawn_at = datetime.now(UTC)
            AuditService(db).record(
                "marketing_consent.withdrawn",
                "consent_record",
                consent.id,
                actor_user_id=actor_user_id,
                request_id=request_id,
                safe_metadata={"capture_source": consent.capture_source},
            )
            db.commit()
            db.refresh(consent)
        return consent
    except Exception:
        db.rollback()
        raise


def update_lead_status(
    db: Session,
    *,
    lead_id: uuid.UUID,
    status: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> LeadInquiry:
    try:
        lead = db.scalar(select(LeadInquiry).where(LeadInquiry.id == lead_id).with_for_update())
        if lead is None:
            raise LeadInquiryNotFound
        previous_status = lead.status
        if previous_status != status:
            lead.status = status
            AuditService(db).record(
                "lead.status_changed",
                "lead_inquiry",
                lead.id,
                actor_user_id=actor_user_id,
                request_id=request_id,
                safe_metadata={"from_status": previous_status, "to_status": status},
            )
            db.commit()
            db.refresh(lead)
        return lead
    except Exception:
        db.rollback()
        raise
