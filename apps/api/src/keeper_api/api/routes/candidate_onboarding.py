from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.db.session import get_db
from keeper_api.models.domain import (
    Candidate,
    CandidateOnboardingAssignment,
    CandidateOnboardingTask,
    DocumentVersion,
)
from keeper_api.models.statuses import OnboardingAssignmentStatus
from keeper_api.schemas.review_onboarding import (
    ActivationGateResponse,
    CandidateOnboardingAvailability,
    CandidateOnboardingDashboard,
    CandidateOnboardingTaskResponse,
    ControlledDocumentResponse,
    DocumentVersionResponse,
    EsignEnvelopeResponse,
    OnboardingAssignmentResponse,
    PolicyAcknowledgementResponse,
)
from keeper_api.services.auth import Principal, require_candidate
from keeper_api.services.onboarding import (
    DERIVED_GATE_CODES,
    OnboardingError,
    acknowledge_policy,
    activation_ready,
    candidate_acknowledgements,
    candidate_assigned_documents,
    candidate_esign_envelopes,
    candidate_gates,
    get_candidate_tasks,
    submit_task_evidence,
)
from keeper_api.services.review import CandidateLifecycleService

router = APIRouter(prefix="/candidate/onboarding", tags=["candidate onboarding"])
NO_STORE = {"Cache-Control": "private, no-store"}
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Authentication required"},
    403: {"description": "Candidate access denied"},
}


def _candidate(principal: Principal, db: Session) -> Candidate:
    if principal.candidate_id is None:
        raise HTTPException(status_code=403, detail="candidate access denied")
    candidate = db.get(Candidate, principal.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    CandidateLifecycleService(db).assert_admin_accessible(candidate)
    return candidate


class TaskEvidenceIn(BaseModel):
    model_config = {"extra": "forbid"}
    evidence: str = Field(min_length=1, max_length=2000)


class PolicyAckIn(BaseModel):
    model_config = {"extra": "forbid"}
    document_version_id: uuid.UUID
    wording: str = Field(min_length=1, max_length=1000)


@router.get(
    "/availability",
    response_model=CandidateOnboardingAvailability,
    responses=AUTH_RESPONSES,
)
def onboarding_availability(
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateOnboardingAvailability:
    response.headers.update(NO_STORE)
    candidate = _candidate(principal, db)
    assignment_id = db.scalar(
        select(CandidateOnboardingAssignment.id).where(
            CandidateOnboardingAssignment.candidate_id == candidate.id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
            CandidateOnboardingAssignment.application_id.is_not(None),
        )
    )
    return CandidateOnboardingAvailability(available=assignment_id is not None)


@router.get(
    "",
    response_model=CandidateOnboardingDashboard,
    responses=AUTH_RESPONSES,
)
def onboarding_dashboard(
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> CandidateOnboardingDashboard:
    response.headers.update(NO_STORE)
    candidate = _candidate(principal, db)
    assignment = db.scalar(
        select(CandidateOnboardingAssignment).where(
            CandidateOnboardingAssignment.candidate_id == candidate.id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
        )
    )
    if assignment is None or assignment.application_id is None:
        return CandidateOnboardingDashboard(
            assignment=None,
            tasks=[],
            gates=[],
            documents=[],
            acknowledgements=[],
            esign_envelopes=[],
            activation_ready=False,
        )
    documents = candidate_assigned_documents(db, candidate_id=candidate.id)
    return CandidateOnboardingDashboard(
        assignment=_assignment_out(assignment),
        tasks=[
            _task_out(t)
            for t in get_candidate_tasks(db, candidate_id=candidate.id, assignment_id=assignment.id)
        ],
        gates=[
            _gate_out(g)
            for g in candidate_gates(db, candidate_id=candidate.id, assignment_id=assignment.id)
        ],
        documents=[_doc_out(document, version) for document, version in documents],
        acknowledgements=[
            _ack_out(a)
            for a in candidate_acknowledgements(
                db, candidate_id=candidate.id, assignment_id=assignment.id
            )
        ],
        esign_envelopes=[
            _esign_out(e)
            for e in candidate_esign_envelopes(
                db, candidate_id=candidate.id, assignment_id=assignment.id
            )
        ],
        activation_ready=activation_ready(
            db, candidate_id=candidate.id, assignment_id=assignment.id
        ),
    )


@router.post(
    "/tasks/{task_id}/evidence",
    responses={
        **AUTH_RESPONSES,
        404: {"description": "Task not found"},
        409: {"description": "Task not in a submittable state"},
    },
)
def submit_evidence(
    task_id: uuid.UUID,
    payload: TaskEvidenceIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    response.headers.update(NO_STORE)
    candidate = _candidate(principal, db)
    task = db.get(CandidateOnboardingTask, task_id)
    if task is None or task.candidate_id != candidate.id:
        raise HTTPException(status_code=404, detail="task not found")
    try:
        submit_task_evidence(
            db,
            candidate=candidate,
            task=task,
            evidence=payload.evidence,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"task_id": str(task.id), "status": task.status}


@router.post(
    "/acknowledgements",
    response_model=PolicyAcknowledgementResponse,
    responses={
        **AUTH_RESPONSES,
        404: {"description": "Document version not found"},
        409: {"description": "Cannot acknowledge"},
    },
)
def acknowledge(
    payload: PolicyAckIn,
    request: Request,
    response: Response,
    principal: Principal = Depends(require_candidate),
    db: Session = Depends(get_db),
) -> PolicyAcknowledgementResponse:
    response.headers.update(NO_STORE)
    candidate = _candidate(principal, db)
    version = db.get(DocumentVersion, payload.document_version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="document version not found")
    try:
        ack = acknowledge_policy(
            db,
            candidate=candidate,
            document_version=version,
            wording=payload.wording,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
        )
    except OnboardingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _ack_out(ack)


# ---- projection helpers ---- #


def _assignment_out(a: CandidateOnboardingAssignment) -> OnboardingAssignmentResponse:
    return OnboardingAssignmentResponse.model_validate(a, from_attributes=True)


def _task_out(t: CandidateOnboardingTask) -> CandidateOnboardingTaskResponse:
    return CandidateOnboardingTaskResponse.model_validate(t, from_attributes=True)


def _gate_out(g: Any) -> ActivationGateResponse:
    return ActivationGateResponse(
        id=g.id,
        candidate_id=g.candidate_id,
        assignment_id=g.assignment_id,
        code=g.code,
        label=g.label,
        status=g.status,
        satisfied_at=g.satisfied_at,
        evidence_kind="derived" if g.code in DERIVED_GATE_CODES else "manual",
    )


def _doc_out(d: Any, version: DocumentVersion) -> ControlledDocumentResponse:
    return ControlledDocumentResponse(
        id=d.id,
        key=d.key,
        title=d.title,
        description=d.description,
        requires_acknowledgement=d.requires_acknowledgement,
        current_version=(
            DocumentVersionResponse.model_validate(version, from_attributes=True)
            if version
            else None
        ),
    )


def _ack_out(a: Any) -> PolicyAcknowledgementResponse:
    return PolicyAcknowledgementResponse.model_validate(a, from_attributes=True)


def _esign_out(e: Any) -> EsignEnvelopeResponse:
    return EsignEnvelopeResponse.model_validate(e, from_attributes=True)
