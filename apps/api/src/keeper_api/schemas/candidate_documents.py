from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CandidateDocumentResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    category: Literal["resume", "cover_letter"]
    original_filename: str
    content_type: str
    size_bytes: int
    scan_status: str
    quarantined: bool
    created_at: datetime


class CandidateDocumentList(BaseModel):
    items: list[CandidateDocumentResponse]
