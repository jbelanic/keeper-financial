from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.core.config import Settings
from keeper_api.models.domain import AuditEvent, RecruitmentPosting

ADMIN_HEADERS = {"X-Dev-Auth-Sub": "posting-admin", "X-Dev-Auth-AAL": "aal2"}


def posting_payload(slug: str = "synthetic-opportunity") -> dict[str, str]:
    return {
        "slug": slug,
        "title": "Synthetic local recruitment opportunity",
        "summary": "An explicitly synthetic opportunity used only by automated tests.",
        "body": "This plain-text posting is not a real job and carries no production claim.",
    }


def create_admin(db: Session) -> None:
    create_user(db, subject="posting-admin", role_code="brokerage_admin")


@pytest.mark.parametrize(
    "case,expected",
    [
        ("anonymous", 401),
        ("unmapped", 403),
        ("identity-only", 403),
        ("wrong-role", 403),
        ("inactive", 403),
        ("candidate", 403),
        ("admin-aal1", 403),
        ("admin-aal2", 201),
    ],
)
def test_posting_creation_enforces_full_admin_matrix(
    client: TestClient,
    db: Session,
    settings: Settings,
    case: str,
    expected: int,
) -> None:
    settings.require_admin_mfa = True
    headers: dict[str, str] = {}
    if case == "unmapped":
        headers = {"X-Dev-Auth-Sub": "unmapped", "X-Dev-Auth-AAL": "aal2"}
    elif case == "identity-only":
        create_user(db, subject="identity-only")
        headers = {"X-Dev-Auth-Sub": "identity-only", "X-Dev-Auth-AAL": "aal2"}
    elif case == "wrong-role":
        create_user(db, subject="wrong-role", role_code="operations")
        headers = {"X-Dev-Auth-Sub": "wrong-role", "X-Dev-Auth-AAL": "aal2"}
    elif case == "inactive":
        create_user(db, subject="inactive-admin", role_code="brokerage_admin", active=False)
        headers = {"X-Dev-Auth-Sub": "inactive-admin", "X-Dev-Auth-AAL": "aal2"}
    elif case == "candidate":
        create_user(
            db,
            subject="posting-candidate",
            role_code="candidate",
            candidate_status="application_started",
        )
        headers = {"X-Dev-Auth-Sub": "posting-candidate", "X-Dev-Auth-AAL": "aal2"}
    elif case == "admin-aal1":
        create_admin(db)
        headers = {"X-Dev-Auth-Sub": "posting-admin", "X-Dev-Auth-AAL": "aal1"}
    elif case == "admin-aal2":
        create_admin(db)
        headers = ADMIN_HEADERS

    response = client.post(
        "/api/v1/admin/recruitment-postings",
        json=posting_payload(f"synthetic-{case}"),
        headers=headers,
    )

    assert response.status_code == expected
    assert response.headers.get("Cache-Control") == "no-store"


def test_posting_lifecycle_is_explicit_audited_and_publication_filtered(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    create_admin(db)
    created = client.post(
        "/api/v1/admin/recruitment-postings",
        json=posting_payload(),
        headers={**ADMIN_HEADERS, "X-Request-ID": "posting-create"},
    )
    assert created.status_code == 201
    posting_id = created.json()["id"]
    assert created.json()["status"] == "draft"
    assert client.get("/api/v1/recruitment/postings").json()["items"] == []
    assert client.get("/api/v1/recruitment/postings/synthetic-opportunity").status_code == 404

    updated = client.patch(
        f"/api/v1/admin/recruitment-postings/{posting_id}",
        json={"summary": "Updated synthetic summary for the publication test."},
        headers=ADMIN_HEADERS,
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    published = client.post(
        f"/api/v1/admin/recruitment-postings/{posting_id}/publish",
        headers={**ADMIN_HEADERS, "X-Request-ID": "posting-publish"},
    )
    assert published.status_code == 200
    assert published.json()["published_at"] is not None
    listing = client.get("/api/v1/recruitment/postings").json()
    assert [item["slug"] for item in listing["items"]] == ["synthetic-opportunity"]
    public = client.get("/api/v1/recruitment/postings/synthetic-opportunity")
    assert public.status_code == 200
    assert set(public.json()) == {"slug", "title", "summary", "body"}

    closed = client.post(
        f"/api/v1/admin/recruitment-postings/{posting_id}/close", headers=ADMIN_HEADERS
    )
    assert closed.status_code == 200
    assert client.get("/api/v1/recruitment/postings").json()["items"] == []
    assert client.get("/api/v1/recruitment/postings/synthetic-opportunity").status_code == 404
    archived = client.post(
        f"/api/v1/admin/recruitment-postings/{posting_id}/archive", headers=ADMIN_HEADERS
    )
    assert archived.status_code == 200

    assert [event.event_type for event in db.query(AuditEvent).order_by(AuditEvent.created_at)] == [
        "recruitment_posting.created",
        "recruitment_posting.updated",
        "recruitment_posting.published",
        "recruitment_posting.closed",
        "recruitment_posting.archived",
    ]
    assert db.get(RecruitmentPosting, uuid.UUID(posting_id)).published_by_user_id is not None


@pytest.mark.parametrize("slug", ["unknown-posting", "UPPERCASE", "contains%2Fslash", "a" * 101])
def test_missing_and_invalid_public_posting_slugs_are_indistinguishable(
    client: TestClient, slug: str
) -> None:
    response = client.get(f"/api/v1/recruitment/postings/{slug}")
    assert response.status_code == 404
    assert response.json() == {"detail": "posting not found"}


def test_phase_1d_candidate_transition_endpoint_is_not_mounted(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    _, candidate = create_user(
        db,
        subject="phase1d-boundary-candidate",
        role_code="candidate",
        candidate_status="application_submitted",
    )
    assert candidate is not None
    response = client.post(
        f"/api/v1/candidates/{candidate.id}/status",
        json={"status": "under_review"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404
