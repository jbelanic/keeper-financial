from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from keeper_api.api.router import api_router
from keeper_api.api.routes.health import router as health_router
from keeper_api.core.config import get_settings
from keeper_api.core.logging import configure_logging
from keeper_api.middleware.sensitive_uploads import (
    SensitiveUploadMiddleware,
    UploadRouteLimit,
    configure_multipart_spooling,
)
from keeper_api.services.candidate_files import FIVE_MIB
from keeper_api.services.document_scan_gate import ProcessLocalDocumentScanGate
from keeper_api.services.submission_guard import LeadSubmissionGuard, SubmissionRateLimited

settings = get_settings()
SENSITIVE_MULTIPART_OVERHEAD_BYTES = 64 * 1024
configure_logging()
logger = logging.getLogger("keeper_api.request")
request_id_pattern = re.compile(r"^[A-Za-z0-9._-]{1,100}$")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None,
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)
app.state.lead_submission_guard = LeadSubmissionGuard(
    request_limit=settings.lead_rate_limit_requests,
    window_seconds=settings.lead_rate_limit_window_seconds,
    tracked_clients=settings.lead_rate_limit_tracked_clients,
)
app.state.document_scan_gate = ProcessLocalDocumentScanGate(settings.document_scan_max_concurrency)
configure_multipart_spooling(
    max(FIVE_MIB, settings.max_document_bytes, settings.borrower_max_document_bytes)
    + SENSITIVE_MULTIPART_OVERHEAD_BYTES
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Dev-Auth-Sub",
        "X-Dev-Auth-AAL",
        "X-Dev-Auth-Email",
        "X-Dev-Auth-Verified",
        "X-Keeper-Borrower-CSRF",
    ],
)


@app.middleware("http")
async def request_context(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    supplied_request_id = request.headers.get("x-request-id", "")
    request_id = (
        supplied_request_id
        if request_id_pattern.fullmatch(supplied_request_id)
        else str(uuid.uuid4())
    )
    request.state.request_id = request_id
    started = time.monotonic()
    response: Response
    if request.method == "POST" and request.url.path == "/api/v1/leads":
        try:
            request.app.state.lead_submission_guard.check(
                request.client.host if request.client else None
            )
        except SubmissionRateLimited as exc:
            response = JSONResponse(
                status_code=429,
                content={"detail": "too many contact requests; please try again later"},
                headers={"Retry-After": str(exc.retry_after_seconds)},
            )
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)
    if (request.method == "GET" and request.url.path == "/api/v1/leads") or (
        request.method == "POST"
        and request.url.path.startswith("/api/v1/leads/")
        and (
            request.url.path.endswith("/marketing-consent/withdrawal")
            or request.url.path.endswith("/status")
        )
    ):
        response.headers["Cache-Control"] = "no-store"
    if request.url.path.startswith("/api/v1/admin/"):
        response.headers["Cache-Control"] = "no-store"
    if request.url.path == "/api/v1/upload-document":
        response.headers["Cache-Control"] = "no-store"
    elif (
        request.url.path.startswith("/api/v1/borrower-applications/")
        or request.url.path.startswith("/api/v1/candidate/")
        or request.url.path.endswith("/applications/start")
    ):
        response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request completed",
        extra={
            "event": "http.request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
        },
    )
    return response


app.add_middleware(
    SensitiveUploadMiddleware,
    route_limits=(
        UploadRouteLimit.exact("/api/v1/upload-document", maximum_file_bytes=FIVE_MIB),
        UploadRouteLimit.pattern(
            r"^/api/v1/candidate/applications/[^/]+/documents$",
            maximum_file_bytes=settings.max_document_bytes,
            private=True,
        ),
        UploadRouteLimit.pattern(
            r"^/api/v1/borrower-applications/[^/]+/documents$",
            maximum_file_bytes=settings.borrower_max_document_bytes,
            private=True,
            auth_mode="borrower_capability",
            expected_host=(
                "localhost:8000" if settings.app_env == "local" else "apply.keeperfinancial.ca"
            ),
            expected_origin=(
                "http://localhost:8000"
                if settings.app_env == "local"
                else "https://apply.keeperfinancial.ca"
            ),
        ),
    ),
    multipart_overhead_bytes=SENSITIVE_MULTIPART_OVERHEAD_BYTES,
)


app.include_router(health_router)
app.include_router(api_router)
