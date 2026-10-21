import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import ConsentRecord
from keeper_api.schemas.leads import (
    ConsentState,
    LeadAssignableAgent,
    LeadAssignableAgentList,
    LeadAssignmentUpdate,
    LeadInquiryCreate,
    LeadInquiryCreated,
    LeadListItem,
    LeadListQuery,
    LeadListResponse,
    LeadStatusUpdate,
    LeadStatusUpdated,
)
from keeper_api.services.auth import Principal, require_admin
from keeper_api.services.consent_registry import (
    MARKETING_CONSENT,
    SERVICE_CONTACT_CONSENT,
)
from keeper_api.services.lead_notifications import send_lead_notification_emails
from keeper_api.services.leads import (
    LeadAssignmentInvalid,
    LeadInquiryNotFound,
    LeadMarketingConsentNotFound,
    assign_lead,
    assigned_agent_names,
    create_lead,
    list_assignable_agents,
    list_leads,
    update_lead_status,
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
    # An unknown or ineligible agent reference resolves to no attribution and is
    # treated exactly like a submission without one, so a code cannot be probed.
    lead, marketing_recorded = create_lead(db, payload, request_id=request.state.request_id)
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
    agent_names = assigned_agent_names(db, leads)
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
                assigned_agent_user_id=lead.assigned_agent_user_id,
                assigned_agent_name=(
                    agent_names.get(lead.assigned_agent_user_id)
                    if lead.assigned_agent_user_id
                    else None
                ),
                assigned_at=lead.assigned_at,
                attribution_source=lead.attribution_source,
                created_at=lead.created_at,
                service_consent=_consent_state(service),
                marketing_consent=_consent_state(marketing) if marketing else None,
            )
        )
    return LeadListResponse(items=items, total=total, limit=query.limit, offset=query.offset)


@router.get(
    "/assignable-agents",
    response_model=LeadAssignableAgentList,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
    },
)
def list_lead_assignable_agents(
    response: Response,
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LeadAssignableAgentList:
    """Onboarded agents an inquiry may be assigned to."""
    response.headers.update(NO_STORE)
    return LeadAssignableAgentList(
        items=[
            LeadAssignableAgent(
                user_id=user_id,
                display_name=display_name,
                email=email,
                has_referral_link=has_link,
            )
            for user_id, display_name, email, has_link in list_assignable_agents(db)
        ]
    )


@router.post(
    "/{lead_id}/assignment",
    response_model=LeadStatusUpdated,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
        404: {"description": "Lead unavailable"},
        409: {"description": "Selected account is not an onboarded agent"},
    },
)
def assign_lead_agent(
    lead_id: uuid.UUID,
    payload: LeadAssignmentUpdate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LeadStatusUpdated:
    """Assign the inquiry to one onboarded agent, or clear the assignment."""
    response.headers.update(NO_STORE)
    try:
        lead = assign_lead(
            db,
            lead_id=lead_id,
            agent_user_id=payload.agent_user_id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LeadInquiryNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="lead is unavailable",
            headers=NO_STORE,
        ) from exc
    except LeadAssignmentInvalid as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
            headers=NO_STORE,
        ) from exc
    return LeadStatusUpdated(id=lead.id, status=lead.status)


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


@router.post(
    "/{lead_id}/status",
    response_model=LeadStatusUpdated,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Administrator access denied"},
        404: {"description": "Lead unavailable"},
    },
)
def update_admin_lead_status(
    lead_id: uuid.UUID,
    payload: LeadStatusUpdate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> LeadStatusUpdated:
    response.headers.update(NO_STORE)
    try:
        lead = update_lead_status(
            db,
            lead_id=lead_id,
            status=payload.status,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LeadInquiryNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="lead is unavailable",
            headers=NO_STORE,
        ) from exc
    return LeadStatusUpdated(id=lead.id, status=lead.status)
