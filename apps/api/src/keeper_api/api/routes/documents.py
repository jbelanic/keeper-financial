import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.session import get_db
from keeper_api.models.domain import CandidateDocument
from keeper_api.services.audit import AuditService
from keeper_api.services.auth import Principal, authorize_portal, get_current_principal
from keeper_api.services.storage import StorageError, build_storage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}/download", response_model=None)
def download_candidate_document(
    document_id: uuid.UUID,
    request: Request,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    document = db.get(CandidateDocument, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="document not found")
    is_owner = principal.candidate_id == document.candidate_id and "candidate" in principal.roles
    is_admin = "brokerage_admin" in principal.roles
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="document access denied")
    authorize_portal(principal, "admin" if is_admin else "candidate", settings)
    if document.scan_status != "clean":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="document is quarantined pending a safe-file decision",
        )
    try:
        retrieval = build_storage(settings).authorized_download(document.object_key)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="document not available"
        ) from exc
    AuditService(db).record(
        "candidate_document.viewed",
        "candidate_document",
        document.id,
        actor_user_id=principal.user_id,
        request_id=request.state.request_id,
    )
    db.commit()
    if isinstance(retrieval, Path):
        return FileResponse(
            retrieval,
            media_type=document.content_type,
            filename=document.original_filename,
            headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
        )
    return RedirectResponse(
        retrieval,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Cache-Control": "private, no-store"},
    )
