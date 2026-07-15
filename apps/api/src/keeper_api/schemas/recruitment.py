from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PostingStatus = Literal["draft", "published", "closed", "archived"]
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_HTML_TAG = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")


def _plain_text(value: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError("value must contain text")
    if _CONTROL.search(clean):
        raise ValueError("control characters are not allowed")
    if _HTML_TAG.search(clean):
        raise ValueError("HTML markup is not allowed")
    return clean


class PostingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=5000)

    _normalize_text = field_validator("title", "summary", "body")(_plain_text)


class PostingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str | None = Field(
        default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    title: str | None = Field(default=None, min_length=1, max_length=160)
    summary: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = Field(default=None, min_length=1, max_length=5000)

    _normalize_text = field_validator("title", "summary", "body")(
        lambda value: _plain_text(value) if value is not None else value
    )


class PublicPosting(BaseModel):
    slug: str
    title: str
    summary: str
    body: str


class PublicPostingSummary(BaseModel):
    slug: str
    title: str
    summary: str


class PublicPostingList(BaseModel):
    items: list[PublicPostingSummary]
    total: int
    limit: int
    offset: int


class AdminPosting(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    summary: str
    body: str
    status: PostingStatus
    version: int
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    closed_at: datetime | None
    archived_at: datetime | None


class AdminPostingList(BaseModel):
    items: list[AdminPosting]
    total: int
    limit: int
    offset: int
