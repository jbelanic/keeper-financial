from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from conftest import create_user
from document_samples import valid_image, valid_pdf
from keeper_api.api.routes import upload_document as upload_document_routes
from keeper_api.services.malware_scanner import MalwareScannerUnavailable, ScanDecision
from test_candidate_applications import candidate_headers, start_application

FIVE_MIB = 5 * 1024 * 1024


def post_file(
    client: TestClient,
    *,
    filename: str = "document.pdf",
    content_type: str = "application/pdf",
    content: bytes | None = None,
    subject: str = "new-candidate",
    aal: str = "aal2",
):
    return client.post(
        "/api/v1/upload-document",
        files={"file": (filename, valid_pdf() if content is None else content, content_type)},
        headers=candidate_headers(subject, aal),
    )


def test_upload_document_requires_candidate_aal2_and_allowed_lifecycle(
    client: TestClient, db: Session
) -> None:
    start_application(client, db)
    anonymous = client.post(
        "/api/v1/upload-document",
        files={"file": ("document.pdf", valid_pdf(), "application/pdf")},
    )
    assert anonymous.status_code == 401
    assert anonymous.headers["Cache-Control"] == "no-store"
    assert post_file(client, aal="aal1").status_code == 403

    create_user(db, subject="upload-admin", role_code="brokerage_admin")
    assert post_file(client, subject="upload-admin").status_code == 403

    create_user(
        db,
        subject="upload-suspended",
        role_code="candidate",
        candidate_status="suspended",
    )
    assert post_file(client, subject="upload-suspended").status_code == 403


@pytest.mark.parametrize(
    ("filename", "content_type", "factory"),
    [
        ("document.pdf", "application/pdf", valid_pdf),
        ("image.jpg", "image/jpeg", lambda: valid_image("JPEG")),
        ("image.png", "image/png", lambda: valid_image("PNG")),
    ],
)
def test_upload_document_returns_minimal_clean_response(
    client: TestClient,
    db: Session,
    filename: str,
    content_type: str,
    factory: Callable[[], bytes],
) -> None:
    start_application(client, db)

    response = post_file(
        client,
        filename=filename,
        content_type=content_type,
        content=factory(),
    )

    assert response.status_code == 200
    assert response.json() == {"status": "clean"}
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "expected_status"),
    [
        ("document.pdf", "application/pdf", b"", 422),
        ("document.txt", "text/plain", b"plain", 415),
        ("document.pdf", "image/png", valid_pdf(), 415),
        ("document.pdf", "application/pdf", valid_image("PNG"), 415),
        ("image.png", "image/png", b"\x89PNG\r\n\x1a\ntruncated", 422),
        ("document.pdf", "application/pdf", b"%PDF-1.7\ninvalid\n%%EOF", 422),
    ],
)
def test_upload_document_rejects_empty_spoofed_and_malformed_files_safely(
    client: TestClient,
    db: Session,
    filename: str,
    content_type: str,
    content: bytes,
    expected_status: int,
) -> None:
    start_application(client, db)

    response = post_file(
        client,
        filename=filename,
        content_type=content_type,
        content=content,
    )

    assert response.status_code == expected_status
    assert response.json() == {
        "detail": "document type is unsupported"
        if expected_status == 415
        else "document was rejected"
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_upload_document_enforces_exact_five_mib_boundary(client: TestClient, db: Session) -> None:
    start_application(client, db)
    exact = valid_pdf(minimum_size=FIVE_MIB)

    assert post_file(client, content=exact).status_code == 200
    oversized = post_file(client, content=exact + b"x")
    assert oversized.status_code == 413
    assert oversized.json() == {"detail": "document is too large"}
    assert oversized.headers["Cache-Control"] == "no-store"


def test_upload_document_stays_in_memory_above_starlette_default_spool_threshold(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start_application(client, db)
    observed_rolled: list[bool] = []
    original = upload_document_routes._read_bounded

    async def observe(file):  # type: ignore[no-untyped-def]
        observed_rolled.append(bool(getattr(file.file, "_rolled", True)))
        return await original(file)

    monkeypatch.setattr(upload_document_routes, "_read_bounded", observe)

    response = post_file(client, content=valid_pdf(minimum_size=2 * 1024 * 1024))

    assert response.status_code == 200
    assert observed_rolled == [False]


def test_unexpected_sensitive_upload_500_has_no_store_and_nosniff(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start_application(client, db)
    monkeypatch.setattr(
        upload_document_routes,
        "validate_document_bytes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic failure")),
    )
    transport = client._transport  # type: ignore[attr-defined]
    monkeypatch.setattr(transport, "raise_server_exceptions", False)

    response = post_file(client)

    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_upload_document_rejects_malware_without_leaking_scanner_details(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    start_application(client, db)
    marker = b"".join([b"EIC", b"AR", b"-TEST", b"-MARKER"])
    content = valid_pdf().replace(b"%%EOF", b"%" + marker + b"\n%%EOF")

    class RejectingScanner:
        def scan(self, scanned: bytes) -> ScanDecision:
            assert marker in scanned
            return ScanDecision(status="rejected", source="clamav")

    monkeypatch.setattr(
        upload_document_routes,
        "build_malware_scanner",
        lambda _settings: RejectingScanner(),
    )

    response = post_file(client, content=content)

    assert response.status_code == 422
    assert response.json() == {"detail": "document was rejected"}
    assert "clam" not in response.text.lower()
    assert "marker" not in response.text.lower()


@pytest.mark.parametrize("failure", ["build", "scan"])
def test_upload_document_scanner_failures_return_safe_503(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    start_application(client, db)

    class UnavailableScanner:
        def scan(self, _content: bytes) -> ScanDecision:
            raise MalwareScannerUnavailable()

    def factory(_settings: object) -> UnavailableScanner:
        if failure == "build":
            raise MalwareScannerUnavailable()
        return UnavailableScanner()

    monkeypatch.setattr(upload_document_routes, "build_malware_scanner", factory)

    response = post_file(client)

    assert response.status_code == 503
    assert response.json() == {"detail": "document scanning is unavailable"}
    assert response.headers["Cache-Control"] == "no-store"


def test_upload_document_closes_upload_file_on_success_rejection_and_scanner_failure(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start_application(client, db)
    closed: list[str | None] = []
    original_close = StarletteUploadFile.close

    async def record_close(self: StarletteUploadFile) -> None:
        closed.append(self.filename)
        await original_close(self)

    monkeypatch.setattr(StarletteUploadFile, "close", record_close)
    anonymous = client.post(
        "/api/v1/upload-document",
        files={"file": ("anonymous.pdf", valid_pdf(), "application/pdf")},
    )
    assert anonymous.status_code == 401
    assert post_file(client, filename="success.pdf").status_code == 200
    assert post_file(client, filename="malformed.pdf", content=b"bad").status_code == 415

    monkeypatch.setattr(
        upload_document_routes,
        "build_malware_scanner",
        lambda _settings: (_ for _ in ()).throw(MalwareScannerUnavailable()),
    )
    assert post_file(client, filename="unavailable.pdf").status_code == 503

    # The ASGI bearer gate rejects anonymous requests before multipart parsing, so
    # no UploadFile exists to close for anonymous.pdf.
    assert {"success.pdf", "malformed.pdf", "unavailable.pdf"}.issubset(closed)
    assert "anonymous.pdf" not in closed


def test_upload_document_openapi_declares_strict_security_and_errors(client: TestClient) -> None:
    operation = client.get("/openapi.json").json()["paths"]["/api/v1/upload-document"]["post"]

    assert operation["security"] == [{"HTTPBearer": []}]
    assert set(operation["responses"]) == {"200", "401", "403", "413", "415", "422", "503"}
    request_body = operation["requestBody"]["content"]["multipart/form-data"]["schema"]
    assert "$ref" in request_body
