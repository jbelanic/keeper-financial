import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import AgentProfile
from keeper_api.schemas.lifecycle import AgentStatusResponse, AgentTransitionRequest
from keeper_api.services.agents import AgentProfileLifecycleService, InvalidAgentProfileTransition
from keeper_api.services.auth import Principal, require_admin

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/{profile_id}/status", response_model=AgentStatusResponse)
def transition_agent_profile(
    profile_id: uuid.UUID,
    payload: AgentTransitionRequest,
    request: Request,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AgentStatusResponse:
    profile = db.get(AgentProfile, profile_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent profile not found")
    try:
        AgentProfileLifecycleService(db).transition(
            profile,
            payload.status,
            actor_user_id=principal.user_id,
            actor_can_approve="brokerage_admin" in principal.roles,
            request_id=request.state.request_id,
        )
    except InvalidAgentProfileTransition as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AgentStatusResponse(status=payload.status)
