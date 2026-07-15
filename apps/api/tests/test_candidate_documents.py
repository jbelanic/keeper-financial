from __future__ import annotations

import io
import json
import uuid
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.api.routes import candidate_documents as candidate_document_routes
from keeper_api.core.config import Settings
from keeper_api.models.domain import AuditEvent, CandidateDocument
from keeper_api.services.audit import AuditService
from keeper_api.services.malware_scanner import ScanDecision
from keeper_api.services.storage import LocalPrivateStorage, StorageError
from test_candidate_applications import (
    candidate_headers,
    complete_draft,
    start_application,
)

PDF = b"%PDF-1.7\n% synthetic candidate document\n%%EOF\n"


def docx_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")
    return output.getvalue()


def upload(
    client: TestClient,
    application_id: str,
    *,
    subject: str = "new-candidate",
    aal: str = "aal2",
    category: str = "resume",
    filename: str = "resume.pdf",
    content_type: str = "application/pdf",
    content: bytes = PDF,
):
    return client.post(
        f"/api/v1/candidate/applications/{application_id}/documents",
        data={"category": category},
        files={"file": (filename, content, content_type)},
        headers=candidate_headers(subject, aal),
    )


def test_candidate_document_upload_requires_owner_aal2_and_active_application(
    client: TestClient, db: Session
) -> None:
    application_id = start_application(client, db)["id"]
    assert (
        client.post(
            f"/api/v1/candidate/applications/{application_id}/documents",
            data={"category": "resume"},
            files={"file": ("resume.pdf", PDF, "application/pdf")},
        ).status_code
        == 401
    )
    assert upload(client, application_id, aal="aal1").status_code == 403

    other = start_application(
        client,
        db,
        subject="document-other",
        email="document-other@example.test",
        slug="synthetic-document-other",
    )
    assert other["id"] != application_id
    assert upload(client, application_id, subject="document-other").status_code == 404

    withdrawn = client.post(
        f"/api/v1/candidate/applications/{application_id}/withdraw",
        json={"expected_revision": 1},
        headers=candidate_headers(),
    )
    assert withdrawn.status_code == 200
    assert upload(client, application_id).status_code == 409


@pytest.mark.parametrize(
    "category,filename,content_type,content",
    [
        ("other", "resume.pdf", "application/pdf", PDF),
        ("resume", "resume.txt", "text/plain", b"plain text"),
        ("resume", "resume.exe.pdf", "application/pdf", PDF),
        ("resume", "resume.pdf", "application/pdf", b"not a pdf"),
        ("resume", "resume.pdf", "application/msword", PDF),
        ("resume", "resume.pdf", "application/pdf", b""),
        (
            "cover_letter",
            "letter.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            b"PK\x03\x04not-an-office-archive",
        ),
    ],
)
def test_candidate_document_rejects_unapproved_or_mismatched_files_before_storage(
    client: TestClient,
    db: Session,
    tmp_path: Path,
    category: str,
    filename: str,
    content_type: str,
    content: bytes,
) -> None:
    application_id = start_application(client, db)["id"]
    response = upload(
        client,
        application_id,
        category=category,
        filename=filename,
        content_type=content_type,
        content=content,
    )
    assert response.status_code == 422
    assert db.query(CandidateDocument).count() == 0
    assert not list((tmp_path / "objects").rglob("*"))
    audit = db.query(AuditEvent).filter_by(event_type="candidate_document.rejected").one()
    serialized = json.dumps(audit.safe_metadata)
    assert filename not in serialized
    assert "content" not in serialized


def test_candidate_document_upload_list_and_private_download_are_validated_and_audited(
    client: TestClient, db: Session
) -> None:
    application_id = start_application(client, db)["id"]
    response = upload(
        client,
        application_id,
        filename="../../resume.pdf",
        content=PDF,
    )
    assert response.status_code == 201
    document_id = response.json()["id"]
    assert response.json()["category"] == "resume"
    assert response.json()["original_filename"] == "resume.pdf"
    assert response.json()["scan_status"] == "clean"
    assert response.json()["quarantined"] is False

    listing = client.get(
        f"/api/v1/candidate/applications/{application_id}/documents",
        headers=candidate_headers(aal="aal2"),
    )
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [document_id]
    assert (
        client.get(
            f"/api/v1/candidate/applications/{application_id}/documents",
            headers=candidate_headers(aal="aal1"),
        ).status_code
        == 403
    )

    downloaded = client.get(
        f"/api/v1/documents/{document_id}/download",
        headers=candidate_headers(aal="aal2"),
    )
    assert downloaded.status_code == 200
    assert downloaded.content == PDF
    assert downloaded.headers["Cache-Control"] == "private, no-store"
    assert downloaded.headers["X-Content-Type-Options"] == "nosniff"
    assert "resume.pdf" in downloaded.headers["Content-Disposition"]
    events = [event.event_type for event in db.query(AuditEvent).order_by(AuditEvent.created_at)]
    assert events[-3:] == [
        "candidate_document.uploaded",
        "candidate_document.scan_decision",
        "candidate_document.viewed",
    ]
    assert "../../resume.pdf" not in json.dumps(
        [event.safe_metadata for event in db.query(AuditEvent).all()]
    )


def test_authorized_aal2_admin_can_retrieve_clean_candidate_document(
    client: TestClient, db: Session, settings: Settings
) -> None:
    application_id = start_application(client, db)["id"]
    uploaded = upload(client, application_id)
    assert uploaded.status_code == 201
    create_user(db, subject="document-admin", role_code="brokerage_admin")
    settings.require_admin_mfa = True
    response = client.get(
        f"/api/v1/documents/{uploaded.json()['id']}/download",
        headers={"X-Dev-Auth-Sub": "document-admin", "X-Dev-Auth-AAL": "aal2"},
    )
    assert response.status_code == 200
    assert response.content == PDF
    assert response.headers["Cache-Control"] == "private, no-store"


def test_valid_docx_signature_is_accepted(client: TestClient, db: Session) -> None:
    application_id = start_application(client, db)["id"]
    response = upload(
        client,
        application_id,
        category="cover_letter",
        filename="letter.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        content=docx_bytes(),
    )
    assert response.status_code == 201


def test_candidate_can_remove_only_draft_documents_and_category_is_bounded_to_five(
    client: TestClient, db: Session
) -> None:
    application_id = start_application(client, db)["id"]
    first = upload(client, application_id)
    assert first.status_code == 201
    removed = client.delete(
        f"/api/v1/candidate/applications/{application_id}/documents/{first.json()['id']}",
        headers=candidate_headers(aal="aal2"),
    )
    assert removed.status_code == 204
    assert db.query(CandidateDocument).count() == 0
    for index in range(5):
        assert upload(client, application_id, filename=f"resume-{index}.pdf").status_code == 201
    assert upload(client, application_id, filename="resume-six.pdf").status_code == 409

    saved = client.patch(
        f"/api/v1/candidate/applications/{application_id}",
        json=complete_draft(),
        headers=candidate_headers(),
    )
    submitted = client.post(
        f"/api/v1/candidate/applications/{application_id}/submit",
        json={"expected_revision": saved.json()["revision"]},
        headers=candidate_headers(),
    )
    assert submitted.status_code == 200
    retained = db.query(CandidateDocument).first()
    assert retained is not None
    assert (
        client.delete(
            f"/api/v1/candidate/applications/{application_id}/documents/{retained.id}",
            headers=candidate_headers(aal="aal2"),
        ).status_code
        == 409
    )


def test_scanner_unavailable_fails_closed_without_object_or_metadata(
    client: TestClient, db: Session, settings: Settings, tmp_path: Path
) -> None:
    application_id = start_application(client, db)["id"]
    settings.malware_scanner_backend = "disabled"
    response = upload(client, application_id)
    assert response.status_code == 503
    assert db.query(CandidateDocument).count() == 0
    assert not list((tmp_path / "objects").rglob("*"))
    assert (
        db.query(AuditEvent).filter_by(event_type="candidate_document.scan_decision").count() == 1
    )


def test_scanner_rejection_remains_quarantined_and_audited_without_sensitive_metadata(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    application_id = start_application(client, db)["id"]

    class RejectingScanner:
        def scan(self, content: bytes) -> ScanDecision:
            return ScanDecision(status="rejected", source="synthetic_test")

    monkeypatch.setattr(
        candidate_document_routes,
        "build_malware_scanner",
        lambda settings: RejectingScanner(),
    )
    response = upload(client, application_id, filename="private-resume.pdf")
    assert response.status_code == 422
    document = db.query(CandidateDocument).one()
    assert document.scan_status == "rejected"
    assert [path for path in (tmp_path / "objects").rglob("*") if path.is_file()]
    assert (
        client.get(
            f"/api/v1/documents/{document.id}/download",
            headers=candidate_headers(aal="aal2"),
        ).status_code
        == 409
    )
    events = {
        event.event_type: event.safe_metadata
        for event in db.query(AuditEvent)
        .filter(
            AuditEvent.event_type.in_(
                ["candidate_document.scan_decision", "candidate_document.rejected"]
            )
        )
        .all()
    }
    assert events["candidate_document.scan_decision"]["decision"] == "rejected"
    assert events["candidate_document.rejected"]["decision"] == "scanner_rejected"
    assert "private-resume.pdf" not in json.dumps(events)


def test_database_failure_after_storage_write_removes_orphan(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    application_id = start_application(client, db)["id"]
    original = AuditService.record

    def fail_upload_audit(self: AuditService, event_type: str, *args: object, **kwargs: object):
        if event_type == "candidate_document.uploaded":
            raise RuntimeError("synthetic database failure")
        return original(self, event_type, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(AuditService, "record", fail_upload_audit)
    with pytest.raises(RuntimeError, match="synthetic database failure"):
        upload(client, application_id)
    assert db.query(CandidateDocument).count() == 0
    assert not [path for path in (tmp_path / "objects").rglob("*") if path.is_file()]


def test_storage_failure_persists_no_metadata_or_success_audit(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application_id = start_application(client, db)["id"]

    def fail_put(self: LocalPrivateStorage, *args: object, **kwargs: object):
        raise StorageError("synthetic storage failure")

    monkeypatch.setattr(LocalPrivateStorage, "put", fail_put)
    response = upload(client, application_id)
    assert response.status_code == 503
    assert db.query(CandidateDocument).count() == 0
    assert db.query(AuditEvent).filter_by(event_type="candidate_document.uploaded").count() == 0


def test_quarantined_and_missing_objects_are_not_downloadable(
    client: TestClient, db: Session
) -> None:
    application_id = start_application(client, db)["id"]
    response = upload(client, application_id)
    document = db.get(CandidateDocument, uuid.UUID(response.json()["id"]))
    assert document is not None
    document.scan_status = "pending"
    db.commit()
    quarantined = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers=candidate_headers(aal="aal2"),
    )
    assert quarantined.status_code == 409
    document.scan_status = "clean"
    document.object_key = "candidate/missing-object"
    db.commit()
    missing = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers=candidate_headers(aal="aal2"),
    )
    assert missing.status_code == 404
