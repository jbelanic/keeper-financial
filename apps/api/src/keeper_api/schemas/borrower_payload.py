from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _luhn_check(value: str) -> bool:
    digits = [int(d) for d in value if d.isdigit()]
    if len(digits) != 9:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


PROVINCES = frozenset(
    {
        "AB",
        "BC",
        "MB",
        "NB",
        "NL",
        "NS",
        "NT",
        "NU",
        "ON",
        "PE",
        "QC",
        "SK",
        "YT",
    }
)

POSTAL_CODE_RE = re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$")

CANADIAN_PHONE_RE = re.compile(r"^\+?1?\d{10,11}$")

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

MAX_STRING_LENGTH = 500
MAX_NOTES_LENGTH = 5000
MAX_DESCRIPTION_LENGTH = 500


class BorrowerGender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MaritalStatus(StrEnum):
    SINGLE = "single"
    MARRIED = "married"
    COMMON_LAW = "common_law"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"


class PreferredContactMethod(StrEnum):
    EMAIL = "email"
    PHONE = "phone"


class MortgageObjective(StrEnum):
    PURCHASE = "purchase"
    REFINANCE = "refinance"
    RENEWAL = "renewal"
    PRE_APPROVAL = "pre_approval"


class EmploymentType(StrEnum):
    EMPLOYED = "employed"
    SELF_EMPLOYED = "self_employed"
    RETIRED = "retired"
    OTHER_INCOME = "other_income"


class PropertyType(StrEnum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    MANUFACTURED = "manufactured"
    OTHER = "other"


class AssetType(StrEnum):
    SAVINGS = "savings"
    CHEQUING = "chequing"
    INVESTMENT = "investment"
    RRSP = "rrsp"
    TFSA = "tfsa"
    PENSION = "pension"
    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    OTHER = "other"


class LiabilityType(StrEnum):
    CREDIT_CARD = "credit_card"
    LINE_OF_CREDIT = "line_of_credit"
    MORTGAGE = "mortgage"
    CAR_LOAN = "car_loan"
    STUDENT_LOAN = "student_loan"
    PERSONAL_LOAN = "personal_loan"
    OTHER = "other"


class DownPaymentSource(StrEnum):
    SAVINGS = "savings"
    GIFT = "gift"
    HOME_EQUITY = "home_equity"
    OTHER = "other"


class BorrowerAddress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    province: str = Field(..., min_length=2, max_length=2)
    postal_code: str = Field(..., min_length=6, max_length=7)
    years_at_address: int = Field(..., ge=0, le=100)
    months_at_address: int = Field(..., ge=0, le=11)

    @field_validator("province")
    @classmethod
    def validate_province(cls, v: str) -> str:
        upper = v.upper()
        if upper not in PROVINCES:
            raise ValueError("must be a valid Canadian province or territory")
        return upper

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, v: str) -> str:
        cleaned = v.replace(" ", "").upper()
        if not POSTAL_CODE_RE.match(cleaned):
            raise ValueError("must be a valid Canadian postal code")
        return cleaned


class EmploymentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employment_type: EmploymentType
    employer_name: str | None = Field(None, max_length=200)
    job_title: str | None = Field(None, max_length=200)
    occupation_category: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=100)
    duration_years: int = Field(..., ge=0, le=100)
    duration_months: int = Field(..., ge=0, le=11)
    annual_gross_income: Decimal = Field(..., ge=Decimal("0"), decimal_places=2)
    employer_address: str | None = Field(None, max_length=200)


class BorrowerInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=320)
    phone: str = Field(..., max_length=20)
    preferred_contact_method: PreferredContactMethod
    date_of_birth: date
    sin: str = Field(..., min_length=9, max_length=9)
    marital_status: MaritalStatus
    number_of_dependants: int = Field(..., ge=0, le=20)
    gender: BorrowerGender | None = None
    current_address: BorrowerAddress
    employment: list[EmploymentEntry] = Field(..., min_length=1, max_length=5)
    relationship_to_primary: str | None = Field(None, max_length=100)

    @field_validator("sin")
    @classmethod
    def validate_sin(cls, v: str) -> str:
        digits = v.replace("-", "").replace(" ", "")
        if not digits.isdigit():
            raise ValueError("SIN must contain only digits")
        if len(digits) != 9:
            raise ValueError("SIN must be exactly 9 digits")
        if not _luhn_check(digits):
            raise ValueError("SIN failed Luhn validation")
        return digits

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_RE.match(v):
            raise ValueError("must be a valid email address")
        return v.lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = re.sub(r"[\s\-\(\)\.]", "", v)
        if not CANADIAN_PHONE_RE.match(cleaned):
            raise ValueError("must be a valid North American phone number")
        return cleaned

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("date of birth must be in the past")
        if v < date(1900, 1, 1):
            raise ValueError("date of birth is implausibly early")
        return v


class DownPaymentEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: DownPaymentSource
    amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class MortgageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mortgage_objective: MortgageObjective
    requested_amount: Decimal | None = Field(None, gt=Decimal("0"), decimal_places=2)
    estimated_property_value: Decimal | None = Field(None, gt=Decimal("0"), decimal_places=2)
    expected_closing_date: date | None = None
    down_payment_sources: list[DownPaymentEntry] = Field(default_factory=list, max_length=10)
    preferred_agent_slug: str | None = Field(None, max_length=128)
    property_address: str | None = Field(None, max_length=200)
    property_city: str | None = Field(None, max_length=100)
    property_province: str | None = Field(None, max_length=2)
    property_postal_code: str | None = Field(None, max_length=7)

    @model_validator(mode="after")
    def validate_amount_fields(self) -> MortgageRequest:
        if (
            self.mortgage_objective
            in (
                MortgageObjective.PURCHASE,
                MortgageObjective.REFINANCE,
            )
            and self.requested_amount is None
            and self.estimated_property_value is None
        ):
            raise ValueError(
                "either requested_amount or estimated_property_value is required "
                f"for {self.mortgage_objective.value}"
            )
        return self


class SubjectProperty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str | None = Field(None, max_length=200)
    city: str | None = Field(None, max_length=100)
    province: str | None = Field(None, max_length=2)
    postal_code: str | None = Field(None, max_length=7)
    property_type: PropertyType | None = None
    year_built: int | None = Field(None, ge=1800, le=2100)
    livable_area_sqft: int | None = Field(None, gt=0, le=50000)
    units: int | None = Field(None, gt=0, le=100)
    monthly_property_tax: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    monthly_heating_cost: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    monthly_condo_fee: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)


class OtherPropertyMortgage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    balance: Decimal = Field(..., ge=Decimal("0"), decimal_places=2)
    payment_amount: Decimal = Field(..., ge=Decimal("0"), decimal_places=2)
    payment_frequency: str = Field(..., max_length=20)
    maturity_date: date | None = None


class OtherProperty(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str | None = Field(None, max_length=200)
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    estimated_value: Decimal | None = Field(None, ge=Decimal("0"), decimal_places=2)
    is_owner_occupied: bool = False
    mortgages: list[OtherPropertyMortgage] = Field(default_factory=list, max_length=10)


class AssetEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_type: AssetType
    value: Decimal = Field(..., ge=Decimal("0"), decimal_places=2)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class LiabilityEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    liability_type: LiabilityType
    current_balance: Decimal = Field(..., ge=Decimal("0"), decimal_places=2)
    payment_amount: Decimal = Field(..., ge=Decimal("0"), decimal_places=2)
    payment_frequency: str | None = Field(None, max_length=20)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class BorrowerApplicationPayloadInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mortgage_request: MortgageRequest
    primary_borrower: BorrowerInfo
    co_borrower: BorrowerInfo | None = None
    subject_property: SubjectProperty | None = None
    other_properties: list[OtherProperty] = Field(default_factory=list, max_length=10)
    assets: list[AssetEntry] = Field(default_factory=list, max_length=50)
    assets_complete: bool = False
    liabilities: list[LiabilityEntry] = Field(default_factory=list, max_length=50)
    liabilities_complete: bool = False
    additional_notes: str | None = Field(None, max_length=MAX_NOTES_LENGTH)

    @model_validator(mode="after")
    def validate_co_borrower(self) -> BorrowerApplicationPayloadInput:
        if self.co_borrower is not None and self.co_borrower.relationship_to_primary is None:
            raise ValueError("co_borrower must have relationship_to_primary")
        return self


def validate_borrower_payload(payload_data: dict[str, Any]) -> BorrowerApplicationPayloadInput:
    return BorrowerApplicationPayloadInput.model_validate(payload_data)
