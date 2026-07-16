from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import Candidate
from keeper_api.models.statuses import CandidateStatus, InterviewStatus
from keeper_api.schemas.review_onboarding import (
    CandidateDecisionRequest,
    CandidateDetailResponse,
    CandidateQueueResponse,
    CandidateReviewSummary,
    InformationRequestCreate,
    InformationRequestResponse,
    InterviewStatusUpdate,
)
from keeper_api.services.auth import Principal, require_admin
from keeper_api.services.onboarding import (
    assign_onboarding_plan,
    get_onboarding_plan,
)
from keeper_api.services.review import (
    CandidateProfileView,
    ReviewError,
    candidate_profile,
    candidate_review_queue,
    decide_candidate,
    get_review_candidate,
    record_interview_status,
    record_withdrawal,
    request_information,
)

router = APIRouter(prefix="/admin/candidates", tags=["admin review"])
NO_STORE = {"Cache-Control": "no-store"}


def _summary(candidate: Candidate, profile: CandidateProfileView) -> CandidateReviewSummary:
    return CandidateReviewSummary(
        candidate_id=candidate.id,
        status=CandidateStatus(candidate.status),
        given_name=profile.given_name,
        family_name=profile.family_name,
        email=profile.email,
        interview_status=InterviewStatus(candidate.interview_status)
        if candidate.interview_status
        else None,
        assigned_onboarding_plan_id=candidate.assigned_onboarding_plan_id,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


def _detail(candidate: Candidate, profile: CandidateProfileView) -> CandidateDetailResponse:
    return CandidateDetailResponse(
        candidate_id=candidate.id,
        status=CandidateStatus(candidate.status),
        given_name=profile.given_name,
        family_name=profile.family_name,
        email=profile.email,
        interview_status=InterviewStatus(candidate.interview_status)
        if candidate.interview_status
        else None,
        interview_notes=candidate.interview_notes,
        interview_recorded_at=candidate.interview_recorded_at,
        assigned_onboarding_plan_id=candidate.assigned_onboarding_plan_id,
        assigned_onboarding_at=candidate.assigned_onboarding_at,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at,
    )


@router.get(
    "",
    response_model=CandidateQueueResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def list_review_queue(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    status_filter: Annotated[CandidateStatus | None, Query(alias="status")] = None,
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CandidateQueueResponse:
    response.headers.update(NO_STORE)
    candidates, total = candidate_review_queue(db, limit=limit, offset=offset, status=status_filter)
    return CandidateQueueResponse(
        items=[_summary(item, candidate_profile(db, item)) for item in candidates],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetailResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied or candidate access unavailable"},
        404: {"description": "Candidate not found"},
    },
)
def get_candidate_detail(
    candidate_id: uuid.UUID,
    response: Response,
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CandidateDetailResponse:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _detail(candidate, candidate_profile(db, candidate))


@router.post(
    "/{candidate_id}/interview",
    response_model=CandidateDetailResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied or candidate access unavailable"},
        404: {"description": "Candidate not found"},
        409: {"description": "Lifecycle conflict"},
    },
)
def set_interview_status(
    candidate_id: uuid.UUID,
    payload: InterviewStatusUpdate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CandidateDetailResponse:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
        candidate = record_interview_status(
            db,
            candidate=candidate,
            interview_status=payload.interview_status,
            notes=payload.notes,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ReviewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _detail(candidate, candidate_profile(db, candidate))


@router.post(
    "/{candidate_id}/information-requests",
    response_model=InformationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied or candidate access unavailable"},
        404: {"description": "Candidate not found"},
        409: {"description": "Lifecycle conflict"},
        422: {"description": "Validation failed"},
    },
)
def create_information_request(
    candidate_id: uuid.UUID,
    payload: InformationRequestCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> InformationRequestResponse:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
        request_record = request_information(
            db,
            candidate=candidate,
            message=payload.message,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ReviewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return InformationRequestResponse.model_validate(request_record, from_attributes=True)


@router.post(
    "/{candidate_id}/decision",
    response_model=CandidateDetailResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied or candidate access unavailable"},
        404: {"description": "Candidate not found"},
        409: {"description": "Invalid transition or required reason missing"},
    },
)
def decide_candidate_status(
    candidate_id: uuid.UUID,
    payload: CandidateDecisionRequest,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CandidateDetailResponse:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
        if payload.decision == CandidateStatus.WITHDRAWN:
            candidate = record_withdrawal(
                db,
                candidate=candidate,
                reason=payload.reason,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        else:
            candidate = decide_candidate(
                db,
                candidate=candidate,
                decision=payload.decision,
                reason=payload.reason,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ReviewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _detail(candidate, candidate_profile(db, candidate))


@router.post(
    "/{candidate_id}/assign-onboarding",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied or candidate access unavailable"},
        404: {"description": "Candidate or plan not found"},
        409: {"description": "Assignment conflict"},
    },
)
def assign_onboarding(
    candidate_id: uuid.UUID,
    plan_id: uuid.UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
        plan = get_onboarding_plan(db, plan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate or plan not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        assignment = assign_onboarding_plan(
            db,
            candidate=candidate,
            plan=plan,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except ReviewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "assignment_id": str(assignment.id),
        "candidate_id": str(candidate.id),
        "onboarding_plan_id": str(plan.id),
        "status": assignment.status,
    }
