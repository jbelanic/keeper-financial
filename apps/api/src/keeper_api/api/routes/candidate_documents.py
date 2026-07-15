from __future__ import annotations

import io
import uuid
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import CandidateApplication, CandidateDocument
from keeper_api.schemas.candidate_documents import CandidateDocumentList, CandidateDocumentResponse
from keeper_api.services.audit import AuditService
from keeper_api.services.auth import Principal, require_candidate_aal2
from keeper_api.services.candidate_applications import owned_application
from keeper_api.services.candidate_files import CandidateFileRejected, validate_candidate_file
from keeper_api.services.malware_scanner import MalwareScannerUnavailable, build_malware_scanner
from keeper_api.services.storage import StorageError, build_storage

router = APIRouter(prefix="/candidate/applications", tags=["candidate documents"])
NO_STORE = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Authentication required"},
    403: {"description": "Candidate ownership or AAL2 denied"},
    404: {"description": "Owned application or document not found"},
}


def _document(document: CandidateDocument) -> CandidateDocumentResponse:
    return CandidateDocumentResponse(
        id=document.id,
        application_id=document.application_id,
        category=document.category,
        original_filename=document.original_filename,
        content_type=document.content_type,
        size_bytes=document.size_bytes,
        scan_status=document.scan_status,
        quarantined=document.scan_status != "clean",
        created_at=document.created_at,
    )


def _application(
    db: Session, application_id: uuid.UUID, principal: Principal
) -> CandidateApplication:
    if principal.candidate_id is None:
        raise HTTPException(
            status_code=403, detail="candidate access is required", headers=NO_STORE
        )
    try:
        return owned_application(db, application_id, principal.candidate_id, lock=True)
    except LookupError as exc:
        raise HTTPException(
            status_code=404, detail="application not found", headers=NO_STORE
        ) from exc


def _rejection_audit(
    db: Session,
    application_id: uuid.UUID,
    principal: Principal,
    request: Request,
    *,
    category: str,
    reason: str,
    event_type: str = "candidate_document.rejected",
) -> None:
    AuditService(db).record(
        event_type,
        "candidate_application",
        application_id,
        actor_user_id=principal.user_id,
        request_id=request.state.request_id,
        safe_metadata={
            "category": category if category in {"resume", "cover_letter"} else "invalid",
            "decision": reason,
        },
    )
    db.commit()


@router.post(
    "/{application_id}/documents",
    response_model=CandidateDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        **AUTH_RESPONSES,
        409: {"description": "Application lifecycle or category limit conflict"},
        422: {"description": "Document category, name, type, signature, or size rejected"},
        503: {"description": "Private storage or scanning unavailable"},
    },
)
def upload_candidate_document(
    application_id: uuid.UUID,
    request: Request,
    category: str = Form(),
    file: UploadFile = File(),
    principal: Principal = Depends(require_candidate_aal2),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CandidateDocumentResponse:
    application = _application(db, application_id, principal)
    if application.state not in {"draft", "submitted"} or application.status in {
        "withdrawn",
        "declined",
    }:
        raise HTTPException(
            status_code=409, detail="document uploads are unavailable", headers=NO_STORE
        )
    try:
        validated = validate_candidate_file(
            file.file,
            category=category,
            original_filename=file.filename,
            declared_content_type=file.content_type,
            maximum=min(settings.max_document_bytes, 10 * 1024 * 1024),
        )
    except CandidateFileRejected as exc:
        _rejection_audit(
            db,
            application.id,
            principal,
            request,
            category=category,
            reason=exc.code,
        )
        raise HTTPException(
            status_code=422, detail="candidate document was rejected", headers=NO_STORE
        ) from exc
    count = (
        db.scalar(
            select(func.count())
            .select_from(CandidateDocument)
            .where(
                CandidateDocument.application_id == application.id,
                CandidateDocument.category == category,
            )
        )
        or 0
    )
    if count >= 5:
        raise HTTPException(
            status_code=409, detail="document category limit reached", headers=NO_STORE
        )
    try:
        scanner = build_malware_scanner(settings)
    except MalwareScannerUnavailable as exc:
        _rejection_audit(
            db,
            application.id,
            principal,
            request,
            category=category,
            reason="scanner_unavailable",
            event_type="candidate_document.scan_decision",
        )
        raise HTTPException(
            status_code=503, detail="document scanning is unavailable", headers=NO_STORE
        ) from exc
    try:
        storage = build_storage(settings)
    except StorageError as exc:
        raise HTTPException(
            status_code=503,
            detail="private document storage is unavailable",
            headers=NO_STORE,
        ) from exc
    stored = None
    document = None
    scan_rejected = False
    try:
        stored = storage.put(io.BytesIO(validated.content), content_type=validated.content_type)
        document = CandidateDocument(
            candidate_id=application.candidate_id,
            application_id=application.id,
            category=category,
            object_key=stored.object_key,
            original_filename=validated.filename,
            content_type=validated.content_type,
            detected_content_type=validated.content_type,
            size_bytes=stored.size_bytes,
            sha256_digest=stored.sha256_digest,
            status="uploaded",
            scan_status="pending",
            is_current=True,
        )
        db.add(document)
        db.flush()
        AuditService(db).record(
            "candidate_document.uploaded",
            "candidate_document",
            document.id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
            safe_metadata={"category": category, "status": "uploaded"},
        )
        decision = scanner.scan(validated.content)
        document.scan_status = decision.status
        AuditService(db).record(
            "candidate_document.scan_decision",
            "candidate_document",
            document.id,
            actor_user_id=principal.user_id,
            request_id=request.state.request_id,
            safe_metadata={
                "category": category,
                "decision": decision.status,
                "source": decision.source,
            },
        )
        scan_rejected = decision.status != "clean"
        if scan_rejected:
            AuditService(db).record(
                "candidate_document.rejected",
                "candidate_document",
                document.id,
                actor_user_id=principal.user_id,
                request_id=request.state.request_id,
                safe_metadata={"category": category, "decision": "scanner_rejected"},
            )
        db.commit()
        db.refresh(document)
    except StorageError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503, detail="private document storage is unavailable", headers=NO_STORE
        ) from exc
    except Exception:
        db.rollback()
        if stored is not None:
            storage.delete(stored.object_key)
        raise
    if scan_rejected:
        raise HTTPException(
            status_code=422, detail="candidate document was rejected", headers=NO_STORE
        )
    if document is None:
        raise HTTPException(
            status_code=503,
            detail="candidate document persistence failed",
            headers=NO_STORE,
        )
    return _document(document)


@router.get(
    "/{application_id}/documents",
    response_model=CandidateDocumentList,
    responses=AUTH_RESPONSES,
)
def list_candidate_documents(
    application_id: uuid.UUID,
    response: Response,
    principal: Principal = Depends(require_candidate_aal2),
    db: Session = Depends(get_db),
) -> CandidateDocumentList:
    application = _application(db, application_id, principal)
    response.headers.update(NO_STORE)
    rows = db.scalars(
        select(CandidateDocument)
        .where(CandidateDocument.application_id == application.id)
        .order_by(CandidateDocument.created_at, CandidateDocument.id)
    ).all()
    return CandidateDocumentList(items=[_document(item) for item in rows])


@router.delete(
    "/{application_id}/documents/{document_id}",
    status_code=204,
    responses={
        **AUTH_RESPONSES,
        409: {"description": "Submitted documents are append-only"},
        503: {"description": "Private storage unavailable"},
    },
)
def remove_draft_candidate_document(
    application_id: uuid.UUID,
    document_id: uuid.UUID,
    principal: Principal = Depends(require_candidate_aal2),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    application = _application(db, application_id, principal)
    if application.state != "draft":
        raise HTTPException(
            status_code=409, detail="submitted documents are append-only", headers=NO_STORE
        )
    document = db.scalar(
        select(CandidateDocument).where(
            CandidateDocument.id == document_id,
            CandidateDocument.application_id == application.id,
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="document not found", headers=NO_STORE)
    try:
        build_storage(settings).delete(document.object_key)
    except StorageError as exc:
        raise HTTPException(
            status_code=503, detail="private document storage is unavailable", headers=NO_STORE
        ) from exc
    db.delete(document)
    db.commit()
    return Response(status_code=204, headers=NO_STORE)
