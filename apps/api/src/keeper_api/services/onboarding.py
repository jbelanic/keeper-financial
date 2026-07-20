from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy import true as sql_true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.domain import (
    Candidate,
    CandidateApplication,
    CandidateEsignEnvelope,
    CandidateOnboardingAssignment,
    CandidateOnboardingDocumentVersion,
    CandidateOnboardingTask,
    CandidateStatusHistory,
    ControlledDocument,
    DocumentVersion,
    GateEvidenceEvent,
    OnboardingPlan,
    OnboardingTask,
    PolicyAcknowledgement,
    ProgrammaticGate,
)
from keeper_api.models.statuses import (
    CandidateStatus,
    EsignEnvelopeStatus,
    GateStatus,
    OnboardingAssignmentStatus,
    OnboardingTaskStatus,
)
from keeper_api.services.audit import AuditService

# Mandatory activation gate codes (ONB-009). Activation is blocked until every
# configured gate is satisfied. These codes are server-owned and stable.
ACTIVATION_GATE_CODES: tuple[str, ...] = (
    "background_check",
    "fsra_authorization",
    "system_provisioning",
    "policy_acknowledgement",
    "executed_agreements",
)

ACTIVATION_GATE_LABELS: dict[str, str] = {
    "background_check": "Background check cleared",
    "fsra_authorization": "FSRA authorization verified",
    "system_provisioning": "System provisioning complete",
    "policy_acknowledgement": "Required policies acknowledged",
    "executed_agreements": "Executed agreements received",
}

MANUAL_GATE_CODES = frozenset(
    {"background_check", "fsra_authorization", "system_provisioning"}
)
DERIVED_GATE_CODES = frozenset({"policy_acknowledgement", "executed_agreements"})


class OnboardingError(ValueError):
    pass


# --------------------------------------------------------------------------- #
# Plan + task templates (ONB-001)
# --------------------------------------------------------------------------- #


def create_onboarding_plan(
    db: Session,
    *,
    name: str,
    description: str | None,
    tasks: list[OnboardingTask],
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> OnboardingPlan:
    plan = OnboardingPlan(name=name, description=description or "", is_active=True)
    db.add(plan)
    db.flush()
    for position, task in enumerate(tasks, start=1):
        db.add(
            OnboardingTask(
                plan_id=plan.id,
                title=task.title,
                instructions=task.instructions or "",
                sequence=position,
                is_required=task.is_required,
            )
        )
    AuditService(db).record(
        "onboarding_plan.created",
        "onboarding_plan",
        plan.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"name": plan.name, "task_count": len(tasks)},
    )
    db.commit()
    db.refresh(plan)
    return plan


def list_onboarding_plans(
    db: Session, *, limit: int, offset: int, active_only: bool = True
) -> tuple[list[OnboardingPlan], int]:
    condition = OnboardingPlan.is_active.is_(True) if active_only else sql_true()
    total = db.scalar(select(func.count()).select_from(OnboardingPlan).where(condition)) or 0
    rows = list(
        db.scalars(
            select(OnboardingPlan)
            .where(condition)
            .order_by(OnboardingPlan.created_at.desc(), OnboardingPlan.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
    )
    return rows, total


def get_onboarding_plan(db: Session, plan_id: uuid.UUID) -> OnboardingPlan:
    plan = db.get(OnboardingPlan, plan_id)
    if plan is None:
        raise LookupError("onboarding plan not found")
    return plan


def update_onboarding_plan(
    db: Session,
    *,
    plan_id: uuid.UUID,
    name: str,
    description: str | None,
    tasks: list[OnboardingTask],
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> OnboardingPlan:
    plan = db.scalar(
        select(OnboardingPlan)
        .where(OnboardingPlan.id == plan_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if plan is None:
        raise LookupError("onboarding plan not found")
    referenced = db.scalar(
        select(CandidateOnboardingAssignment.id)
        .where(CandidateOnboardingAssignment.onboarding_plan_id == plan.id)
        .limit(1)
    )
    if referenced is not None:
        raise OnboardingError("a referenced onboarding plan is immutable")

    plan.name = name
    plan.description = description or ""
    db.execute(delete(OnboardingTask).where(OnboardingTask.plan_id == plan.id))
    for position, task in enumerate(tasks, start=1):
        db.add(
            OnboardingTask(
                plan_id=plan.id,
                title=task.title,
                instructions=task.instructions or "",
                sequence=position,
                is_required=task.is_required,
            )
        )
    AuditService(db).record(
        "onboarding_plan.updated",
        "onboarding_plan",
        plan.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"name": plan.name, "task_count": len(tasks)},
    )
    db.commit()
    db.refresh(plan)
    return plan


def set_onboarding_plan_active(
    db: Session,
    *,
    plan: OnboardingPlan,
    is_active: bool,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> OnboardingPlan:
    locked_plan = db.scalar(
        select(OnboardingPlan)
        .where(OnboardingPlan.id == plan.id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if locked_plan is None:
        raise LookupError("onboarding plan not found")
    plan = locked_plan
    if plan.is_active == is_active:
        return plan
    referenced = db.scalar(
        select(CandidateOnboardingAssignment.id)
        .where(CandidateOnboardingAssignment.onboarding_plan_id == plan.id)
        .limit(1)
    )
    if referenced is not None:
        raise OnboardingError("a referenced onboarding plan is immutable")
    plan.is_active = is_active
    AuditService(db).record(
        "onboarding_plan.availability_changed",
        "onboarding_plan",
        plan.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"is_active": is_active},
    )
    db.commit()
    db.refresh(plan)
    return plan


# --------------------------------------------------------------------------- #
# Assignment (ONB-002)
# --------------------------------------------------------------------------- #


def assign_onboarding_plan(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    plan: OnboardingPlan,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateOnboardingAssignment:
    if application.candidate_id != candidate.id:
        raise OnboardingError("application does not belong to this candidate")
    locked_application = db.scalar(
        select(CandidateApplication)
        .where(
            CandidateApplication.id == application.id,
            CandidateApplication.candidate_id == candidate.id,
        )
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if locked_application is None:
        raise OnboardingError("the candidate application does not exist")
    application = locked_application
    locked_candidate = db.scalar(
        select(Candidate)
        .where(Candidate.id == candidate.id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if locked_candidate is None:
        raise OnboardingError("the candidate does not exist")
    candidate = locked_candidate
    locked_plan = db.scalar(
        select(OnboardingPlan)
        .where(OnboardingPlan.id == plan.id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if locked_plan is None:
        raise OnboardingError("the onboarding plan does not exist")
    plan = locked_plan
    existing = db.scalar(
        select(CandidateOnboardingAssignment).where(
            CandidateOnboardingAssignment.application_id == application.id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
        )
    )
    if existing is not None:
        if existing.onboarding_plan_id == plan.id:
            return existing
        raise OnboardingError("the application already has an active onboarding assignment")
    if CandidateStatus(application.status) != CandidateStatus.CONDITIONALLY_SELECTED:
        raise OnboardingError("only a conditionally selected application may be assigned")
    if not plan.is_active:
        raise OnboardingError("the onboarding plan is not active")

    # A candidate has one current onboarding assignment. Preserve prior
    # application-specific generations as superseded history only after every
    # new assignment precondition has passed.
    prior = db.scalars(
        select(CandidateOnboardingAssignment).where(
            CandidateOnboardingAssignment.candidate_id == candidate.id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
        )
    ).all()
    for old in prior:
        old.status = OnboardingAssignmentStatus.SUPERSEDED.value
    generation = (
        db.scalar(
            select(func.max(CandidateOnboardingAssignment.generation)).where(
                CandidateOnboardingAssignment.candidate_id == candidate.id,
                CandidateOnboardingAssignment.onboarding_plan_id == plan.id,
            )
        )
        or 0
    ) + 1
    assignment = CandidateOnboardingAssignment(
        candidate_id=candidate.id,
        application_id=application.id,
        onboarding_plan_id=plan.id,
        generation=generation,
        status=OnboardingAssignmentStatus.ACTIVE.value,
        assigned_by_user_id=actor_user_id,
    )
    db.add(assignment)
    db.flush()
    tasks = db.scalars(
        select(OnboardingTask)
        .where(OnboardingTask.plan_id == plan.id)
        .order_by(OnboardingTask.sequence)
    ).all()
    for task in tasks:
        db.add(
            CandidateOnboardingTask(
                candidate_id=candidate.id,
                assignment_id=assignment.id,
                onboarding_task_id=task.id,
                status=OnboardingTaskStatus.REQUIRED.value,
            )
        )
    versions = db.scalars(
        select(DocumentVersion).where(
            DocumentVersion.issued_at.is_not(None),
            DocumentVersion.superseded_at.is_(None),
        )
    ).all()
    for version in versions:
        db.add(
            CandidateOnboardingDocumentVersion(
                assignment_id=assignment.id,
                document_version_id=version.id,
                assigned_by_user_id=actor_user_id,
            )
        )
    candidate.assigned_onboarding_plan_id = plan.id
    candidate.assigned_onboarding_at = datetime.now(UTC)
    _advance_status(
        db,
        candidate=candidate,
        application=application,
        target=CandidateStatus.ONBOARDING_IN_PROGRESS,
        actor_user_id=actor_user_id,
        request_id=request_id,
        reason="onboarding plan assigned",
    )
    ensure_gates_exist(db, candidate=candidate, assignment=assignment)
    AuditService(db).record(
        "candidate.onboarding_assigned",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "application_id": str(application.id),
            "plan_id": str(plan.id),
            "generation": generation,
        },
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def _advance_status(
    db: Session,
    *,
    candidate: Candidate,
    application: CandidateApplication,
    target: CandidateStatus,
    actor_user_id: uuid.UUID,
    request_id: str | None,
    reason: str | None,
) -> None:
    previous = application.status
    application.status = target.value
    db.add(
        CandidateStatusHistory(
            candidate_id=candidate.id,
            application_id=application.id,
            previous_status=previous,
            new_status=target.value,
            actor_user_id=actor_user_id,
            reason=reason,
        )
    )
    AuditService(db).record(
        "candidate_application.status_changed",
        "candidate_application",
        application.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"previous_status": previous, "new_status": target.value},
    )


# --------------------------------------------------------------------------- #
# Task lifecycle (ONB-003)
# --------------------------------------------------------------------------- #


def get_candidate_tasks(
    db: Session, *, candidate_id: uuid.UUID, assignment_id: uuid.UUID | None = None
) -> list[CandidateOnboardingTask]:
    conditions = [CandidateOnboardingTask.candidate_id == candidate_id]
    if assignment_id is not None:
        conditions.append(CandidateOnboardingTask.assignment_id == assignment_id)
    return list(
        db.scalars(
            select(CandidateOnboardingTask)
            .where(*conditions)
            .order_by(CandidateOnboardingTask.created_at, CandidateOnboardingTask.id)
        ).all()
    )


def submit_task_evidence(
    db: Session,
    *,
    candidate: Candidate,
    task: CandidateOnboardingTask,
    evidence: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateOnboardingTask:
    if task.candidate_id != candidate.id:
        raise OnboardingError("task does not belong to this candidate")
    assignment = db.get(CandidateOnboardingAssignment, task.assignment_id)
    if (
        assignment is None
        or assignment.candidate_id != candidate.id
        or assignment.status != OnboardingAssignmentStatus.ACTIVE.value
    ):
        raise OnboardingError("task is not part of the current onboarding assignment")
    if task.status in {OnboardingTaskStatus.COMPLETED.value, OnboardingTaskStatus.REJECTED.value}:
        raise OnboardingError("task is already finalized")
    task.evidence = evidence
    task.status = OnboardingTaskStatus.SUBMITTED.value
    task.completed_at = datetime.now(UTC)
    task.completed_by_user_id = actor_user_id
    AuditService(db).record(
        "onboarding_task.evidence_submitted",
        "candidate_onboarding_task",
        task.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"candidate_id": str(candidate.id)},
    )
    db.commit()
    db.refresh(task)
    return task


def review_task(
    db: Session,
    *,
    task: CandidateOnboardingTask,
    approved: bool,
    review_notes: str | None,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateOnboardingTask:
    assignment = db.get(CandidateOnboardingAssignment, task.assignment_id)
    if assignment is None or assignment.status != OnboardingAssignmentStatus.ACTIVE.value:
        raise OnboardingError("task is not part of the current onboarding assignment")
    if task.status not in {
        OnboardingTaskStatus.SUBMITTED.value,
        OnboardingTaskStatus.REQUIRED.value,
        OnboardingTaskStatus.IN_PROGRESS.value,
    }:
        raise OnboardingError("task is not in a reviewable state")
    task.status = (
        OnboardingTaskStatus.COMPLETED.value if approved else OnboardingTaskStatus.REJECTED.value
    )
    task.reviewed_by_user_id = actor_user_id
    task.reviewed_at = datetime.now(UTC)
    task.review_notes = review_notes
    AuditService(db).record(
        "onboarding_task.reviewed",
        "candidate_onboarding_task",
        task.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"approved": approved},
    )
    db.commit()
    db.refresh(task)
    return task


# --------------------------------------------------------------------------- #
# Controlled documents (ONB-004/005)
# --------------------------------------------------------------------------- #


def list_controlled_documents(db: Session) -> tuple[list[ControlledDocument], int]:
    total = db.scalar(select(func.count()).select_from(ControlledDocument)) or 0
    rows = list(
        db.scalars(
            select(ControlledDocument).order_by(ControlledDocument.title, ControlledDocument.id)
        ).all()
    )
    return rows, total


def current_document_version(db: Session, document: ControlledDocument) -> DocumentVersion | None:
    return db.scalar(
        select(DocumentVersion)
        .where(
            DocumentVersion.controlled_document_id == document.id,
            DocumentVersion.superseded_at.is_(None),
        )
        .order_by(DocumentVersion.issued_at.desc(), DocumentVersion.id.desc())
    )


def candidate_assigned_documents(
    db: Session, *, candidate_id: uuid.UUID
) -> list[tuple[ControlledDocument, DocumentVersion]]:
    """Documents a candidate may view/download once onboarding is assigned (ONB-005)."""
    assignment = db.scalar(
        select(CandidateOnboardingAssignment).where(
            CandidateOnboardingAssignment.candidate_id == candidate_id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
        )
    )
    if assignment is None:
        return []
    return [
        (document, version)
        for document, version in db.execute(
            select(ControlledDocument, DocumentVersion)
            .join(
                DocumentVersion,
                DocumentVersion.controlled_document_id == ControlledDocument.id,
            )
            .join(
                CandidateOnboardingDocumentVersion,
                CandidateOnboardingDocumentVersion.document_version_id == DocumentVersion.id,
            )
            .where(CandidateOnboardingDocumentVersion.assignment_id == assignment.id)
            .order_by(ControlledDocument.title, DocumentVersion.id)
        ).all()
    ]


# --------------------------------------------------------------------------- #
# Policy acknowledgements (ONB-006)
# --------------------------------------------------------------------------- #


def _all_required_policies_acknowledged(db: Session, *, assignment_id: uuid.UUID) -> bool:
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    if assignment is None:
        return False
    required_version_ids = set(
        db.scalars(
            select(CandidateOnboardingDocumentVersion.document_version_id)
            .join(
                DocumentVersion,
                DocumentVersion.id == CandidateOnboardingDocumentVersion.document_version_id,
            )
            .join(
                ControlledDocument,
                ControlledDocument.id == DocumentVersion.controlled_document_id,
            )
            .where(
                CandidateOnboardingDocumentVersion.assignment_id == assignment_id,
                ControlledDocument.requires_acknowledgement.is_(True),
                DocumentVersion.issued_at.is_not(None),
            )
        ).all()
    )
    if not required_version_ids:
        return True
    acknowledged_version_ids = set(
        db.scalars(
            select(PolicyAcknowledgement.document_version_id)
            .join(
                CandidateOnboardingAssignment,
                CandidateOnboardingAssignment.id == PolicyAcknowledgement.assignment_id,
            )
            .where(
                PolicyAcknowledgement.candidate_id == assignment.candidate_id,
                PolicyAcknowledgement.assignment_id == assignment_id,
                CandidateOnboardingAssignment.candidate_id == assignment.candidate_id,
                PolicyAcknowledgement.document_version_id.in_(required_version_ids),
            )
        ).all()
    )
    return acknowledged_version_ids == required_version_ids


def acknowledge_policy(
    db: Session,
    *,
    candidate: Candidate,
    document_version: DocumentVersion,
    wording: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> PolicyAcknowledgement:
    if candidate.user_id != actor_user_id:
        raise OnboardingError("acknowledgement must be recorded by the candidate")
    assignment = db.scalar(
        select(CandidateOnboardingAssignment)
        .where(
            CandidateOnboardingAssignment.candidate_id == candidate.id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
        )
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if assignment is None:
        raise OnboardingError("an active onboarding assignment is required")
    assigned = db.scalar(
        select(CandidateOnboardingDocumentVersion).where(
            CandidateOnboardingDocumentVersion.assignment_id == assignment.id,
            CandidateOnboardingDocumentVersion.document_version_id == document_version.id,
        )
    )
    if assigned is None:
        raise OnboardingError("the document version is not assigned to this candidate")
    if document_version.issued_at is None or document_version.superseded_at is not None:
        raise OnboardingError("the assigned document version is not eligible for acknowledgement")
    existing = db.scalar(
        select(PolicyAcknowledgement).where(
            PolicyAcknowledgement.assignment_id == assignment.id,
            PolicyAcknowledgement.document_version_id == document_version.id,
        )
    )
    if existing is not None:
        return existing
    acknowledgement = PolicyAcknowledgement(
        candidate_id=candidate.id,
        assignment_id=assignment.id,
        user_id=actor_user_id,
        document_version_id=document_version.id,
        wording=wording,
    )
    db.add(acknowledgement)
    db.flush()
    if _all_required_policies_acknowledged(db, assignment_id=assignment.id):
        _set_derived_gate(
            db,
            assignment=assignment,
            code="policy_acknowledgement",
            satisfied=True,
            actor_user_id=actor_user_id,
        )
    AuditService(db).record(
        "policy.acknowledged",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"document_version_id": str(document_version.id)},
    )
    db.commit()
    db.refresh(acknowledgement)
    return acknowledgement


def candidate_acknowledgements(
    db: Session, *, candidate_id: uuid.UUID, assignment_id: uuid.UUID | None = None
) -> list[PolicyAcknowledgement]:
    conditions = [PolicyAcknowledgement.candidate_id == candidate_id]
    statement = select(PolicyAcknowledgement)
    if assignment_id is not None:
        statement = statement.join(
            CandidateOnboardingAssignment,
            CandidateOnboardingAssignment.id == PolicyAcknowledgement.assignment_id,
        )
        conditions.extend(
            [
                CandidateOnboardingAssignment.candidate_id == candidate_id,
                PolicyAcknowledgement.assignment_id == assignment_id,
                PolicyAcknowledgement.document_version_id.in_(
                    select(CandidateOnboardingDocumentVersion.document_version_id).where(
                        CandidateOnboardingDocumentVersion.assignment_id == assignment_id
                    )
                ),
            ]
        )
    return list(
        db.scalars(
            statement.where(*conditions).order_by(
                PolicyAcknowledgement.acknowledged_at, PolicyAcknowledgement.id
            )
        ).all()
    )


# --------------------------------------------------------------------------- #
# External e-sign envelope link (ONB-008) — no embedded cryptographic signature
# --------------------------------------------------------------------------- #


def _lock_active_assignment(
    db: Session, assignment_id: uuid.UUID
) -> CandidateOnboardingAssignment:
    assignment = db.scalar(
        select(CandidateOnboardingAssignment)
        .where(CandidateOnboardingAssignment.id == assignment_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if assignment is None or assignment.status != OnboardingAssignmentStatus.ACTIVE.value:
        raise OnboardingError("the onboarding assignment is not active")
    return assignment


def _lock_active_esign_assignment(
    db: Session, assignment_id: uuid.UUID
) -> CandidateOnboardingAssignment:
    return _lock_active_assignment(db, assignment_id)


def _lock_active_esign_envelope(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    envelope: CandidateEsignEnvelope,
) -> CandidateEsignEnvelope:
    locked_envelope = db.scalar(
        select(CandidateEsignEnvelope)
        .where(
            CandidateEsignEnvelope.id == envelope.id,
            CandidateEsignEnvelope.assignment_id == assignment.id,
            CandidateEsignEnvelope.superseded_at.is_(None),
            CandidateEsignEnvelope.provider == "documenso",
            CandidateEsignEnvelope.envelope_id == envelope.envelope_id,
        )
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if locked_envelope is None:
        raise OnboardingError("the active assignment envelope could not be verified")
    return locked_envelope


def _fail_closed_esign_refresh(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    envelope: CandidateEsignEnvelope,
    actor_user_id: uuid.UUID,
    request_id: str | None,
    failure_kind: str,
) -> None:
    assignment = _lock_active_esign_assignment(db, assignment.id)
    _lock_active_esign_envelope(db, assignment=assignment, envelope=envelope)
    _set_derived_gate(
        db,
        assignment=assignment,
        code="executed_agreements",
        satisfied=False,
        actor_user_id=actor_user_id,
    )
    AuditService(db).record(
        "esign.envelope_refresh_failed",
        "candidate_onboarding_assignment",
        assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"provider": "documenso", "failure_kind": failure_kind},
    )
    db.commit()


def link_esign_envelope(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    provider_envelope_id: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateEsignEnvelope:
    normalized_id = provider_envelope_id.strip()
    if not normalized_id or len(normalized_id) > 255:
        raise OnboardingError("Documenso envelope identifier is invalid")
    assignment = _lock_active_esign_assignment(db, assignment.id)
    existing = db.scalar(
        select(CandidateEsignEnvelope).where(
            CandidateEsignEnvelope.assignment_id == assignment.id,
            CandidateEsignEnvelope.superseded_at.is_(None),
        )
    )
    if existing is not None:
        raise OnboardingError("the assignment already has an active e-sign envelope")
    reused = db.scalar(
        select(CandidateEsignEnvelope.id).where(
            CandidateEsignEnvelope.provider == "documenso",
            CandidateEsignEnvelope.envelope_id == normalized_id,
        )
    )
    if reused is not None:
        raise OnboardingError("the Documenso envelope is already linked")
    envelope = CandidateEsignEnvelope(
        candidate_id=assignment.candidate_id,
        assignment_id=assignment.id,
        created_by_user_id=actor_user_id,
        provider="documenso",
        status=EsignEnvelopeStatus.SENT.value,
        envelope_id=normalized_id,
        envelope_url=None,
    )
    db.add(envelope)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise OnboardingError("the Documenso envelope is already linked") from exc
    AuditService(db).record(
        "esign.envelope_linked",
        "candidate_onboarding_assignment",
        assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"provider": "documenso", "status": envelope.status},
    )
    db.commit()
    db.refresh(envelope)
    return envelope


def refresh_esign_envelope(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    envelope: CandidateEsignEnvelope,
    settings: Settings,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateEsignEnvelope:
    if (
        envelope.assignment_id != assignment.id
        or assignment.status != OnboardingAssignmentStatus.ACTIVE.value
        or envelope.superseded_at is not None
        or envelope.provider != "documenso"
        or not envelope.envelope_id
    ):
        raise OnboardingError("the active assignment envelope could not be verified")
    from keeper_api.services import documenso

    try:
        provider_status = documenso.fetch_envelope_status(settings, envelope.envelope_id)
    except documenso.DocumensoError:
        _fail_closed_esign_refresh(
            db,
            assignment=assignment,
            envelope=envelope,
            actor_user_id=actor_user_id,
            request_id=request_id,
            failure_kind="provider_error",
        )
        raise
    if provider_status == "DRAFT":
        _fail_closed_esign_refresh(
            db,
            assignment=assignment,
            envelope=envelope,
            actor_user_id=actor_user_id,
            request_id=request_id,
            failure_kind="draft",
        )
        raise OnboardingError("the Documenso envelope has not been distributed")
    status_map = {
        "PENDING": EsignEnvelopeStatus.SENT,
        "COMPLETED": EsignEnvelopeStatus.COMPLETED,
        "REJECTED": EsignEnvelopeStatus.REJECTED,
    }
    local_status = status_map[provider_status]
    assignment = _lock_active_esign_assignment(db, assignment.id)
    envelope = _lock_active_esign_envelope(
        db, assignment=assignment, envelope=envelope
    )
    envelope.status = local_status.value
    envelope.last_synced_at = datetime.now(UTC)
    _set_derived_gate(
        db,
        assignment=assignment,
        code="executed_agreements",
        satisfied=local_status == EsignEnvelopeStatus.COMPLETED,
        actor_user_id=actor_user_id,
    )
    AuditService(db).record(
        "esign.envelope_refreshed",
        "candidate_onboarding_assignment",
        assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"provider": "documenso", "status": local_status.value},
    )
    db.commit()
    db.refresh(envelope)
    return envelope


def replace_esign_envelope(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    envelope: CandidateEsignEnvelope,
    provider_envelope_id: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateEsignEnvelope:
    normalized_id = provider_envelope_id.strip()
    if not normalized_id or len(normalized_id) > 255:
        raise OnboardingError("Documenso envelope identifier is invalid")
    assignment = _lock_active_esign_assignment(db, assignment.id)
    envelope = _lock_active_esign_envelope(
        db, assignment=assignment, envelope=envelope
    )
    if envelope.status not in {
        EsignEnvelopeStatus.REJECTED.value,
        EsignEnvelopeStatus.VOIDED.value,
    }:
        raise OnboardingError("only a rejected or voided envelope can be replaced")
    if db.scalar(
        select(CandidateEsignEnvelope.id).where(
            CandidateEsignEnvelope.provider == "documenso",
            CandidateEsignEnvelope.envelope_id == normalized_id,
        )
    ) is not None:
        raise OnboardingError("the Documenso envelope is already linked")

    envelope.superseded_at = datetime.now(UTC)
    db.flush()
    replacement = CandidateEsignEnvelope(
        candidate_id=assignment.candidate_id,
        assignment_id=assignment.id,
        created_by_user_id=actor_user_id,
        provider="documenso",
        envelope_id=normalized_id,
        envelope_url=None,
        status=EsignEnvelopeStatus.SENT.value,
    )
    db.add(replacement)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise OnboardingError("the Documenso envelope is already linked") from exc
    envelope.replacement_envelope_id = replacement.id
    AuditService(db).record(
        "esign.envelope_replaced",
        "candidate_onboarding_assignment",
        assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "provider": "documenso",
            "replaced_record_id": str(envelope.id),
            "replacement_record_id": str(replacement.id),
        },
    )
    db.commit()
    db.refresh(replacement)
    return replacement


def candidate_esign_envelopes(
    db: Session, *, candidate_id: uuid.UUID, assignment_id: uuid.UUID | None = None
) -> list[CandidateEsignEnvelope]:
    conditions = [CandidateEsignEnvelope.candidate_id == candidate_id]
    if assignment_id is not None:
        conditions.append(CandidateEsignEnvelope.assignment_id == assignment_id)
    return list(
        db.scalars(
            select(CandidateEsignEnvelope)
            .where(*conditions)
            .order_by(CandidateEsignEnvelope.created_at.desc(), CandidateEsignEnvelope.id.desc())
        ).all()
    )


# --------------------------------------------------------------------------- #
# Activation gates (ONB-009)
# --------------------------------------------------------------------------- #


def ensure_gates_exist(
    db: Session, *, candidate: Candidate, assignment: CandidateOnboardingAssignment
) -> None:
    if assignment.candidate_id != candidate.id:
        raise OnboardingError("assignment does not belong to this candidate")
    existing = {
        gate.code
        for gate in db.scalars(
            select(ProgrammaticGate).where(ProgrammaticGate.assignment_id == assignment.id)
        ).all()
    }
    for code in ACTIVATION_GATE_CODES:
        if code not in existing:
            db.add(
                ProgrammaticGate(
                    candidate_id=candidate.id,
                    assignment_id=assignment.id,
                    code=code,
                    label=ACTIVATION_GATE_LABELS[code],
                    status=GateStatus.OPEN.value,
                )
            )
    db.flush()


def _lock_gate(
    db: Session, *, assignment_id: uuid.UUID, code: str
) -> ProgrammaticGate | None:
    return db.scalar(
        select(ProgrammaticGate)
        .where(
            ProgrammaticGate.assignment_id == assignment_id,
            ProgrammaticGate.code == code,
        )
        .execution_options(populate_existing=True)
        .with_for_update()
    )


def _set_derived_gate(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    code: str,
    satisfied: bool,
    actor_user_id: uuid.UUID,
) -> None:
    if code not in DERIVED_GATE_CODES:
        raise OnboardingError("only derived gates may use automatic evidence")
    gate = _lock_gate(db, assignment_id=assignment.id, code=code)
    if gate is None:
        candidate = db.get(Candidate, assignment.candidate_id)
        if candidate is None:
            raise OnboardingError("candidate not found")
        ensure_gates_exist(db, candidate=candidate, assignment=assignment)
        gate = _lock_gate(db, assignment_id=assignment.id, code=code)
    assert gate is not None
    if satisfied:
        gate.status = GateStatus.SATISFIED.value
        gate.satisfied_at = datetime.now(UTC)
        gate.satisfied_by_user_id = actor_user_id
    else:
        gate.status = GateStatus.OPEN.value
        gate.satisfied_at = None
        gate.satisfied_by_user_id = None


def satisfy_gate(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    code: str,
    verified_on: date,
    evidence_source: str,
    evidence_reference: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> ProgrammaticGate:
    if code not in MANUAL_GATE_CODES:
        raise OnboardingError("derived activation gates cannot be satisfied manually")
    assignment = _lock_active_assignment(db, assignment.id)
    candidate = db.get(Candidate, assignment.candidate_id)
    if candidate is None:
        raise OnboardingError("candidate not found")
    ensure_gates_exist(db, candidate=candidate, assignment=assignment)
    gate = _lock_gate(db, assignment_id=assignment.id, code=code)
    assert gate is not None
    if gate.status == GateStatus.SATISFIED.value:
        raise OnboardingError("the activation gate is already satisfied")
    gate.status = GateStatus.SATISFIED.value
    gate.satisfied_at = datetime.now(UTC)
    gate.satisfied_by_user_id = actor_user_id
    db.add(
        GateEvidenceEvent(
            gate_id=gate.id,
            event_type="satisfied",
            verified_on=verified_on,
            evidence_source=evidence_source,
            evidence_reference=evidence_reference,
            actor_user_id=actor_user_id,
            created_at=datetime.now(UTC),
        )
    )
    AuditService(db).record(
        "activation_gate.satisfied",
        "candidate_onboarding_assignment",
        assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"code": code, "evidence_recorded": True},
    )
    db.commit()
    db.refresh(gate)
    return gate


def reopen_gate(
    db: Session,
    *,
    assignment: CandidateOnboardingAssignment,
    code: str,
    reason: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> ProgrammaticGate:
    if code not in MANUAL_GATE_CODES:
        raise OnboardingError("derived activation gates cannot be reopened manually")
    assignment = _lock_active_assignment(db, assignment.id)
    gate = _lock_gate(db, assignment_id=assignment.id, code=code)
    if gate is None or gate.status != GateStatus.SATISFIED.value:
        raise OnboardingError("only a satisfied manual gate can be reopened")
    gate.status = GateStatus.OPEN.value
    gate.satisfied_at = None
    gate.satisfied_by_user_id = None
    db.add(
        GateEvidenceEvent(
            gate_id=gate.id,
            event_type="reopened",
            reason=reason,
            actor_user_id=actor_user_id,
            created_at=datetime.now(UTC),
        )
    )
    AuditService(db).record(
        "activation_gate.reopened",
        "candidate_onboarding_assignment",
        assignment.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"code": code, "reason_recorded": True},
    )
    db.commit()
    db.refresh(gate)
    return gate


def candidate_gates(
    db: Session, *, candidate_id: uuid.UUID, assignment_id: uuid.UUID | None = None
) -> list[ProgrammaticGate]:
    if assignment_id is None:
        assignment_id = db.scalar(
            select(CandidateOnboardingAssignment.id).where(
                CandidateOnboardingAssignment.candidate_id == candidate_id,
                CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
            )
        )
    if assignment_id is None:
        return []
    return list(
        db.scalars(
            select(ProgrammaticGate)
            .where(
                ProgrammaticGate.candidate_id == candidate_id,
                ProgrammaticGate.assignment_id == assignment_id,
            )
            .order_by(ProgrammaticGate.code)
        ).all()
    )


def activation_ready(
    db: Session, *, candidate_id: uuid.UUID, assignment_id: uuid.UUID
) -> bool:
    assignment = db.scalar(
        select(CandidateOnboardingAssignment).where(
            CandidateOnboardingAssignment.id == assignment_id,
            CandidateOnboardingAssignment.candidate_id == candidate_id,
            CandidateOnboardingAssignment.status == OnboardingAssignmentStatus.ACTIVE.value,
        )
    )
    if assignment is None or assignment.application_id is None:
        return False
    application = db.get(CandidateApplication, assignment.application_id)
    if application is None or application.candidate_id != candidate_id:
        return False
    required_task_statuses = list(
        db.execute(
            select(CandidateOnboardingTask.status)
            .join(
                OnboardingTask,
                OnboardingTask.id == CandidateOnboardingTask.onboarding_task_id,
            )
            .where(
                CandidateOnboardingTask.assignment_id == assignment.id,
                OnboardingTask.is_required.is_(True),
            )
        ).scalars()
    )
    if any(status != OnboardingTaskStatus.COMPLETED.value for status in required_task_statuses):
        return False
    if not _all_required_policies_acknowledged(db, assignment_id=assignment.id):
        return False
    gates = candidate_gates(
        db, candidate_id=candidate_id, assignment_id=assignment.id
    )
    gate_status = {gate.code: gate.status for gate in gates}
    return all(
        gate_status.get(code) == GateStatus.SATISFIED.value for code in ACTIVATION_GATE_CODES
    )


__all__ = [
    "ACTIVATION_GATE_CODES",
    "DERIVED_GATE_CODES",
    "MANUAL_GATE_CODES",
    "OnboardingError",
    "acknowledge_policy",
    "activation_ready",
    "assign_onboarding_plan",
    "candidate_acknowledgements",
    "candidate_assigned_documents",
    "candidate_esign_envelopes",
    "candidate_gates",
    "create_onboarding_plan",
    "current_document_version",
    "get_candidate_tasks",
    "get_onboarding_plan",
    "link_esign_envelope",
    "list_controlled_documents",
    "list_onboarding_plans",
    "refresh_esign_envelope",
    "reopen_gate",
    "replace_esign_envelope",
    "review_task",
    "satisfy_gate",
    "set_onboarding_plan_active",
    "submit_task_evidence",
    "update_onboarding_plan",
]
