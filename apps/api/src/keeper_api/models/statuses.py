from enum import StrEnum


class CandidateStatus(StrEnum):
    PROSPECT = "prospect"
    APPLICATION_STARTED = "application_started"
    APPLICATION_SUBMITTED = "application_submitted"
    UNDER_REVIEW = "under_review"
    MORE_INFORMATION_REQUIRED = "more_information_required"
    INTERVIEW = "interview"
    CONDITIONALLY_SELECTED = "conditionally_selected"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"
    ONBOARDING_IN_PROGRESS = "onboarding_in_progress"
    PENDING_FSRA_AUTHORIZATION = "pending_fsra_authorization"
    PENDING_SYSTEM_PROVISIONING = "pending_system_provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OFFBOARDING = "offboarding"
    OFFBOARDED = "offboarded"


class AgentProfileStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class DocumentStatus(StrEnum):
    REQUIRED = "required"
    AVAILABLE = "available"
    VIEWED = "viewed"
    ACKNOWLEDGED = "acknowledged"
    SENT_FOR_SIGNATURE = "sent_for_signature"
    SIGNED = "signed"
    UPLOADED = "uploaded"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"


class OnboardingTaskStatus(StrEnum):
    REQUIRED = "required"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    REJECTED = "rejected"


class OnboardingAssignmentStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    SUPERSEDED = "superseded"


class InterviewStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class EsignEnvelopeStatus(StrEnum):
    SENT = "sent"
    VIEWED = "viewed"
    COMPLETED = "completed"
    REJECTED = "rejected"
    VOIDED = "voided"


class InformationRequestStatus(StrEnum):
    OPEN = "open"
    RESPONDED = "responded"


class GateStatus(StrEnum):
    OPEN = "open"
    SATISFIED = "satisfied"
