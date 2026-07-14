from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.db.session import get_db
from keeper_api.main import app
from keeper_api.models.domain import CandidateDocument


def test_api_and_database_health_are_distinct(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/health/db").json() == {"status": "ok", "database": "reachable"}


def test_database_health_reports_unavailable_without_breaking_api(client: TestClient) -> None:
    class BrokenSession:
        def execute(self, _statement):  # type: ignore[no-untyped-def]
            raise OperationalError("SELECT 1", {}, Exception("unavailable"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json()["database"] == "unreachable"
    assert client.get("/health").status_code == 200


def test_candidate_document_is_not_publicly_addressable(
    client: TestClient, db: Session, tmp_path: Path
) -> None:
    _, candidate = create_user(
        db, subject="owner", role_code="candidate", candidate_status="application_started"
    )
    assert candidate is not None
    private_path = tmp_path / "objects" / "candidate" / "random-key"
    private_path.parent.mkdir(parents=True)
    private_path.write_bytes(b"synthetic document")
    document = CandidateDocument(
        candidate_id=candidate.id,
        object_key="candidate/random-key",
        original_filename="synthetic.pdf",
        content_type="application/pdf",
        size_bytes=18,
        sha256_digest="0" * 64,
    )
    db.add(document)
    db.commit()
    response = client.get(f"/api/v1/documents/{document.id}/download")
    assert response.status_code == 401


def test_candidate_cannot_download_another_candidates_document(
    client: TestClient, db: Session
) -> None:
    _, owner = create_user(
        db, subject="owner", role_code="candidate", candidate_status="application_started"
    )
    create_user(db, subject="other", role_code="candidate", candidate_status="application_started")
    assert owner is not None
    document = CandidateDocument(
        candidate_id=owner.id,
        object_key="candidate/random-key",
        original_filename="synthetic.pdf",
        content_type="application/pdf",
        size_bytes=1,
        sha256_digest="0" * 64,
    )
    db.add(document)
    db.commit()
    response = client.get(
        f"/api/v1/documents/{document.id}/download",
        headers={"X-Dev-Auth-Sub": "other"},
    )
    assert response.status_code == 403
