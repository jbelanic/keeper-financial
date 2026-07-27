from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MaskedSIN(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_three: str = Field(..., min_length=3, max_length=3, pattern=r"^\d{3}$")
    display: str = Field(..., pattern=r"^\*\*\* \*\*\* \d{3}$")


class MaskedBorrowerInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    sin: MaskedSIN
    marital_status: str
    number_of_dependants: int
    current_address: dict[str, Any]
    employment: list[dict[str, Any]]
    has_sin: bool = True


class BorrowerInternalProjection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    lifecycle_status: str
    revision: int
    has_sin: bool
    has_co_borrower: bool
    primary_borrower: MaskedBorrowerInfo | None
    co_borrower: MaskedBorrowerInfo | None = None
    mortgage_request: dict[str, Any] | None = None
    last_activity_at: str
    submitted_at: str | None = None


class BorrowerAgentInfo(BaseModel):
    """Full borrower detail for the exact assigned agent (per docs/35)."""

    model_config = ConfigDict(extra="forbid")

    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    sin: str
    marital_status: str
    number_of_dependants: int
    current_address: dict[str, Any]
    employment: list[dict[str, Any]]
    has_sin: bool = True
    relationship_to_primary: str | None = None


class BorrowerAgentProjection(BaseModel):
    """Full submitted-application projection for the exact assigned agent.

    Authorized only by require_internal_agent_access (exact assigned_agent_id).
    Returns unmasked SIN and full financial detail needed to open the deal in
    an external origination system. See docs/35_AGENT_FULL_DATA_PRIVACY_APPROVAL.md.
    """

    model_config = ConfigDict(extra="forbid")

    application_id: str
    lifecycle_status: str
    revision: int
    has_sin: bool
    has_co_borrower: bool
    primary_borrower: BorrowerAgentInfo | None
    co_borrower: BorrowerAgentInfo | None = None
    mortgage_request: dict[str, Any] | None = None
    subject_property: dict[str, Any] | None = None
    other_properties: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    liabilities: list[dict[str, Any]] = Field(default_factory=list)
    additional_notes: str | None = None
    last_activity_at: str
    submitted_at: str | None = None


class SinRevealAuditEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    actor_user_id: str
    actor_role: str
    assurance_level: str
    selector: str
    reason_category: str
    result: str
    revealed_at: datetime
    safe_reason_code: str


class SinRevealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_category: str = Field(..., min_length=1, max_length=64)


class SinRevealResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    sin: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")


def mask_sin(sin_digits: str) -> MaskedSIN:
    if len(sin_digits) != 9 or not sin_digits.isdigit():
        raise ValueError("invalid SIN for masking")
    return MaskedSIN(
        last_three=sin_digits[-3:],
        display=f"*** *** {sin_digits[-3:]}",
    )
