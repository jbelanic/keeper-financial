from __future__ import annotations

import re
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

_DISALLOWED = re.compile(
    r"\b(?:social\s+insurance|SIN\s*(?:number|#)|credit\s*card|bank\s*(?:account|statement)|"
    r"tax\s*return|credit\s*report|passport|password|CVV)\b",
    re.IGNORECASE,
)


class LeadInquiryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    telephone: str = Field(min_length=7, max_length=32, pattern=r"^[0-9+().\- x]+$")
    mortgage_objective: Literal["purchase", "refinance", "renewal", "investment", "other"]
    preferred_contact_method: Literal["email", "telephone"]
    preferred_agent_slug: str | None = Field(default=None, max_length=100, pattern=r"^[a-z0-9-]+$")
    message: str | None = Field(default=None, max_length=1000)
    service_contact_acknowledged: bool
    marketing_consent: bool = False
    service_wording_version: str = Field(default="service-contact-v1", max_length=80)
    marketing_wording_version: str = Field(default="marketing-v1", max_length=80)
    privacy_notice_version: str = Field(default="privacy-draft-v1", max_length=80)
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

    @model_validator(mode="after")
    def require_service_acknowledgement(self) -> LeadInquiryCreate:
        if not self.service_contact_acknowledged:
            raise ValueError("service-contact acknowledgement is required")
        return self


class LeadInquiryCreated(BaseModel):
    id: uuid.UUID
    status: str
    marketing_consent_recorded: bool
