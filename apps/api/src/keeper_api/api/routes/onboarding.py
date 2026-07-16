from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import CandidateEsignEnvelope, CandidateOnboardingTask
from keeper_api.models.statuses import EsignEnvelopeStatus
from keeper_api.schemas.review_onboarding import (
    CandidateOnboardingTaskResponse,
    ControlledDocumentResponse,
    DocumentVersionResponse,
    OnboardingTaskResponse,
    PlanSummary,
    PlanWithTasks,
)
from keeper_api.services.auth import Principal, require_admin
from keeper_api.services.onboarding import (
    OnboardingError,
    link_esign_envelope,
    list_controlled_documents,
    review_task,
    satisfy_gate,
    update_esign_envelope,
)
from keeper_api.services.review import (
    get_review_candidate,
)

router = APIRouter(prefix="/admin/onboarding", tags=["admin onboarding"])
NO_STORE = {"Cache-Control": "no-store"}


class TaskReviewIn(BaseModel):
    model_config = {"extra": "forbid"}
    approved: bool
    review_notes: str | None = Field(default=None, max_length=1000)


class EsignLinkIn(BaseModel):
    model_config = {"extra": "forbid"}
    envelope_url: str = Field(min_length=1, max_length=2048)
    envelope_id: str | None = Field(default=None, max_length=255)
    document_version_id: uuid.UUID | None = None
    status: EsignEnvelopeStatus


class EsignUpdateIn(BaseModel):
    model_config = {"extra": "forbid"}
    envelope_id: str | None = Field(default=None, max_length=255)
    envelope_url: str | None = Field(default=None, max_length=2048)
    status: EsignEnvelopeStatus


class GateSatisfyIn(BaseModel):
    model_config = {"extra": "forbid"}
    code: str = Field(min_length=1, max_length=64)


class TaskTemplateIn(BaseModel):
    model_config = {"extra": "forbid"}
    title: str = Field(min_length=1, max_length=160)
    instructions: str = Field(default="", max_length=2000)
    is_required: bool = True


class PlanCreateIn(BaseModel):
    model_config = {"extra": "forbid"}
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    tasks: list[TaskTemplateIn] = Field(default_factory=list, max_length=100)


def _plan_out(plan: object) -> PlanWithTasks:
    from keeper_api.models.domain import OnboardingPlan as Plan

    assert isinstance(plan, Plan)
    tasks = sorted(plan.tasks, key=lambda t: t.sequence)
    return PlanWithTasks(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        is_active=plan.is_active,
        tasks=[
            OnboardingTaskResponse(
                id=t.id,
                plan_id=t.plan_id,
                title=t.title,
                instructions=t.instructions,
                sequence=t.sequence,
                is_required=t.is_required,
            )
            for t in tasks
        ],
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post(
    "/plans",
    response_model=PlanWithTasks,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def create_plan(
    payload: PlanCreateIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PlanWithTasks:
    response.headers.update(NO_STORE)
    from keeper_api.models.domain import OnboardingTask

    task_objs = [
        OnboardingTask(
            title=t.title, instructions=t.instructions, is_required=t.is_required, sequence=i + 1
        )
        for i, t in enumerate(payload.tasks)
    ]
    from keeper_api.services.onboarding import create_onboarding_plan

    plan = create_onboarding_plan(
        db,
        name=payload.name,
        description=payload.description,
        tasks=task_objs,
        actor_user_id=principal.user_id,
        request_id=request.state.request_id,
    )
    return _plan_out(plan)


@router.get(
    "/plans",
    response_model=list[PlanSummary],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def list_plans(
    response: Response,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[PlanSummary]:
    response.headers.update(NO_STORE)
    from keeper_api.services.onboarding import list_onboarding_plans

    plans, _ = list_onboarding_plans(db, limit=limit, offset=offset)
    return [
        PlanSummary(id=p.id, name=p.name, description=p.description, is_active=p.is_active)
        for p in plans
    ]


@router.get(
    "/plans/{plan_id}",
    response_model=PlanWithTasks,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Plan not found"},
    },
)
def get_plan(
    plan_id: uuid.UUID,
    response: Response,
    _principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PlanWithTasks:
    response.headers.update(NO_STORE)
    from keeper_api.services.onboarding import get_onboarding_plan

    try:
        plan = get_onboarding_plan(db, plan_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="plan not found") from exc
    return _plan_out(plan)


@router.post(
    "/candidates/{candidate_id}/tasks/{task_id}/review",
    response_model=CandidateOnboardingTaskResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Not found"},
        409: {"description": "Not in a reviewable state"},
    },
)
def review_candidate_task(
    candidate_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskReviewIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> CandidateOnboardingTaskResponse:
    response.headers.update(NO_STORE)
    task = db.get(CandidateOnboardingTask, task_id)
    if task is None or task.candidate_id != candidate_id:
        raise HTTPException(status_code=404, detail="task not found")
    try:
        task = review_task(
            db,
            task=task,
            approved=payload.approved,
            review_notes=payload.review_notes,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CandidateOnboardingTaskResponse.model_validate(task, from_attributes=True)


@router.post(
    "/candidates/{candidate_id}/esign-envelopes",
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Candidate not found"},
    },
)
def link_envelope(
    candidate_id: uuid.UUID,
    payload: EsignLinkIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    envelope = link_esign_envelope(
        db,
        candidate=candidate,
        envelope_id=payload.envelope_id,
        envelope_url=payload.envelope_url,
        document_version_id=payload.document_version_id,
        status=payload.status,
        actor_user_id=principal.user_id,
        request_id=request.state.request_id,
    )
    return {"envelope_id": str(envelope.id), "status": envelope.status}


@router.patch(
    "/candidates/{candidate_id}/esign-envelopes/{envelope_id}",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Not found"},
    },
)
def update_envelope(
    candidate_id: uuid.UUID,
    envelope_id: uuid.UUID,
    payload: EsignUpdateIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    response.headers.update(NO_STORE)
    envelope = db.get(CandidateEsignEnvelope, envelope_id)
    if envelope is None or envelope.candidate_id != candidate_id:
        raise HTTPException(status_code=404, detail="envelope not found")
    update_esign_envelope(
        db,
        envelope=envelope,
        envelope_id=payload.envelope_id,
        envelope_url=payload.envelope_url,
        status=payload.status,
        actor_user_id=principal.user_id,
        request_id=request.state.request_id,
    )
    return {"envelope_id": str(envelope.id), "status": envelope.status}


@router.post(
    "/candidates/{candidate_id}/gates",
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Candidate not found"},
        409: {"description": "Unknown gate"},
    },
)
def satisfy_activation_gate(
    candidate_id: uuid.UUID,
    payload: GateSatisfyIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    response.headers.update(NO_STORE)
    try:
        candidate = get_review_candidate(db, candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="candidate not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        gate = satisfy_gate(
            db,
            candidate=candidate,
            code=payload.code,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"candidate_id": str(candidate.id), "code": gate.code, "status": gate.status}


@router.get(
    "/documents",
    response_model=list[ControlledDocumentResponse],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def list_documents(
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ControlledDocumentResponse]:
    response.headers.update(NO_STORE)
    documents, _ = list_controlled_documents(db)
    out: list[ControlledDocumentResponse] = []
    for doc in documents:
        version = next((v for v in doc.versions if v.superseded_at is None), None)
        out.append(
            ControlledDocumentResponse(
                id=doc.id,
                key=doc.key,
                title=doc.title,
                description=doc.description,
                requires_acknowledgement=doc.requires_acknowledgement,
                current_version=(
                    DocumentVersionResponse.model_validate(version, from_attributes=True)
                    if version
                    else None
                ),
            )
        )
    return out
