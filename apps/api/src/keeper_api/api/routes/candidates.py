import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import Candidate
from keeper_api.schemas.lifecycle import CandidateStatusResponse, CandidateTransitionRequest
from keeper_api.services.auth import Principal, require_admin
from keeper_api.services.candidates import CandidateLifecycleService, InvalidCandidateTransition

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("/{candidate_id}/status", response_model=CandidateStatusResponse)
def transition_candidate(
    candidate_id: uuid.UUID,
    payload: CandidateTransitionRequest,
    request: Request,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CandidateStatusResponse:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="candidate not found")
    try:
        CandidateLifecycleService(db).transition(
            candidate,
            payload.status,
            actor_user_id=principal.user_id,
            reason=payload.reason,
            request_id=request.state.request_id,
        )
    except InvalidCandidateTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CandidateStatusResponse(status=payload.status)
