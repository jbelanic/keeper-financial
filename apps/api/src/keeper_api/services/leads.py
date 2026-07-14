from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.models.domain import AgentProfile, ConsentRecord, LeadInquiry
from keeper_api.schemas.leads import LeadInquiryCreate
from keeper_api.services.audit import AuditService


class InvalidLeadAttribution(ValueError):
    pass


def create_lead(
    db: Session,
    payload: LeadInquiryCreate,
    *,
    request_id: str | None = None,
) -> tuple[LeadInquiry, bool]:
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
    )
    db.add(lead)
    db.flush()
    db.add(
        ConsentRecord(
            lead_inquiry_id=lead.id,
            purpose="service_contact_acknowledgement",
            wording_version=payload.service_wording_version,
            privacy_notice_version=payload.privacy_notice_version,
            capture_source="website_apply",
        )
    )
    if payload.marketing_consent:
        marketing_record = ConsentRecord(
            lead_inquiry_id=lead.id,
            purpose="marketing",
            wording_version=payload.marketing_wording_version,
            privacy_notice_version=payload.privacy_notice_version,
            capture_source="website_apply",
        )
        db.add(marketing_record)
        db.flush()
        AuditService(db).record(
            "marketing_consent.granted",
            "consent_record",
            marketing_record.id,
            request_id=request_id,
            safe_metadata={"capture_source": "website_apply"},
        )
    db.commit()
    db.refresh(lead)
    return lead, payload.marketing_consent
