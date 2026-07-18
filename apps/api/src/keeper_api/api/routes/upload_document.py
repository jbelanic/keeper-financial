from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from keeper_api.core.config import Settings, get_settings
from keeper_api.schemas.document_upload import DocumentScanResponse
from keeper_api.services.auth import Principal, require_candidate_aal2
from keeper_api.services.candidate_files import (
    FIVE_MIB,
    SCAN_ONLY_POLICY,
    DocumentRejected,
    validate_document_bytes,
)
from keeper_api.services.malware_scanner import (
    MalwareScannerUnavailable,
    ScanDecision,
    build_malware_scanner,
)

router = APIRouter(tags=["document scanning"])
NO_STORE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
READ_CHUNK_BYTES = 64 * 1024
RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"description": "Authentication required"},
    403: {"description": "Candidate role, lifecycle, or AAL2 denied"},
    413: {"description": "Document exceeds exactly 5 MiB"},
    415: {"description": "Document type or type relationship is unsupported"},
    422: {"description": "Document is empty, malformed, or contains malware"},
    503: {"description": "Malware scanner is unavailable or returned an invalid response"},
}


async def _read_bounded(file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(min(READ_CHUNK_BYTES, FIVE_MIB + 1 - total))
        if not chunk:
            break
        total += len(chunk)
        if total > FIVE_MIB:
            raise HTTPException(
                status_code=413,
                detail="document is too large",
                headers=NO_STORE,
            )
        chunks.append(chunk)
    return b"".join(chunks)


@router.post(
    "/upload-document",
    response_model=DocumentScanResponse,
    responses=RESPONSES,
)
async def upload_document(
    request: Request,
    response: Response,
    file: UploadFile = File(),
    _principal: Principal = Depends(require_candidate_aal2),
    settings: Settings = Depends(get_settings),
) -> DocumentScanResponse:
    try:
        content = await _read_bounded(file)

        def validate_and_scan() -> ScanDecision:
            validated = validate_document_bytes(
                content,
                original_filename=file.filename,
                declared_content_type=file.content_type,
                policy=SCAN_ONLY_POLICY,
            )
            scanner = build_malware_scanner(settings)
            return scanner.scan(validated.content)

        try:
            decision = await run_in_threadpool(
                request.app.state.document_scan_gate.run,
                validate_and_scan,
            )
        except DocumentRejected as exc:
            unsupported = exc.code in {
                "declared_mime_mismatch",
                "detected_mime_mismatch",
                "invalid_filename",
                "unsupported_extension",
            }
            raise HTTPException(
                status_code=415 if unsupported else 422,
                detail="document type is unsupported" if unsupported else "document was rejected",
                headers=NO_STORE,
            ) from exc
        except MalwareScannerUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail="document scanning is unavailable",
                headers=NO_STORE,
            ) from exc
        if decision.status != "clean":
            raise HTTPException(
                status_code=422,
                detail="document was rejected",
                headers=NO_STORE,
            )
        response.headers.update(NO_STORE)
        return DocumentScanResponse(status="clean")
    finally:
        await file.close()
