from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from keeper_api.models.domain import AgentProfile, ConsentRecord, LeadInquiry
from keeper_api.schemas.leads import LeadInquiryCreate
from keeper_api.services.audit import AuditService
from keeper_api.services.consent_registry import (
    MARKETING_CONSENT,
    PRIVACY_NOTICE_VERSION,
    SERVICE_CONTACT_CONSENT,
    WEBSITE_CAPTURE_SOURCE,
)


class InvalidLeadAttribution(ValueError):
    pass


class LeadMarketingConsentNotFound(ValueError):
    pass


class LeadInquiryNotFound(ValueError):
    pass


def create_lead(
    db: Session,
    payload: LeadInquiryCreate,
    *,
    request_id: str | None = None,
) -> tuple[LeadInquiry, bool]:
    try:
        if payload.preferred_agent_slug:
            approved_agent_id = db.scalar(
                select(AgentProfile.id).where(
                    AgentProfile.slug == payload.preferred_agent_slug,
                    AgentProfile.status == "published",
                )
            )
            if approved_agent_id is None:
                raise InvalidLeadAttribution("preferred agent is not an approved published profile")
        lead = LeadInquiry(
            name=payload.name,
            email=str(payload.email),
            telephone=payload.telephone,
            mortgage_objective=payload.mortgage_objective,
            preferred_contact_method=payload.preferred_contact_method,
            preferred_agent_slug=payload.preferred_agent_slug,
            message=payload.message,
            source=WEBSITE_CAPTURE_SOURCE,
            status="new",
        )
        db.add(lead)
        db.flush()
        db.add(
            ConsentRecord(
                lead_inquiry_id=lead.id,
                purpose=SERVICE_CONTACT_CONSENT.purpose,
                wording_version=SERVICE_CONTACT_CONSENT.wording_version,
                privacy_notice_version=PRIVACY_NOTICE_VERSION,
                capture_source=WEBSITE_CAPTURE_SOURCE,
            )
        )
        audit = AuditService(db)
        audit.record(
            "lead.created",
            "lead_inquiry",
            lead.id,
            request_id=request_id,
            safe_metadata={"status": lead.status, "source": lead.source},
        )
        if payload.marketing_consent:
            marketing_record = ConsentRecord(
                lead_inquiry_id=lead.id,
                purpose=MARKETING_CONSENT.purpose,
                wording_version=MARKETING_CONSENT.wording_version,
                privacy_notice_version=PRIVACY_NOTICE_VERSION,
                capture_source=WEBSITE_CAPTURE_SOURCE,
            )
            db.add(marketing_record)
            db.flush()
            audit.record(
                "marketing_consent.granted",
                "consent_record",
                marketing_record.id,
                request_id=request_id,
                safe_metadata={"capture_source": WEBSITE_CAPTURE_SOURCE},
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
    consent_by_lead: dict[uuid.UUID, dict[str, ConsentRecord]] = {}
    if leads:
        consents = db.scalars(
            select(ConsentRecord).where(
                ConsentRecord.lead_inquiry_id.in_([lead.id for lead in leads]),
                ConsentRecord.purpose.in_(
                    [SERVICE_CONTACT_CONSENT.purpose, MARKETING_CONSENT.purpose]
                ),
            )
        ).all()
        for consent in consents:
            if consent.lead_inquiry_id is not None:
                consent_by_lead.setdefault(consent.lead_inquiry_id, {})[consent.purpose] = consent
    return leads, consent_by_lead, total


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
