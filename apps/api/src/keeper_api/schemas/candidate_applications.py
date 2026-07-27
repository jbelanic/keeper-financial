from __future__ import annotations

import re
import unicodedata
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CandidateVisibleStatus = Literal[
    "application_started",
    "application_submitted",
    "under_review",
    "more_information_required",
    "interview",
    "conditionally_selected",
    "onboarding_in_progress",
    "pending_fsra_authorization",
    "pending_system_provisioning",
    "active",
    "suspended",
    "offboarding",
    "offboarded",
    "withdrawn",
    "declined",
]

COUNTRY_CODES = frozenset(
    [
        "AD",
        "AE",
        "AF",
        "AG",
        "AI",
        "AL",
        "AM",
        "AO",
        "AQ",
        "AR",
        "AS",
        "AT",
        "AU",
        "AW",
        "AX",
        "AZ",
        "BA",
        "BB",
        "BD",
        "BE",
        "BF",
        "BG",
        "BH",
        "BI",
        "BJ",
        "BL",
        "BM",
        "BN",
        "BO",
        "BQ",
        "BR",
        "BS",
        "BT",
        "BV",
        "BW",
        "BY",
        "BZ",
        "CA",
        "CC",
        "CD",
        "CF",
        "CG",
        "CH",
        "CI",
        "CK",
        "CL",
        "CM",
        "CN",
        "CO",
        "CR",
        "CU",
        "CV",
        "CW",
        "CX",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DM",
        "DO",
        "DZ",
        "EC",
        "EE",
        "EG",
        "EH",
        "ER",
        "ES",
        "ET",
        "FI",
        "FJ",
        "FK",
        "FM",
        "FO",
        "FR",
        "GA",
        "GB",
        "GD",
        "GE",
        "GF",
        "GG",
        "GH",
        "GI",
        "GL",
        "GM",
        "GN",
        "GP",
        "GQ",
        "GR",
        "GS",
        "GT",
        "GU",
        "GW",
        "GY",
        "HK",
        "HM",
        "HN",
        "HR",
        "HT",
        "HU",
        "ID",
        "IE",
        "IL",
        "IM",
        "IN",
        "IO",
        "IQ",
        "IR",
        "IS",
        "IT",
        "JE",
        "JM",
        "JO",
        "JP",
        "KE",
        "KG",
        "KH",
        "KI",
        "KM",
        "KN",
        "KP",
        "KR",
        "KW",
        "KY",
        "KZ",
        "LA",
        "LB",
        "LC",
        "LI",
        "LK",
        "LR",
        "LS",
        "LT",
        "LU",
        "LV",
        "LY",
        "MA",
        "MC",
        "MD",
        "ME",
        "MF",
        "MG",
        "MH",
        "MK",
        "ML",
        "MM",
        "MN",
        "MO",
        "MP",
        "MQ",
        "MR",
        "MS",
        "MT",
        "MU",
        "MV",
        "MW",
        "MX",
        "MY",
        "MZ",
        "NA",
        "NC",
        "NE",
        "NF",
        "NG",
        "NI",
        "NL",
        "NO",
        "NP",
        "NR",
        "NU",
        "NZ",
        "OM",
        "PA",
        "PE",
        "PF",
        "PG",
        "PH",
        "PK",
        "PL",
        "PM",
        "PN",
        "PR",
        "PS",
        "PT",
        "PW",
        "PY",
        "QA",
        "RE",
        "RO",
        "RS",
        "RU",
        "RW",
        "SA",
        "SB",
        "SC",
        "SD",
        "SE",
        "SG",
        "SH",
        "SI",
        "SJ",
        "SK",
        "SL",
        "SM",
        "SN",
        "SO",
        "SR",
        "SS",
        "ST",
        "SV",
        "SX",
        "SY",
        "SZ",
        "TC",
        "TD",
        "TF",
        "TG",
        "TH",
        "TJ",
        "TK",
        "TL",
        "TM",
        "TN",
        "TO",
        "TR",
        "TT",
        "TV",
        "TW",
        "TZ",
        "UA",
        "UG",
        "UM",
        "US",
        "UY",
        "UZ",
        "VA",
        "VC",
        "VE",
        "VG",
        "VI",
        "VN",
        "VU",
        "WF",
        "WS",
        "YE",
        "YT",
        "ZA",
        "ZM",
        "ZW",
    ]
)
_CONTROL_SINGLE = re.compile(r"[\x00-\x1f\x7f]")
_CONTROL_MULTI = re.compile(r"[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]")
_MONTH = re.compile(r"^(19|20)\d{2}-(0[1-9]|1[0-2])$")


def _single(value: str | None) -> str | None:
    if value is None:
        return None
    clean = unicodedata.normalize("NFKC", value).strip()
    if not clean or _CONTROL_SINGLE.search(clean):
        raise ValueError("enter plain single-line text")
    return clean


def _multi(value: str | None) -> str | None:
    if value is None:
        return None
    clean = unicodedata.normalize("NFKC", value).strip()
    if not clean or _CONTROL_MULTI.search(clean):
        raise ValueError("enter plain text without control characters")
    return clean


class EmploymentEntryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employer_name: str = Field(min_length=1, max_length=160)
    role_title: str = Field(min_length=1, max_length=160)
    start_month: str = Field(pattern=r"^(19|20)\d{2}-(0[1-9]|1[0-2])$")
    currently_employed: bool
    end_month: str | None = Field(default=None, pattern=r"^(19|20)\d{2}-(0[1-9]|1[0-2])$")
    summary: str | None = Field(default=None, max_length=1000)

    _normalize_single = field_validator("employer_name", "role_title")(_single)
    _normalize_multi = field_validator("summary")(_multi)

    @model_validator(mode="after")
    def validate_months(self) -> EmploymentEntryInput:
        if self.currently_employed and self.end_month is not None:
            raise ValueError("end month must be absent for current employment")
        if not self.currently_employed and self.end_month is None:
            raise ValueError("end month is required")
        if self.end_month is not None and self.end_month < self.start_month:
            raise ValueError("end month cannot precede start month")
        return self


class EducationEntryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    institution_name: str = Field(min_length=1, max_length=160)
    program_name: str = Field(min_length=1, max_length=160)
    completion_year: int | None = Field(default=None, ge=1900)

    _normalize = field_validator("institution_name", "program_name")(_single)

    @model_validator(mode="after")
    def current_year_limit(self) -> EducationEntryInput:
        if self.completion_year is not None and self.completion_year > date.today().year:
            raise ValueError("completion year cannot be in the future")
        return self


class ApplicationDraftUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    given_name: str | None = Field(default=None, max_length=70)
    family_name: str | None = Field(default=None, max_length=70)
    preferred_name: str | None = Field(default=None, max_length=70)
    phone: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    country_code: str | None = None
    preferred_contact_method: Literal["email", "phone", "no_preference"] | None = None
    available_from: date | None = None
    referral_source: (
        Literal[
            "keeper_website",
            "search",
            "social_media",
            "employee_or_agent_referral",
            "event",
            "other",
            "prefer_not_to_say",
        ]
        | None
    ) = None
    referral_detail: str | None = Field(default=None, max_length=120)
    interest_statement: str | None = Field(default=None, max_length=2000)
    relevant_experience: str | None = Field(default=None, max_length=2000)
    employment: list[EmploymentEntryInput] | None = Field(default=None, max_length=5)
    education: list[EducationEntryInput] | None = Field(default=None, max_length=3)
    privacy_acknowledged: bool | None = None
    information_accuracy_confirmed: bool | None = None

    _normalize_single = field_validator(
        "given_name", "family_name", "preferred_name", "city", "region", "referral_detail"
    )(_single)
    _normalize_multi = field_validator("interest_statement", "relevant_experience")(_multi)

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        if not re.fullmatch(r"\+?[0-9 ().-]+", clean) or not clean.startswith("+"):
            raise ValueError("phone must include a leading country code")
        normalized = "+" + re.sub(r"\D", "", clean)
        if not re.fullmatch(r"\+[0-9]{8,15}", normalized):
            raise ValueError("phone must normalize to E.164")
        return normalized

    @field_validator("country_code")
    @classmethod
    def validate_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.upper()
        if normalized not in COUNTRY_CODES:
            raise ValueError("country must be an ISO 3166-1 alpha-2 code")
        return normalized

    @model_validator(mode="after")
    def validate_referral(self) -> ApplicationDraftUpdate:
        if self.referral_detail is not None and self.referral_source not in {
            "employee_or_agent_referral",
            "other",
        }:
            raise ValueError("referral detail is allowed only for referral or other")
        return self


class ApplicationAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)


class EmploymentEntryResponse(EmploymentEntryInput):
    pass


class EducationEntryResponse(EducationEntryInput):
    pass


class CandidateApplicationResponse(BaseModel):
    id: uuid.UUID
    recruitment_posting_id: uuid.UUID
    source_posting_slug: str
    source_posting_title: str
    source_posting_version: int
    schema_version: str
    revision: int
    state: Literal["draft", "submitted", "withdrawn"]
    status: CandidateVisibleStatus
    email: str
    given_name: str | None
    family_name: str | None
    preferred_name: str | None
    phone: str | None
    city: str | None
    region: str | None
    country_code: str | None
    preferred_contact_method: str | None
    available_from: date | None
    referral_source: str | None
    referral_detail: str | None
    interest_statement: str | None
    relevant_experience: str | None
    employment: list[EmploymentEntryResponse]
    education: list[EducationEntryResponse]
    privacy_acknowledged: bool
    information_accuracy_confirmed: bool
    privacy_disclosure_version: str | None
    privacy_acknowledged_at: datetime | None
    submitted_at: datetime | None
    withdrawn_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    applications: list[CandidateApplicationResponse]


class CandidateVisibleApplicationStatus(BaseModel):
    application_id: uuid.UUID
    status: CandidateVisibleStatus
    messages: list[str]


class CandidateStatusListResponse(BaseModel):
    applications: list[CandidateVisibleApplicationStatus]


class CandidatePrivacyDisclosureResponse(BaseModel):
    title: str
    version: str
    paragraphs: list[str]
