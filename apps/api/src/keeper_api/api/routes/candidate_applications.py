from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import CandidateApplication
from keeper_api.schemas.candidate_applications import (
    ApplicationAction,
    ApplicationDraftUpdate,
    ApplicationListResponse,
    CandidateApplicationResponse,
    CandidatePrivacyDisclosureResponse,
    CandidateStatusListResponse,
    CandidateVisibleApplicationStatus,
)
from keeper_api.services.auth import Principal, require_candidate
from keeper_api.services.candidate_applications import (
    CandidateApplicationConflict,
    CandidateApplicationInvalid,
    candidate_application_response,
    owned_application,
    save_draft,
    submit_application,
    withdraw_application,
)
from keeper_api.services.candidate_privacy import CANDIDATE_PRIVACY_DISCLOSURE

router = APIRouter(prefix="/candidate/applications", tags=["candidate applications"])
privacy_router = APIRouter(prefix="/candidate", tags=["candidate applications"])
NO_STORE = {"Cache-Control": "private, no-store"}
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Authentication required"},
    403: {"description": "Candidate access denied"},
}
OWNED_RESPONSES: dict[int | str, dict[str, Any]] = {
    **AUTH_RESPONSES,
    404: {"description": "Owned application not found"},
}


@privacy_router.get(
    "/privacy-disclosure",
    response_model=CandidatePrivacyDisclosureResponse,
    responses=AUTH_RESPONSES,
)
def candidate_privacy_disclosure(
    response: Response,
    _principal: Principal = Depends(require_candidate),
) -> CandidatePrivacyDisclosureResponse:
    response.headers.update(NO_STORE)
    return CandidatePrivacyDisclosureResponse(
        title=CANDIDATE_PRIVACY_DISCLOSURE.title,
        version=CANDIDATE_PRIVACY_DISCLOSURE.version,
        paragraphs=list(CANDIDATE_PRIVACY_DISCLOSURE.paragraphs),
    )


def _response(db: Session, application: CandidateApplication) -> CandidateApplicationResponse:
    return candidate_application_response(db, application)


def _owned(
    db: Session, application_id: uuid.UUID, principal: Principal, *, lock: bool = False
) -> CandidateApplication:
    if principal.candidate_id is None:
        raise HTTPException(
            status_code=403, detail="candidate access is required", headers=NO_STORE
        )
    try:
        return owned_application(db, application_id, principal.candidate_id, lock=lock)
    except LookupError as exc:
        raise HTTPException(
            status_code=404, detail="application not found", headers=NO_STORE
        ) from exc


@router.get("", response_model=ApplicationListResponse, responses=AUTH_RESPONSES)
def list_candidate_applications(
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> ApplicationListResponse:
    response.headers.update(NO_STORE)
    rows = db.scalars(
        select(CandidateApplication)
        .where(CandidateApplication.candidate_id == principal.candidate_id)
        .order_by(CandidateApplication.created_at, CandidateApplication.id)
    ).all()
    return ApplicationListResponse(applications=[_response(db, item) for item in rows])


@router.get("/status", response_model=CandidateStatusListResponse, responses=AUTH_RESPONSES)
def candidate_status(
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateStatusListResponse:
    response.headers.update(NO_STORE)
    rows = db.scalars(
        select(CandidateApplication)
        .where(CandidateApplication.candidate_id == principal.candidate_id)
        .order_by(CandidateApplication.created_at, CandidateApplication.id)
    ).all()
    return CandidateStatusListResponse(
        applications=[
            CandidateVisibleApplicationStatus(
                application_id=item.id, status=item.status, messages=[]
            )
            for item in rows
        ]
    )


@router.get(
    "/{application_id}",
    response_model=CandidateApplicationResponse,
    responses=OWNED_RESPONSES,
)
def get_candidate_application(
    application_id: uuid.UUID,
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateApplicationResponse:
    response.headers.update(NO_STORE)
    return _response(db, _owned(db, application_id, principal))


@router.patch(
    "/{application_id}",
    response_model=CandidateApplicationResponse,
    responses={
        **OWNED_RESPONSES,
        409: {"description": "Application revision or lifecycle conflict"},
        422: {"description": "Draft validation failed"},
    },
)
def patch_candidate_application(
    application_id: uuid.UUID,
    payload: ApplicationDraftUpdate,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateApplicationResponse:
    try:
        application = save_draft(db, _owned(db, application_id, principal, lock=True), payload)
    except CandidateApplicationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
    except CandidateApplicationInvalid as exc:
        raise HTTPException(status_code=422, detail=str(exc), headers=NO_STORE) from exc
    return _response(db, application)


@router.post(
    "/{application_id}/submit",
    response_model=CandidateApplicationResponse,
    responses={
        **OWNED_RESPONSES,
        409: {"description": "Application revision or lifecycle conflict"},
        422: {"description": "Required submission content is incomplete"},
    },
)
def submit_candidate_application(
    application_id: uuid.UUID,
    payload: ApplicationAction,
    request: Request,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateApplicationResponse:
    try:
        application = submit_application(
            db,
            _owned(db, application_id, principal, lock=True),
            expected_revision=payload.expected_revision,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except CandidateApplicationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
    except CandidateApplicationInvalid as exc:
        raise HTTPException(status_code=422, detail=str(exc), headers=NO_STORE) from exc
    return _response(db, application)


@router.post(
    "/{application_id}/withdraw",
    response_model=CandidateApplicationResponse,
    responses={
        **OWNED_RESPONSES,
        409: {"description": "Application revision or lifecycle conflict"},
    },
)
def withdraw_candidate_application(
    application_id: uuid.UUID,
    payload: ApplicationAction,
    request: Request,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateApplicationResponse:
    try:
        application = withdraw_application(
            db,
            _owned(db, application_id, principal, lock=True),
            expected_revision=payload.expected_revision,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except CandidateApplicationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
    return _response(db, application)
