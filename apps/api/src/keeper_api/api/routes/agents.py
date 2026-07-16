from __future__ import annotations

import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import AgentProfile
from keeper_api.models.statuses import CandidateStatus
from keeper_api.schemas.agents import (
    AdminAgentProfile,
    AdminAgentProfileList,
    AgentProfileCreate,
    AgentProfileUpdate,
    PublicAgentProfile,
    PublicAgentProfileList,
    PublicAgentProfileSummary,
)
from keeper_api.schemas.lifecycle import AgentStatusResponse, AgentTransitionRequest
from keeper_api.services.agents import (
    AgentProfileConflict,
    AgentProfileLifecycleService,
    InvalidAgentProfileTransition,
    admin_profiles,
    create_profile,
    get_admin_profile,
    public_profile_by_slug,
    public_profiles,
    update_profile,
)
from keeper_api.services.auth import Principal, require_admin

router = APIRouter(tags=["agents"])
NO_STORE = {"Cache-Control": "no-store"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DENIED_AGENT_PRINCIPAL_STATUSES = {
    CandidateStatus.DECLINED,
    CandidateStatus.WITHDRAWN,
    CandidateStatus.SUSPENDED,
    CandidateStatus.OFFBOARDING,
    CandidateStatus.OFFBOARDED,
}


def require_agent_profile_admin(
    principal: Principal = Depends(require_admin),
) -> Principal:
    if principal.candidate_status in DENIED_AGENT_PRINCIPAL_STATUSES:
        raise HTTPException(status_code=403, detail="agent profile access is unavailable")
    return principal


def _admin(profile: AgentProfile) -> AdminAgentProfile:
    return AdminAgentProfile.model_validate(profile, from_attributes=True)


@router.get(
    "/agents",
    response_model=PublicAgentProfileList,
    responses={422: {"description": "Invalid pagination"}},
)
def list_public_agent_profiles(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> PublicAgentProfileList:
    response.headers.update(NO_STORE)
    rows, total = public_profiles(db, limit=limit, offset=offset)
    return PublicAgentProfileList(
        items=[
            PublicAgentProfileSummary.model_validate(item, from_attributes=True) for item in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/agents/{slug}",
    response_model=PublicAgentProfile,
    responses={
        404: {"description": "Published profile not found"},
        422: {"description": "Invalid request"},
    },
)
def get_public_agent_profile(
    slug: str, response: Response, db: Session = Depends(get_db)
) -> PublicAgentProfile:
    response.headers.update(NO_STORE)
    profile = None
    if len(slug) <= 100 and SLUG.fullmatch(slug):
        profile = public_profile_by_slug(db, slug)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    return PublicAgentProfile.model_validate(profile, from_attributes=True)


@router.get(
    "/admin/agent-profiles",
    response_model=AdminAgentProfileList,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        422: {"description": "Invalid pagination"},
    },
)
def list_admin_agent_profiles(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    _: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfileList:
    response.headers.update(NO_STORE)
    rows, total = admin_profiles(db, limit=limit, offset=offset)
    return AdminAgentProfileList(
        items=[_admin(item) for item in rows], total=total, limit=limit, offset=offset
    )


@router.post(
    "/admin/agent-profiles",
    response_model=AdminAgentProfile,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        404: {"description": "Active agent relationship not found"},
        409: {"description": "Profile user or slug conflict"},
        422: {"description": "Invalid profile content"},
    },
)
def create_admin_agent_profile(
    payload: AgentProfileCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfile:
    response.headers.update(NO_STORE)
    try:
        return _admin(
            create_profile(
                db,
                payload,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc), headers=NO_STORE) from exc
    except AgentProfileConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc


@router.get(
    "/admin/agent-profiles/{profile_id}",
    response_model=AdminAgentProfile,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        404: {"description": "Profile not found"},
        422: {"description": "Invalid profile id"},
    },
)
def get_admin_agent_profile(
    profile_id: uuid.UUID,
    response: Response,
    _: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfile:
    response.headers.update(NO_STORE)
    profile = get_admin_profile(db, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    return _admin(profile)


@router.patch(
    "/admin/agent-profiles/{profile_id}",
    response_model=AdminAgentProfile,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin or MFA denied"},
        404: {"description": "Profile not found"},
        409: {"description": "Profile lifecycle or slug conflict"},
        422: {"description": "Invalid profile content"},
    },
)
def patch_admin_agent_profile(
    profile_id: uuid.UUID,
    payload: AgentProfileUpdate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AdminAgentProfile:
    response.headers.update(NO_STORE)
    profile = get_admin_profile(db, profile_id, lock=True)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    try:
        return _admin(
            update_profile(
                db,
                profile,
                payload,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        )
    except AgentProfileConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc


@router.post(
    "/agents/{profile_id}/status",
    response_model=AgentStatusResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin, MFA, or approval denied"},
        404: {"description": "Profile not found"},
        409: {"description": "Invalid profile transition"},
        422: {"description": "Invalid transition request"},
    },
)
def transition_agent_profile(
    profile_id: uuid.UUID,
    payload: AgentTransitionRequest,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_agent_profile_admin),
    db: Session = Depends(get_db),
) -> AgentStatusResponse:
    response.headers.update(NO_STORE)
    profile = get_admin_profile(db, profile_id, lock=True)
    if profile is None:
        raise HTTPException(status_code=404, detail="agent profile not found", headers=NO_STORE)
    try:
        AgentProfileLifecycleService(db).transition(
            profile,
            payload.status,
            actor_user_id=principal.user_id,
            actor_can_approve="brokerage_admin" in principal.roles,
            reason=payload.reason,
            request_id=request.state.request_id,
        )
    except InvalidAgentProfileTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
    return AgentStatusResponse(status=payload.status)
