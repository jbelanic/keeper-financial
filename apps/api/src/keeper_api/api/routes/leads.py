from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.schemas.leads import LeadInquiryCreate, LeadInquiryCreated
from keeper_api.services.leads import InvalidLeadAttribution, create_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadInquiryCreated, status_code=status.HTTP_201_CREATED)
def submit_lead(
    payload: LeadInquiryCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> LeadInquiryCreated:
    try:
        lead, marketing_recorded = create_lead(db, payload, request_id=request.state.request_id)
    except InvalidLeadAttribution as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from exc
    return LeadInquiryCreated(
        id=lead.id,
        status=lead.status,
        marketing_consent_recorded=marketing_recorded,
    )
