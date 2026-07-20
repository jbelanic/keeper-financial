from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import (
    CandidateApplication,
    CandidateEsignEnvelope,
    CandidateOnboardingAssignment,
    CandidateOnboardingTask,
    OnboardingPlan,
    OnboardingTask,
)
from keeper_api.schemas.review_onboarding import (
    ActivationGateResponse,
    AdminOnboardingAssignmentDetail,
    AdminOnboardingAssignmentSummary,
    CandidateOnboardingTaskResponse,
    ControlledDocumentResponse,
    DocumentVersionResponse,
    EsignEnvelopeCreate,
    EsignEnvelopeResponse,
    GateReopenRequest,
    ManualGateEvidenceCreate,
    OnboardingPlanCreate,
    OnboardingTaskResponse,
    PlanSummary,
    PlanWithTasks,
)
from keeper_api.services.auth import Principal, require_admin
from keeper_api.services.documenso import DocumensoError
from keeper_api.services.onboarding import (
    DERIVED_GATE_CODES,
    OnboardingError,
    activation_ready,
    candidate_esign_envelopes,
    candidate_gates,
    get_candidate_tasks,
    link_esign_envelope,
    list_controlled_documents,
    refresh_esign_envelope,
    reopen_gate,
    replace_esign_envelope,
    review_task,
    satisfy_gate,
    set_onboarding_plan_active,
    update_onboarding_plan,
)

router = APIRouter(prefix="/admin/onboarding", tags=["admin onboarding"])
NO_STORE = {"Cache-Control": "no-store"}


class TaskReviewIn(BaseModel):
    model_config = {"extra": "forbid"}
    approved: bool
    review_notes: str | None = Field(default=None, max_length=1000)


class PlanAvailabilityIn(BaseModel):
    model_config = {"extra": "forbid"}
    is_active: bool


class PlanCreateIn(OnboardingPlanCreate):
    pass


class PlanUpdateIn(PlanCreateIn):
    pass


def _plan_is_locked(db: Session, plan_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(CandidateOnboardingAssignment.id)
            .where(CandidateOnboardingAssignment.onboarding_plan_id == plan_id)
            .limit(1)
        )
        is not None
    )


def _plan_out(db: Session, plan: object) -> PlanWithTasks:
    from keeper_api.models.domain import OnboardingPlan as Plan

    assert isinstance(plan, Plan)
    tasks = sorted(plan.tasks, key=lambda t: t.sequence)
    return PlanWithTasks(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        is_active=plan.is_active,
        is_locked=_plan_is_locked(db, plan.id),
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


def _gate_out(gate: object) -> ActivationGateResponse:
    from keeper_api.models.domain import ProgrammaticGate

    assert isinstance(gate, ProgrammaticGate)
    return ActivationGateResponse(
        id=gate.id,
        candidate_id=gate.candidate_id,
        assignment_id=gate.assignment_id,
        code=gate.code,
        label=gate.label,
        status=gate.status,
        satisfied_at=gate.satisfied_at,
        evidence_kind="derived" if gate.code in DERIVED_GATE_CODES else "manual",
    )


def _assignment_row(
    db: Session, assignment_id: uuid.UUID
) -> tuple[CandidateOnboardingAssignment, CandidateApplication, OnboardingPlan]:
    row = db.execute(
        select(CandidateOnboardingAssignment, CandidateApplication, OnboardingPlan)
        .join(
            CandidateApplication,
            CandidateApplication.id == CandidateOnboardingAssignment.application_id,
        )
        .join(
            OnboardingPlan,
            OnboardingPlan.id == CandidateOnboardingAssignment.onboarding_plan_id,
        )
        .where(CandidateOnboardingAssignment.id == assignment_id)
    ).one_or_none()
    if row is None:
        raise LookupError("onboarding assignment not found")
    return row.tuple()


def _assignment_summary(
    db: Session,
    assignment: CandidateOnboardingAssignment,
    application: CandidateApplication,
    plan: OnboardingPlan,
) -> AdminOnboardingAssignmentSummary:
    name = " ".join(
        item for item in (application.given_name, application.family_name) if item
    ).strip()
    return AdminOnboardingAssignmentSummary(
        assignment_id=assignment.id,
        candidate_id=assignment.candidate_id,
        application_id=application.id,
        candidate_name=name or application.email,
        candidate_email=application.email,
        opportunity_title=application.source_posting_title,
        attempt_number=application.attempt_number,
        plan_name=plan.name,
        status=assignment.status,
        created_at=assignment.created_at,
        activation_ready=activation_ready(
            db,
            candidate_id=assignment.candidate_id,
            assignment_id=assignment.id,
        ),
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
    task_objs = [
        OnboardingTask(
            title=t.title,
            instructions=t.instructions or "",
            is_required=t.is_required,
            sequence=i + 1,
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
    return _plan_out(db, plan)


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

    plans, _ = list_onboarding_plans(db, active_only=False, limit=limit, offset=offset)
    locked_plan_ids = set(
        db.scalars(
            select(CandidateOnboardingAssignment.onboarding_plan_id)
            .where(
                CandidateOnboardingAssignment.onboarding_plan_id.in_([plan.id for plan in plans])
            )
            .distinct()
        ).all()
    )
    return [
        PlanSummary(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            is_active=plan.is_active,
            is_locked=plan.id in locked_plan_ids,
        )
        for plan in plans
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
    return _plan_out(db, plan)


@router.patch(
    "/plans/{plan_id}",
    response_model=PlanWithTasks,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Plan not found"},
        409: {"description": "Referenced plan is immutable"},
    },
)
def update_plan(
    plan_id: uuid.UUID,
    payload: PlanUpdateIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PlanWithTasks:
    response.headers.update(NO_STORE)
    tasks = [
        OnboardingTask(
            title=task.title,
            instructions=task.instructions or "",
            is_required=task.is_required,
            sequence=position,
        )
        for position, task in enumerate(payload.tasks, start=1)
    ]
    try:
        plan = update_onboarding_plan(
            db,
            plan_id=plan_id,
            name=payload.name,
            description=payload.description,
            tasks=tasks,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="plan not found") from exc
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _plan_out(db, plan)


@router.patch(
    "/plans/{plan_id}/availability",
    response_model=PlanWithTasks,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Plan not found"},
    },
)
def update_plan_availability(
    plan_id: uuid.UUID,
    payload: PlanAvailabilityIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PlanWithTasks:
    response.headers.update(NO_STORE)
    plan = db.get(OnboardingPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    try:
        plan = set_onboarding_plan_active(
            db,
            plan=plan,
            is_active=payload.is_active,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _plan_out(db, plan)


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


@router.get(
    "/assignments",
    response_model=list[AdminOnboardingAssignmentSummary],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
    },
)
def list_assignments(
    response: Response,
    _principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[AdminOnboardingAssignmentSummary]:
    response.headers.update(NO_STORE)
    rows = db.execute(
        select(CandidateOnboardingAssignment, CandidateApplication, OnboardingPlan)
        .join(
            CandidateApplication,
            CandidateApplication.id == CandidateOnboardingAssignment.application_id,
        )
        .join(
            OnboardingPlan,
            OnboardingPlan.id == CandidateOnboardingAssignment.onboarding_plan_id,
        )
        .order_by(
            CandidateOnboardingAssignment.created_at.desc(),
            CandidateOnboardingAssignment.id.desc(),
        )
        .limit(100)
    ).all()
    return [
        _assignment_summary(db, assignment, application, plan)
        for assignment, application, plan in rows
    ]


@router.get(
    "/assignments/{assignment_id}",
    response_model=AdminOnboardingAssignmentDetail,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Assignment not found"},
    },
)
def get_assignment(
    assignment_id: uuid.UUID,
    response: Response,
    _principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminOnboardingAssignmentDetail:
    response.headers.update(NO_STORE)
    try:
        assignment, application, plan = _assignment_row(db, assignment_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    summary = _assignment_summary(db, assignment, application, plan)
    return AdminOnboardingAssignmentDetail(
        **summary.model_dump(),
        tasks=[
            CandidateOnboardingTaskResponse.model_validate(task, from_attributes=True)
            for task in get_candidate_tasks(
                db, candidate_id=assignment.candidate_id, assignment_id=assignment.id
            )
        ],
        gates=[
            _gate_out(gate)
            for gate in candidate_gates(
                db, candidate_id=assignment.candidate_id, assignment_id=assignment.id
            )
        ],
        esign_envelopes=[
            EsignEnvelopeResponse.model_validate(envelope, from_attributes=True)
            for envelope in candidate_esign_envelopes(
                db, candidate_id=assignment.candidate_id, assignment_id=assignment.id
            )
        ],
    )


@router.post(
    "/assignments/{assignment_id}/gates/{code}/satisfy",
    response_model=ActivationGateResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Assignment not found"},
        409: {"description": "Gate cannot be satisfied manually"},
    },
)
def satisfy_activation_gate(
    assignment_id: uuid.UUID,
    code: str,
    payload: ManualGateEvidenceCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActivationGateResponse:
    response.headers.update(NO_STORE)
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="onboarding assignment not found")
    try:
        gate = satisfy_gate(
            db,
            assignment=assignment,
            code=code,
            verified_on=payload.verified_on,
            evidence_source=payload.evidence_source,
            evidence_reference=payload.evidence_reference,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _gate_out(gate)


@router.post(
    "/assignments/{assignment_id}/gates/{code}/reopen",
    response_model=ActivationGateResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Assignment not found"},
        409: {"description": "Gate cannot be reopened"},
    },
)
def reopen_activation_gate(
    assignment_id: uuid.UUID,
    code: str,
    payload: GateReopenRequest,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ActivationGateResponse:
    response.headers.update(NO_STORE)
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="onboarding assignment not found")
    try:
        gate = reopen_gate(
            db,
            assignment=assignment,
            code=code,
            reason=payload.reason,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _gate_out(gate)


@router.post(
    "/assignments/{assignment_id}/esign-envelopes",
    response_model=EsignEnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Assignment not found"},
        409: {"description": "Envelope cannot be linked"},
    },
)
def link_envelope(
    assignment_id: uuid.UUID,
    payload: EsignEnvelopeCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EsignEnvelopeResponse:
    response.headers.update(NO_STORE)
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="onboarding assignment not found")
    try:
        envelope = link_esign_envelope(
            db,
            assignment=assignment,
            provider_envelope_id=payload.provider_envelope_id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return EsignEnvelopeResponse.model_validate(envelope, from_attributes=True)


@router.post(
    "/assignments/{assignment_id}/esign-envelopes/{envelope_id}/replace",
    response_model=EsignEnvelopeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Assignment or envelope not found"},
        409: {"description": "Envelope cannot be replaced"},
    },
)
def replace_envelope(
    assignment_id: uuid.UUID,
    envelope_id: uuid.UUID,
    payload: EsignEnvelopeCreate,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
) -> EsignEnvelopeResponse:
    response.headers.update(NO_STORE)
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    envelope = db.get(CandidateEsignEnvelope, envelope_id)
    if assignment is None or envelope is None or envelope.assignment_id != assignment.id:
        raise HTTPException(status_code=404, detail="e-sign envelope not found")
    try:
        replacement = replace_esign_envelope(
            db,
            assignment=assignment,
            envelope=envelope,
            provider_envelope_id=payload.provider_envelope_id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return EsignEnvelopeResponse.model_validate(replacement, from_attributes=True)


@router.post(
    "/assignments/{assignment_id}/esign-envelopes/{envelope_id}/refresh",
    response_model=EsignEnvelopeResponse,
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin denied"},
        404: {"description": "Assignment or envelope not found"},
        409: {"description": "Envelope cannot be refreshed"},
        503: {"description": "Documenso unavailable or returned invalid evidence"},
    },
)
def refresh_envelope(
    assignment_id: uuid.UUID,
    envelope_id: uuid.UUID,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_admin),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EsignEnvelopeResponse:
    response.headers.update(NO_STORE)
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    envelope = db.get(CandidateEsignEnvelope, envelope_id)
    if assignment is None or envelope is None or envelope.assignment_id != assignment.id:
        raise HTTPException(status_code=404, detail="e-sign envelope not found")
    try:
        refreshed = refresh_esign_envelope(
            db,
            assignment=assignment,
            envelope=envelope,
            settings=settings,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except DocumensoError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return EsignEnvelopeResponse.model_validate(refreshed, from_attributes=True)


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
