import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import ConsentRecord
from keeper_api.schemas.leads import (
    ConsentState,
    LeadInquiryCreate,
    LeadInquiryCreated,
    LeadListItem,
    LeadListQuery,
    LeadListResponse,
)
from keeper_api.services.auth import Principal, require_admin
from keeper_api.services.consent_registry import (
    MARKETING_CONSENT,
    SERVICE_CONTACT_CONSENT,
)
from keeper_api.services.lead_notifications import send_lead_notification_emails
from keeper_api.services.leads import (
    InvalidLeadAttribution,
    LeadMarketingConsentNotFound,
    create_lead,
    list_leads,
    withdraw_marketing_consent,
)

router = APIRouter(prefix="/leads", tags=["leads"])
NO_STORE = {"Cache-Control": "no-store"}


@router.post(
    "",
    response_model=LeadInquiryCreated,
    status_code=status.HTTP_201_CREATED,
    responses={429: {"description": "Contact submission rate limit exceeded"}},
)
def submit_lead(
    payload: LeadInquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LeadInquiryCreated:
    try:
        lead, marketing_recorded = create_lead(db, payload, request_id=request.state.request_id)
    except InvalidLeadAttribution as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    send_lead_notification_emails(db, settings=settings, lead=lead)
    return LeadInquiryCreated(
        id=lead.id,
        status=lead.status,
        marketing_consent_recorded=marketing_recorded,
    )


def _consent_state(consent: ConsentRecord) -> ConsentState:
    return ConsentState(
        state="withdrawn" if consent.withdrawn_at else "granted",
        granted_at=consent.granted_at,
        withdrawn_at=consent.withdrawn_at,
    )


@router.get(
    "",
    response_model=LeadListResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
    },
)
def get_leads(
    query: Annotated[LeadListQuery, Query()],
    response: Response,
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LeadListResponse:
    response.headers.update(NO_STORE)
    leads, consents, total = list_leads(
        db,
        lead_status=query.status,
        limit=query.limit,
        offset=query.offset,
    )
    items: list[LeadListItem] = []
    for lead in leads:
        lead_consents = consents.get(lead.id, {})
        service = lead_consents.get(SERVICE_CONTACT_CONSENT.purpose)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="lead consent evidence is unavailable",
                headers=NO_STORE,
            )
        marketing = lead_consents.get(MARKETING_CONSENT.purpose)
        items.append(
            LeadListItem(
                id=lead.id,
                name=lead.name,
                email=lead.email,
                telephone=lead.telephone,
                mortgage_objective=lead.mortgage_objective,
                preferred_contact_method=lead.preferred_contact_method,
                preferred_agent_slug=lead.preferred_agent_slug,
                message=lead.message,
                source=lead.source,
                status=lead.status,
                created_at=lead.created_at,
                service_consent=_consent_state(service),
                marketing_consent=_consent_state(marketing) if marketing else None,
            )
        )
    return LeadListResponse(items=items, total=total, limit=query.limit, offset=query.offset)


@router.post(
    "/{lead_id}/marketing-consent/withdrawal",
    response_model=ConsentState,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
        404: {"description": "Lead or marketing consent unavailable"},
    },
)
def withdraw_lead_marketing_consent(
    lead_id: uuid.UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ConsentState:
    response.headers.update(NO_STORE)
    try:
        consent = withdraw_marketing_consent(
            db,
            lead_id=lead_id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LeadMarketingConsentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="marketing consent is unavailable",
            headers=NO_STORE,
        ) from exc
    return _consent_state(consent)
