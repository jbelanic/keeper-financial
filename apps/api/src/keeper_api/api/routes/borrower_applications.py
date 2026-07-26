from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.security import APIKeyCookie
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.borrower import BorrowerApplication
from keeper_api.services.auth import Principal, get_current_principal
from keeper_api.services.borrower_applications import (
    BorrowerSubmissionError,
    get_application_summary,
    get_internal_projection,
    reveal_sin,
    save_draft_payload,
    start_borrower_application,
    submit_borrower_application,
)
from keeper_api.services.borrower_authorization import (
    extract_capability_from_cookie,
    require_admin_aal2_borrower_access,
    require_borrower_feature_enabled,
    require_internal_agent_access,
    validate_borrower_origin,
    verify_borrower_capability,
)
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoConfigurationError,
    BorrowerCryptoState,
    verify_capability_digest,
)
from keeper_api.services.borrower_documents import (
    BorrowerDocumentRejected,
    BorrowerDocumentStorageError,
    upload_document,
)

logger = logging.getLogger(__name__)

_BORROWER_COOKIE_NAME = "__Host-keeper-borrower-draft"
_BORROWER_CAPABILITY_COOKIE = APIKeyCookie(
    name=_BORROWER_COOKIE_NAME,
    scheme_name=_BORROWER_COOKIE_NAME,
    auto_error=False,
)


router = APIRouter(prefix="/borrower-applications", tags=["borrower-applications"])


def _get_crypto_state(request: Request) -> BorrowerCryptoState | None:
    state = getattr(request.app.state, "borrower_crypto_state", None)
    if state is None:
        try:
            from pathlib import Path

            from keeper_api.core.config import get_settings
            from keeper_api.services.borrower_crypto import load_borrower_crypto_state

            settings = get_settings()
            if (
                settings.borrower_encryption_keyring_file
                and settings.borrower_capability_hmac_key_file
            ):
                state = load_borrower_crypto_state(
                    keyring_path=Path(settings.borrower_encryption_keyring_file),
                    hmac_key_path=Path(settings.borrower_capability_hmac_key_file),
                    active_key_id=settings.borrower_encryption_active_key_id,
                    borrower_origin=settings.borrower_application_origin,
                    production=settings.app_env == "production",
                )
                request.app.state.borrower_crypto_state = state
        except (BorrowerCryptoConfigurationError, Exception):
            return None
    return state


class BorrowerApplicationStartResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    revision: int
    lifecycle_status: str


class BorrowerApplicationSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(..., ge=0)
    payload: dict[str, Any]


class BorrowerApplicationSaveResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    revision: int
    lifecycle_status: str
    has_sin: bool
    has_co_borrower: bool
    last_activity_at: str
    draft_expires_at: str | None


class BorrowerSinRevealRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_category: str = Field(..., min_length=1, max_length=64)


class BorrowerSinRevealResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    sin: str


class BorrowerDocumentUploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    size_bytes: int
    scan_status: str


class BorrowerApplicationSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_version: str = Field(..., min_length=1, max_length=128)
    consent_wording_digest: str = Field(..., min_length=64, max_length=128)
    borrower_coverage: str = Field(..., pattern="^(primary|co_borrower|both)$")
    expected_revision: int = Field(..., ge=0)


class BorrowerApplicationSubmitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    application_id: str
    lifecycle_status: str
    submitted_at: str
    retention_due_at: str
    snapshot_id: str
    consent_record_id: str


@router.post(
    "/start",
    response_model=BorrowerApplicationStartResponse,
    status_code=201,
)
def start_application(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BorrowerApplicationStartResponse:
    require_borrower_feature_enabled(settings)
    validate_borrower_origin(request, settings)
    crypto_state = _get_crypto_state(request)

    application, capability = start_borrower_application(db, crypto_state, settings)

    response.set_cookie(
        key=_BORROWER_COOKIE_NAME,
        value=capability,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
        max_age=30 * 24 * 60 * 60,
    )

    return BorrowerApplicationStartResponse(
        application_id=str(application.id),
        revision=application.revision,
        lifecycle_status=application.lifecycle_status,
    )


@router.get(
    "/{application_id}",
    response_model=BorrowerApplicationSaveResponse,
    dependencies=[Depends(_BORROWER_CAPABILITY_COOKIE)],
)
def get_application(
    application_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BorrowerApplicationSaveResponse:
    require_borrower_feature_enabled(settings)
    validate_borrower_origin(request, settings)
    crypto_state = _get_crypto_state(request)

    capability = extract_capability_from_cookie(request)
    if not capability:
        raise HTTPException(status_code=404, detail="application not found")

    verify_borrower_capability(db, crypto_state, application_id, capability)

    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise ValueError("application not found")

    summary = get_application_summary(db, application)

    return BorrowerApplicationSaveResponse(
        application_id=summary["id"],
        revision=summary["revision"],
        lifecycle_status=summary["lifecycle_status"],
        has_sin=summary["has_sin"],
        has_co_borrower=summary["has_co_borrower"],
        last_activity_at=summary["last_activity_at"],
        draft_expires_at=summary["draft_expires_at"],
    )


@router.patch(
    "/{application_id}",
    response_model=BorrowerApplicationSaveResponse,
    dependencies=[Depends(_BORROWER_CAPABILITY_COOKIE)],
)
def save_application(
    application_id: uuid.UUID,
    body: BorrowerApplicationSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BorrowerApplicationSaveResponse:
    require_borrower_feature_enabled(settings)
    validate_borrower_origin(request, settings)
    crypto_state = _get_crypto_state(request)

    capability = extract_capability_from_cookie(request)
    if not capability:
        raise HTTPException(status_code=404, detail="application not found")

    existing_application = db.get(BorrowerApplication, application_id)
    if (
        existing_application is not None
        and existing_application.lifecycle_status != "draft"
        and crypto_state is not None
        and existing_application.capability_digest is not None
        and verify_capability_digest(
            capability,
            existing_application.capability_digest,
            crypto_state.hmac_key,
        )
    ):
        raise HTTPException(status_code=409, detail="already_submitted")

    ctx = verify_borrower_capability(db, crypto_state, application_id, capability)

    from keeper_api.schemas.borrower_payload import validate_borrower_draft

    try:
        validated_payload = validate_borrower_draft(body.payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc
    payload_dict = validated_payload.model_dump(mode="python", exclude_none=True)

    application = save_draft_payload(
        db=db,
        crypto_state=crypto_state,
        application_id=application_id,
        capability_session_id=ctx.capability_session_id,
        expected_revision=body.expected_revision,
        payload_data=payload_dict,
        settings=settings,
    )

    summary = get_application_summary(db, application)

    return BorrowerApplicationSaveResponse(
        application_id=summary["id"],
        revision=summary["revision"],
        lifecycle_status=summary["lifecycle_status"],
        has_sin=summary["has_sin"],
        has_co_borrower=summary["has_co_borrower"],
        last_activity_at=summary["last_activity_at"],
        draft_expires_at=summary["draft_expires_at"],
    )


@router.post(
    "/{application_id}/documents",
    response_model=BorrowerDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_BORROWER_CAPABILITY_COOKIE)],
)
def upload_borrower_document(
    application_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BorrowerDocumentUploadResponse:
    require_borrower_feature_enabled(settings)
    validate_borrower_origin(request, settings)
    crypto_state = _get_crypto_state(request)

    capability = extract_capability_from_cookie(request)
    if not capability:
        raise HTTPException(status_code=404, detail="application not found")

    ctx = verify_borrower_capability(db, crypto_state, application_id, capability)

    try:
        document = upload_document(
            db=db,
            crypto_state=crypto_state,
            application_id=application_id,
            capability_session_id=ctx.capability_session_id,
            file_stream=file.file,
            filename=file.filename,
            mime_type=file.content_type,
            settings=settings,
        )
    except BorrowerDocumentRejected as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc
    except BorrowerDocumentStorageError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        file.file.close()

    return BorrowerDocumentUploadResponse(
        document_id=str(document.id),
        filename=document.filename,
        size_bytes=document.size_bytes,
        scan_status=document.scan_status,
    )


@router.post(
    "/{application_id}/submit",
    response_model=BorrowerApplicationSubmitResponse,
    dependencies=[Depends(_BORROWER_CAPABILITY_COOKIE)],
)
def submit_application(
    application_id: uuid.UUID,
    body: BorrowerApplicationSubmitRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BorrowerApplicationSubmitResponse:
    require_borrower_feature_enabled(settings)
    validate_borrower_origin(request, settings)
    crypto_state = _get_crypto_state(request)

    capability = extract_capability_from_cookie(request)
    if not capability:
        raise HTTPException(status_code=404, detail="application not found")

    existing_application = db.get(BorrowerApplication, application_id)
    if (
        existing_application is not None
        and existing_application.lifecycle_status != "draft"
        and crypto_state is not None
        and existing_application.capability_digest is not None
        and verify_capability_digest(
            capability,
            existing_application.capability_digest,
            crypto_state.hmac_key,
        )
    ):
        raise HTTPException(status_code=409, detail="already_submitted")

    ctx = verify_borrower_capability(db, crypto_state, application_id, capability)
    try:
        application, snapshot, consent = submit_borrower_application(
            db=db,
            crypto_state=crypto_state,
            application_id=application_id,
            capability_session_id=ctx.capability_session_id,
            expected_revision=body.expected_revision,
            consent_version=body.consent_version,
            consent_wording_digest=body.consent_wording_digest,
            borrower_coverage=body.borrower_coverage,
            settings=settings,
        )
    except BorrowerSubmissionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.code) from exc

    return BorrowerApplicationSubmitResponse(
        application_id=str(application.id),
        lifecycle_status=application.lifecycle_status,
        submitted_at=application.submitted_at.isoformat() if application.submitted_at else "",
        retention_due_at=application.retention_due_at.isoformat()
        if application.retention_due_at
        else "",
        snapshot_id=str(snapshot.id),
        consent_record_id=str(consent.id),
    )


@router.get(
    "/{application_id}/internal",
)
def get_internal_application(
    application_id: uuid.UUID,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    require_borrower_feature_enabled(settings)
    require_internal_agent_access(principal, application_id, db, settings)

    crypto_state = _get_crypto_state(request)

    result = get_internal_projection(db, crypto_state, application_id)
    return result


@router.post(
    "/{application_id}/sin/reveal",
    response_model=BorrowerSinRevealResponse,
)
def sin_reveal(
    application_id: uuid.UUID,
    body: BorrowerSinRevealRequest,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BorrowerSinRevealResponse:
    require_borrower_feature_enabled(settings)
    require_admin_aal2_borrower_access(principal, application_id, db, settings)

    crypto_state = _get_crypto_state(request)

    try:
        sin_value = reveal_sin(
            db=db,
            crypto_state=crypto_state,
            application_id=application_id,
            selector="primary",
            reason_category=body.reason_category,
            actor_user_id=principal.user_id,
            actor_role="brokerage_admin",
            assurance_level=principal.aal,
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail="application not found") from err

    return BorrowerSinRevealResponse(
        application_id=str(application_id),
        sin=sin_value,
    )
