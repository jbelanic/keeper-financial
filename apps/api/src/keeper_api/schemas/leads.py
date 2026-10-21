from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_DISALLOWED = re.compile(
    r"\b(?:social\s+insurance|SIN\s*(?:number|#)|credit\s*card|bank\s*(?:account|statement)|"
    r"tax\s*return|credit\s*report|passport|password|CVV|medical|health|diagnosis|"
    r"underwriting)\b",
    re.IGNORECASE,
)


class LeadInquiryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(max_length=320, json_schema_extra={"format": "email"})
    telephone: str = Field(min_length=7, max_length=32, pattern=r"^[0-9+().\- x]+$")
    mortgage_objective: Literal["purchase", "refinance", "renewal", "investment", "other"]
    preferred_contact_method: Literal["email", "telephone"]
    # One opaque reference from the agent link (`?agent=`), resolved server-side to
    # an eligible agent account. Accepts the current referral code and the legacy
    # published-profile slug; never a client-supplied account identifier.
    agent_reference: str | None = Field(default=None, max_length=100, pattern=r"^[a-z0-9-]+$")
    message: str | None = Field(default=None, max_length=1000)
    service_contact_acknowledged: bool
    marketing_consent: bool = False
    website: str = Field(default="", max_length=0, repr=False)

    @field_validator("name", "message")
    @classmethod
    def reject_sensitive_or_control_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        clean = value.strip()
        if _DISALLOWED.search(clean):
            raise ValueError("remove sensitive financial, identity, or authentication information")
        if any(ord(character) < 32 and character not in "\n\r\t" for character in clean):
            raise ValueError("control characters are not allowed")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, value: str) -> str:
        try:
            return validate_email(
                value,
                check_deliverability=False,
                # Reserved domains are intentional for local and automated smoke tests.
                test_environment=True,
            ).normalized
        except EmailNotValidError as exc:
            raise ValueError("enter a valid email address") from exc

    @model_validator(mode="after")
    def require_service_acknowledgement(self) -> LeadInquiryCreate:
        if not self.service_contact_acknowledged:
            raise ValueError("service-contact acknowledgement is required")
        return self


class LeadInquiryCreated(BaseModel):
    id: uuid.UUID
    status: str
    marketing_consent_recorded: bool


LeadStatus = Literal["new", "assigned", "contacted", "closed"]


class LeadStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: LeadStatus


class LeadStatusUpdated(BaseModel):
    id: uuid.UUID
    status: LeadStatus


class LeadListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    status: LeadStatus | None = None


class ConsentState(BaseModel):
    state: Literal["granted", "withdrawn"]
    granted_at: datetime
    withdrawn_at: datetime | None


class LeadListItem(BaseModel):
    id: uuid.UUID
    name: str
    email: str = Field(max_length=320, json_schema_extra={"format": "email"})
    telephone: str
    mortgage_objective: Literal["purchase", "refinance", "renewal", "investment", "other"]
    preferred_contact_method: Literal["email", "telephone"]
    # Legacy pre-assignment attribution, retained for historical rows only.
    preferred_agent_slug: str | None
    preferred_agent_name: str | None = None
    message: str | None
    source: str
    status: LeadStatus
    assigned_agent_user_id: uuid.UUID | None = None
    assigned_agent_name: str | None = None
    assigned_at: datetime | None = None
    attribution_source: str | None = None
    created_at: datetime
    service_consent: ConsentState
    marketing_consent: ConsentState | None


class LeadListResponse(BaseModel):
    items: list[LeadListItem]
    total: int
    limit: int
    offset: int


class LeadAssignmentUpdate(BaseModel):
    """Assign an inquiry to one onboarded agent, or clear the assignment."""

    model_config = ConfigDict(extra="forbid")

    agent_user_id: uuid.UUID | None


class LeadAssignableAgent(BaseModel):
    user_id: uuid.UUID
    display_name: str
    email: str
    has_referral_link: bool


class LeadAssignableAgentList(BaseModel):
    items: list[LeadAssignableAgent]


class AgentLeadSummary(BaseModel):
    id: uuid.UUID
    name: str
    mortgage_objective: Literal["purchase", "refinance", "renewal", "investment", "other"]
    preferred_contact_method: Literal["email", "telephone"]
    status: LeadStatus
    assigned_at: datetime | None
    created_at: datetime


class AgentLeadListResponse(BaseModel):
    items: list[AgentLeadSummary]
    total: int
    limit: int
    offset: int


class AgentLeadDetail(BaseModel):
    id: uuid.UUID
    name: str
    email: str = Field(max_length=320, json_schema_extra={"format": "email"})
    telephone: str
    mortgage_objective: Literal["purchase", "refinance", "renewal", "investment", "other"]
    preferred_contact_method: Literal["email", "telephone"]
    message: str | None
    status: LeadStatus
    assigned_at: datetime | None
    created_at: datetime
    service_consent: ConsentState
    marketing_consent: ConsentState | None
