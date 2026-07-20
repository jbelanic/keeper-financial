from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, Field, field_validator

from keeper_api.models.statuses import (
    CandidateStatus,
    EsignEnvelopeStatus,
    GateStatus,
    InformationRequestStatus,
    InterviewStatus,
    OnboardingAssignmentStatus,
    OnboardingTaskStatus,
)

_PLAIN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")


def _plain_text(value: str, *, maximum: int, field_name: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError(f"{field_name} must contain text")
    if _PLAIN.search(clean):
        raise ValueError("control characters are not allowed")
    if _HTML.search(clean):
        raise ValueError("HTML markup is not allowed")
    if len(clean) > maximum:
        raise ValueError(f"{field_name} exceeds {maximum} characters")
    return clean


# --------------------------------------------------------------------------- #
# Review pipeline (REV-001..006)
# --------------------------------------------------------------------------- #


class CandidateReviewSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    application_id: uuid.UUID
    attempt_number: int
    source_posting_slug: str
    source_posting_title: str
    status: CandidateStatus
    given_name: str | None
    family_name: str | None
    email: str
    interview_status: InterviewStatus | None
    assigned_onboarding_plan_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CandidateQueueResponse(BaseModel):
    items: list[CandidateReviewSummary]
    total: int
    limit: int
    offset: int


class CandidateDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    application_id: uuid.UUID
    attempt_number: int
    source_posting_slug: str
    source_posting_title: str
    status: CandidateStatus
    given_name: str | None
    family_name: str | None
    email: str
    interview_status: InterviewStatus | None
    interview_notes: str | None
    interview_recorded_at: datetime | None
    assigned_onboarding_plan_id: uuid.UUID | None
    assigned_onboarding_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InterviewStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: uuid.UUID
    interview_status: InterviewStatus
    notes: str | None = Field(default=None, max_length=1000)

    _validate_notes = field_validator("notes")(
        lambda v: _plain_text(v, maximum=1000, field_name="notes") if v is not None else v
    )


class InformationRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: uuid.UUID
    message: str = Field(min_length=1, max_length=2000)

    _validate_message = field_validator("message")(
        lambda v: _plain_text(v, maximum=2000, field_name="message")
    )


class InformationRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID | None
    status: InformationRequestStatus
    message: str
    response: str | None
    responded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CandidateDecisionRequest(BaseModel):
    """REV-004/005: select, decline, or withdraw with a required reason where applicable."""

    model_config = ConfigDict(extra="forbid")

    application_id: uuid.UUID
    decision: CandidateStatus
    reason: str | None = Field(default=None, max_length=1000)

    _validate_reason = field_validator("reason")(
        lambda v: _plain_text(v, maximum=1000, field_name="reason") if v is not None else v
    )


# --------------------------------------------------------------------------- #
# Onboarding templates (ONB-001)
# --------------------------------------------------------------------------- #


class OnboardingTaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    instructions: str | None = Field(default=None, max_length=2000)
    is_required: bool = True

    _v_title = field_validator("title")(lambda v: _plain_text(v, maximum=160, field_name="title"))
    _v_inst = field_validator("instructions")(
        lambda v: _plain_text(v, maximum=2000, field_name="instructions") if v is not None else v
    )


class OnboardingPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1000)
    tasks: list[OnboardingTaskCreate] = Field(default_factory=list, max_length=100)

    _v_name = field_validator("name")(lambda v: _plain_text(v, maximum=160, field_name="name"))
    _v_desc = field_validator("description")(
        lambda v: _plain_text(v, maximum=1000, field_name="description") if v is not None else v
    )


class OnboardingTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    title: str
    instructions: str
    sequence: int
    is_required: bool


class OnboardingPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tasks: list[OnboardingTaskResponse] = Field(default_factory=list)


class OnboardingPlanListResponse(BaseModel):
    items: list[OnboardingPlanResponse]
    total: int
    limit: int
    offset: int


class PlanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    is_locked: bool


class PlanWithTasks(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    is_active: bool
    is_locked: bool
    tasks: list[OnboardingTaskResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Onboarding assignment + task lifecycle (ONB-002/003)
# --------------------------------------------------------------------------- #


class OnboardingAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID | None
    onboarding_plan_id: uuid.UUID
    generation: int
    status: OnboardingAssignmentStatus
    assigned_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CandidateOnboardingTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    assignment_id: uuid.UUID | None
    onboarding_task_id: uuid.UUID
    title: str = Field(validation_alias=AliasPath("template", "title"))
    status: OnboardingTaskStatus
    due_at: datetime | None
    completed_at: datetime | None
    completed_by_user_id: uuid.UUID | None
    evidence: str | None
    reviewed_by_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_notes: str | None


class CandidateOnboardingTaskListResponse(BaseModel):
    items: list[CandidateOnboardingTaskResponse]
    total: int


class OnboardingTaskEvidenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: str = Field(min_length=1, max_length=2000)

    _v_evidence = field_validator("evidence")(
        lambda v: _plain_text(v, maximum=2000, field_name="evidence")
    )


class OnboardingTaskReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    review_notes: str | None = Field(default=None, max_length=1000)

    _v_notes = field_validator("review_notes")(
        lambda v: _plain_text(v, maximum=1000, field_name="review_notes") if v is not None else v
    )


# --------------------------------------------------------------------------- #
# Controlled documents (ONB-004/005)
# --------------------------------------------------------------------------- #


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    controlled_document_id: uuid.UUID
    version_label: str
    content_type: str
    size_bytes: int
    sha256_digest: str
    issued_at: datetime | None
    superseded_at: datetime | None


class ControlledDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    title: str
    description: str
    requires_acknowledgement: bool
    current_version: DocumentVersionResponse | None = None


class ControlledDocumentListResponse(BaseModel):
    items: list[ControlledDocumentResponse]
    total: int


class PolicyAcknowledgementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    assignment_id: uuid.UUID | None
    document_version_id: uuid.UUID
    wording: str
    acknowledged_at: datetime


# --------------------------------------------------------------------------- #
# External e-sign envelope link (ONB-008) — no embedded signature
# --------------------------------------------------------------------------- #


class EsignEnvelopeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_envelope_id: str = Field(min_length=1, max_length=255)

    _v_id = field_validator("provider_envelope_id")(
        lambda v: _plain_text(v, maximum=255, field_name="provider envelope id")
    )


class EsignEnvelopeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope_id: str | None = Field(default=None, max_length=255)
    envelope_url: str | None = Field(default=None, max_length=2048)
    status: EsignEnvelopeStatus


class EsignEnvelopeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    assignment_id: uuid.UUID | None
    document_version_id: uuid.UUID | None
    provider: str
    status: EsignEnvelopeStatus
    envelope_id: str | None
    envelope_url: str | None
    last_synced_at: datetime | None
    superseded_at: datetime | None
    replacement_envelope_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------- #
# Activation gates (ONB-009)
# --------------------------------------------------------------------------- #


class ActivationGateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    assignment_id: uuid.UUID | None
    code: str
    label: str
    status: GateStatus
    satisfied_at: datetime | None
    evidence_kind: Literal["manual", "derived"]


class ManualGateEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified_on: date
    evidence_source: str = Field(min_length=1, max_length=120)
    evidence_reference: str = Field(min_length=1, max_length=160)

    _source = field_validator("evidence_source")(
        lambda v: _plain_text(v, maximum=120, field_name="evidence source")
    )
    _reference = field_validator("evidence_reference")(
        lambda v: _plain_text(v, maximum=160, field_name="evidence reference")
    )


class GateReopenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=500)

    _reason = field_validator("reason")(
        lambda v: _plain_text(v, maximum=500, field_name="reason")
    )


class AdminOnboardingAssignmentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignment_id: uuid.UUID
    candidate_id: uuid.UUID
    application_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    opportunity_title: str
    attempt_number: int
    plan_name: str
    status: OnboardingAssignmentStatus
    created_at: datetime
    activation_ready: bool


class AdminOnboardingAssignmentDetail(AdminOnboardingAssignmentSummary):
    tasks: list[CandidateOnboardingTaskResponse]
    gates: list[ActivationGateResponse]
    esign_envelopes: list[EsignEnvelopeResponse]


class ActivationGateListResponse(BaseModel):
    items: list[ActivationGateResponse]
    all_satisfied: bool


# --------------------------------------------------------------------------- #
# Candidate-facing onboarding dashboard projection
# --------------------------------------------------------------------------- #


class CandidateOnboardingAvailability(BaseModel):
    available: bool


class CandidateOnboardingDashboard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assignment: OnboardingAssignmentResponse | None
    tasks: list[CandidateOnboardingTaskResponse]
    gates: list[ActivationGateResponse]
    documents: list[ControlledDocumentResponse]
    acknowledgements: list[PolicyAcknowledgementResponse]
    esign_envelopes: list[EsignEnvelopeResponse]
    activation_ready: bool
