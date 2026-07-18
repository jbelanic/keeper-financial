from __future__ import annotations

import re
import uuid
from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from keeper_api.models.statuses import AgentProfileStatus

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE = re.compile(r"^[+()\d .-]{7,32}$")


def _plain_text(value: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError("value must contain text")
    if _CONTROL.search(clean):
        raise ValueError("control characters are not allowed")
    if _HTML_TAG.search(clean):
        raise ValueError("HTML markup is not allowed")
    return clean


def _optional_plain_text(value: str | None) -> str | None:
    return _plain_text(value) if value is not None else None


def _https_url(value: str) -> str:
    clean = value.strip()
    parsed = urlsplit(clean)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("URL must be HTTPS without credentials, query data, or a fragment")
    return clean


def _public_items(values: list[str]) -> list[str]:
    normalized = [_plain_text(value) for value in values]
    if any(len(value) > 100 for value in normalized):
        raise ValueError("list items must be 100 characters or fewer")
    if len({value.casefold() for value in normalized}) != len(normalized):
        raise ValueError("list items must be unique")
    return normalized


class AgentSocialLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=1, max_length=2048)

    _normalize_label = field_validator("label")(_plain_text)
    _validate_url = field_validator("url")(_https_url)


class AgentProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: uuid.UUID
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    licensed_name: str = Field(min_length=1, max_length=160)
    approved_title: str = Field(min_length=1, max_length=160)
    licence_number: str = Field(min_length=1, max_length=80)
    biography: str = Field(default="", max_length=3000)
    languages: list[str] = Field(default_factory=list, max_length=12)
    service_areas: list[str] = Field(default_factory=list, max_length=30)
    specialties: list[str] = Field(default_factory=list, max_length=30)
    photo_url: str | None = Field(default=None, max_length=2048)
    photo_alt_text: str | None = Field(default=None, max_length=300)
    public_email: str | None = Field(default=None, max_length=320)
    public_phone: str | None = Field(default=None, max_length=32)
    social_links: list[AgentSocialLink] = Field(default_factory=list, max_length=10)

    _normalize_required = field_validator("licensed_name", "approved_title", "licence_number")(
        _plain_text
    )
    _normalize_optional = field_validator(
        "biography", "photo_alt_text", "public_email", "public_phone"
    )(_optional_plain_text)
    _normalize_lists = field_validator("languages", "service_areas", "specialties")(_public_items)

    @field_validator("photo_url")
    @classmethod
    def validate_photo_url(cls, value: str | None) -> str | None:
        return _https_url(value) if value is not None else None

    @field_validator("public_email")
    @classmethod
    def validate_public_email(cls, value: str | None) -> str | None:
        if value is not None and not _EMAIL.fullmatch(value):
            raise ValueError("public email is invalid")
        return value

    @field_validator("public_phone")
    @classmethod
    def validate_public_phone(cls, value: str | None) -> str | None:
        if value is not None and not _PHONE.fullmatch(value):
            raise ValueError("public phone is invalid")
        return value

    @model_validator(mode="after")
    def validate_photo_pair(self) -> AgentProfileCreate:
        if (self.photo_url is None) != (self.photo_alt_text is None):
            raise ValueError("photo URL and photo alternative text must be supplied together")
        return self


class AgentProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str | None = Field(
        default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    licensed_name: str | None = Field(default=None, min_length=1, max_length=160)
    approved_title: str | None = Field(default=None, min_length=1, max_length=160)
    licence_number: str | None = Field(default=None, min_length=1, max_length=80)
    biography: str | None = Field(default=None, max_length=3000)
    languages: list[str] | None = Field(default=None, max_length=12)
    service_areas: list[str] | None = Field(default=None, max_length=30)
    specialties: list[str] | None = Field(default=None, max_length=30)
    photo_url: str | None = Field(default=None, max_length=2048)
    photo_alt_text: str | None = Field(default=None, max_length=300)
    public_email: str | None = Field(default=None, max_length=320)
    public_phone: str | None = Field(default=None, max_length=32)
    social_links: list[AgentSocialLink] | None = Field(default=None, max_length=10)

    _normalize_required = field_validator("licensed_name", "approved_title", "licence_number")(
        _optional_plain_text
    )
    _normalize_optional = field_validator(
        "biography", "photo_alt_text", "public_email", "public_phone"
    )(_optional_plain_text)
    _normalize_lists = field_validator("languages", "service_areas", "specialties")(
        lambda value: _public_items(value) if value is not None else value
    )

    @field_validator("photo_url")
    @classmethod
    def validate_photo_url(cls, value: str | None) -> str | None:
        return _https_url(value) if value is not None else None

    @field_validator("public_email")
    @classmethod
    def validate_public_email(cls, value: str | None) -> str | None:
        if value is not None and not _EMAIL.fullmatch(value):
            raise ValueError("public email is invalid")
        return value

    @field_validator("public_phone")
    @classmethod
    def validate_public_phone(cls, value: str | None) -> str | None:
        if value is not None and not _PHONE.fullmatch(value):
            raise ValueError("public phone is invalid")
        return value


class PublicAgentProfileSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str
    licensed_name: str
    approved_title: str
    licence_number: str
    languages: list[str]
    service_areas: list[str]
    specialties: list[str]
    photo_url: str | None
    photo_alt_text: str | None


class PublicAgentProfile(PublicAgentProfileSummary):
    biography: str
    public_email: str | None
    public_phone: str | None
    social_links: list[AgentSocialLink]


class PublicAgentProfileList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PublicAgentProfileSummary]
    total: int
    limit: int
    offset: int


class AdminAgentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    user_id: uuid.UUID
    slug: str
    licensed_name: str
    approved_title: str
    licence_number: str
    biography: str
    languages: list[str]
    service_areas: list[str]
    specialties: list[str]
    photo_url: str | None
    photo_alt_text: str | None
    public_email: str | None
    public_phone: str | None
    social_links: list[AgentSocialLink]
    status: AgentProfileStatus
    version: int
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    published_at: datetime | None


class AdminAgentProfileList(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AdminAgentProfile]
    total: int
    limit: int
    offset: int
