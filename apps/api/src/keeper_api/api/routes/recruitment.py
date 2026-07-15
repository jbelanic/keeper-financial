from __future__ import annotations

import re
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import RecruitmentPosting
from keeper_api.schemas.candidate_applications import CandidateApplicationResponse
from keeper_api.schemas.recruitment import (
    AdminPosting,
    AdminPostingList,
    PostingCreate,
    PostingUpdate,
    PublicPosting,
    PublicPostingList,
    PublicPostingSummary,
)
from keeper_api.services.auth import (
    ExternalIdentity,
    Principal,
    get_verified_external_identity,
    require_admin,
)
from keeper_api.services.candidate_applications import (
    CandidateApplicationConflict,
    candidate_application_response,
    provision_application,
)
from keeper_api.services.recruitment import (
    PostingConflict,
    create_posting,
    public_postings,
    transition_posting,
    update_posting,
)

router = APIRouter(tags=["recruitment"])
NO_STORE = {"Cache-Control": "no-store"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _admin(posting: RecruitmentPosting) -> AdminPosting:
    return AdminPosting.model_validate(posting, from_attributes=True)


def _get_admin_posting(db: Session, posting_id: uuid.UUID) -> RecruitmentPosting:
    posting = db.get(RecruitmentPosting, posting_id)
    if posting is None:
        raise HTTPException(status_code=404, detail="posting not found", headers=NO_STORE)
    return posting


@router.get("/recruitment/postings", response_model=PublicPostingList)
def list_public_postings(
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> PublicPostingList:
    rows, total = public_postings(db, limit=limit, offset=offset)
    return PublicPostingList(
        items=[PublicPostingSummary.model_validate(item, from_attributes=True) for item in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/recruitment/postings/{slug}/applications/start",
    response_model=CandidateApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Verified identity required"},
        404: {"description": "Posting unavailable"},
        409: {"description": "Identity conflict"},
    },
)
def start_candidate_application(
    slug: str,
    request: Request,
    response: Response,
    identity: ExternalIdentity = Depends(get_verified_external_identity),
    db: Session = Depends(get_db),
) -> CandidateApplicationResponse:
    if not identity.verified:
        raise HTTPException(status_code=403, detail="verified provider identity is required")
    try:
        application, created = provision_application(
            db, identity=identity, posting_slug=slug, request_id=request.state.request_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="posting not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except CandidateApplicationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not created:
        response.status_code = status.HTTP_200_OK
    return candidate_application_response(db, application)


@router.get("/recruitment/postings/{slug:path}", response_model=PublicPosting)
def get_public_posting(slug: str, db: Session = Depends(get_db)) -> PublicPosting:
    posting = None
    if len(slug) <= 100 and SLUG.fullmatch(slug):
        posting = db.scalar(
            select(RecruitmentPosting).where(
                RecruitmentPosting.slug == slug, RecruitmentPosting.status == "published"
            )
        )
    if posting is None:
        raise HTTPException(status_code=404, detail="posting not found")
    return PublicPosting.model_validate(posting, from_attributes=True)


@router.get(
    "/admin/recruitment-postings",
    response_model=AdminPostingList,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def list_admin_postings(
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    _: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminPostingList:
    response.headers.update(NO_STORE)
    total = db.scalar(select(func.count()).select_from(RecruitmentPosting)) or 0
    rows = db.scalars(
        select(RecruitmentPosting)
        .order_by(RecruitmentPosting.created_at.desc(), RecruitmentPosting.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return AdminPostingList(
        items=[_admin(item) for item in rows], total=total, limit=limit, offset=offset
    )


@router.post(
    "/admin/recruitment-postings",
    response_model=AdminPosting,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        409: {"description": "Conflict"},
    },
)
def create_admin_posting(
    payload: PostingCreate,
    request: Request,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminPosting:
    try:
        return _admin(
            create_posting(
                db,
                payload,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        )
    except PostingConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc


@router.patch(
    "/admin/recruitment-postings/{posting_id}",
    response_model=AdminPosting,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Posting not found"},
        409: {"description": "Posting lifecycle or slug conflict"},
    },
)
def patch_admin_posting(
    posting_id: uuid.UUID,
    payload: PostingUpdate,
    request: Request,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminPosting:
    try:
        return _admin(
            update_posting(
                db,
                _get_admin_posting(db, posting_id),
                payload,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        )
    except PostingConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc


@router.post(
    "/admin/recruitment-postings/{posting_id}/{action}",
    response_model=AdminPosting,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Posting not found"},
        409: {"description": "Posting lifecycle conflict"},
    },
)
def transition_admin_posting(
    posting_id: uuid.UUID,
    action: Literal["publish", "close", "archive"],
    request: Request,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminPosting:
    try:
        return _admin(
            transition_posting(
                db,
                _get_admin_posting(db, posting_id),
                {"publish": "published", "close": "closed", "archive": "archived"}[action],
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
            )
        )
    except PostingConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc), headers=NO_STORE) from exc
