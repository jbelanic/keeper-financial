from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy import true as sql_true
from sqlalchemy.orm import Session

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
    ensure_gates_exist(db, candidate=candidate)
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
            PolicyAcknowledgement.candidate_id == candidate.id,
            PolicyAcknowledgement.document_version_id == document_version.id,
        )
    )
    if existing is not None:
        evidence_assignment = (
            db.get(CandidateOnboardingAssignment, existing.assignment_id)
            if existing.assignment_id is not None
            else None
        )
        if evidence_assignment is not None and evidence_assignment.candidate_id == candidate.id:
            return existing
        raise OnboardingError("existing acknowledgement assignment cannot be verified")
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
        _maybe_satisfy_gate(
            db, candidate, code="policy_acknowledgement", actor_user_id=actor_user_id
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


def link_esign_envelope(
    db: Session,
    *,
    candidate: Candidate,
    envelope_id: str | None,
    envelope_url: str,
    document_version_id: uuid.UUID | None,
    status: EsignEnvelopeStatus,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateEsignEnvelope:
    envelope = CandidateEsignEnvelope(
        candidate_id=candidate.id,
        created_by_user_id=actor_user_id,
        document_version_id=document_version_id,
        status=status.value,
        envelope_id=envelope_id,
        envelope_url=envelope_url,
    )
    db.add(envelope)
    AuditService(db).record(
        "esign.envelope_linked",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"status": status.value},
    )
    db.commit()
    db.refresh(envelope)
    return envelope


def update_esign_envelope(
    db: Session,
    *,
    envelope: CandidateEsignEnvelope,
    envelope_id: str | None,
    envelope_url: str | None,
    status: EsignEnvelopeStatus,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> CandidateEsignEnvelope:
    candidate_id = envelope.candidate_id
    if envelope_id is not None:
        envelope.envelope_id = envelope_id
    if envelope_url is not None:
        envelope.envelope_url = envelope_url
    envelope.status = status.value
    if status == EsignEnvelopeStatus.COMPLETED:
        candidate = db.get(Candidate, candidate_id)
        if candidate is not None:
            _maybe_satisfy_gate(
                db, candidate, code="executed_agreements", actor_user_id=actor_user_id
            )
    AuditService(db).record(
        "esign.envelope_updated",
        "candidate",
        candidate_id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"status": status.value},
    )
    db.commit()
    db.refresh(envelope)
    return envelope


def candidate_esign_envelopes(
    db: Session, *, candidate_id: uuid.UUID
) -> list[CandidateEsignEnvelope]:
    return list(
        db.scalars(
            select(CandidateEsignEnvelope)
            .where(CandidateEsignEnvelope.candidate_id == candidate_id)
            .order_by(CandidateEsignEnvelope.created_at.desc(), CandidateEsignEnvelope.id.desc())
        ).all()
    )


# --------------------------------------------------------------------------- #
# Activation gates (ONB-009)
# --------------------------------------------------------------------------- #


def ensure_gates_exist(db: Session, *, candidate: Candidate) -> None:
    existing = {
        gate.code
        for gate in db.scalars(
            select(ProgrammaticGate).where(ProgrammaticGate.candidate_id == candidate.id)
        ).all()
    }
    for code in ACTIVATION_GATE_CODES:
        if code not in existing:
            db.add(
                ProgrammaticGate(
                    candidate_id=candidate.id,
                    code=code,
                    label=ACTIVATION_GATE_LABELS[code],
                    status=GateStatus.OPEN.value,
                )
            )
    db.flush()


def _maybe_satisfy_gate(
    db: Session, candidate: Candidate, *, code: str, actor_user_id: uuid.UUID
) -> None:
    gate = db.scalar(
        select(ProgrammaticGate).where(
            ProgrammaticGate.candidate_id == candidate.id,
            ProgrammaticGate.code == code,
        )
    )
    if gate is None:
        gate = ProgrammaticGate(
            candidate_id=candidate.id,
            code=code,
            label=ACTIVATION_GATE_LABELS.get(code, code),
            status=GateStatus.OPEN.value,
        )
        db.add(gate)
        db.flush()
    if gate.status != GateStatus.SATISFIED.value:
        gate.status = GateStatus.SATISFIED.value
        gate.satisfied_at = datetime.now(UTC)
        gate.satisfied_by_user_id = actor_user_id


def satisfy_gate(
    db: Session,
    *,
    candidate: Candidate,
    code: str,
    actor_user_id: uuid.UUID,
    request_id: str | None,
) -> ProgrammaticGate:
    if code not in ACTIVATION_GATE_CODES:
        raise OnboardingError("unknown activation gate")
    ensure_gates_exist(db, candidate=candidate)
    _maybe_satisfy_gate(db, candidate, code=code, actor_user_id=actor_user_id)
    gate = db.scalar(
        select(ProgrammaticGate).where(
            ProgrammaticGate.candidate_id == candidate.id,
            ProgrammaticGate.code == code,
        )
    )
    assert gate is not None
    AuditService(db).record(
        "activation_gate.satisfied",
        "candidate",
        candidate.id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={"code": code},
    )
    db.commit()
    db.refresh(gate)
    return gate


def candidate_gates(db: Session, *, candidate_id: uuid.UUID) -> list[ProgrammaticGate]:
    return list(
        db.scalars(
            select(ProgrammaticGate)
            .where(ProgrammaticGate.candidate_id == candidate_id)
            .order_by(ProgrammaticGate.code)
        ).all()
    )


def activation_ready(db: Session, *, candidate_id: uuid.UUID) -> bool:
    assignment = db.scalar(
        select(CandidateOnboardingAssignment).where(
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
    gates = candidate_gates(db, candidate_id=candidate_id)
    gate_status = {gate.code: gate.status for gate in gates}
    return all(
        gate_status.get(code) == GateStatus.SATISFIED.value for code in ACTIVATION_GATE_CODES
    )


__all__ = [
    "ACTIVATION_GATE_CODES",
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
    "review_task",
    "satisfy_gate",
    "submit_task_evidence",
    "update_esign_envelope",
]
