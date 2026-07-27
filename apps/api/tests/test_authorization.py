from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.core.config import Settings


def test_anonymous_user_cannot_access_candidate_area(client: TestClient) -> None:
    response = client.get("/api/v1/auth/access?area=candidate")
    assert response.status_code == 401


def test_authenticated_identity_alone_does_not_grant_access(
    client: TestClient, db: Session
) -> None:
    create_user(db, subject="identity-only")
    response = client.get(
        "/api/v1/auth/access?area=candidate",
        headers={"X-Dev-Auth-Sub": "identity-only"},
    )
    assert response.status_code == 403


def test_candidate_account_can_access_candidate_area(client: TestClient, db: Session) -> None:
    create_user(
        db, subject="candidate", role_code="candidate", candidate_status="application_started"
    )
    response = client.get(
        "/api/v1/auth/access?area=candidate",
        headers={"X-Dev-Auth-Sub": "candidate"},
    )
    assert response.status_code == 200
    assert response.json()["area"] == "candidate"


def test_candidate_cannot_access_admin_area(client: TestClient, db: Session) -> None:
    create_user(db, subject="candidate", role_code="candidate", candidate_status="under_review")
    response = client.get(
        "/api/v1/auth/access?area=admin",
        headers={"X-Dev-Auth-Sub": "candidate", "X-Dev-Auth-AAL": "aal2"},
    )
    assert response.status_code == 403


def test_authorized_admin_can_access_admin_area(client: TestClient, db: Session) -> None:
    create_user(db, subject="admin", role_code="brokerage_admin")
    response = client.get(
        "/api/v1/auth/access?area=admin",
        headers={"X-Dev-Auth-Sub": "admin", "X-Dev-Auth-AAL": "aal2"},
    )
    assert response.status_code == 200


def test_authorized_agent_can_access_agent_area(client: TestClient, db: Session) -> None:
    create_user(db, subject="agent", role_code="agent")
    response = client.get(
        "/api/v1/auth/access?area=agent",
        headers={"X-Dev-Auth-Sub": "agent", "X-Dev-Auth-AAL": "aal2"},
    )
    assert response.status_code == 200


def test_admin_cannot_access_agent_area(client: TestClient, db: Session) -> None:
    create_user(db, subject="admin", role_code="brokerage_admin")
    response = client.get(
        "/api/v1/auth/access?area=agent",
        headers={"X-Dev-Auth-Sub": "admin", "X-Dev-Auth-AAL": "aal2"},
    )
    assert response.status_code == 403


def test_candidate_cannot_access_agent_area(client: TestClient, db: Session) -> None:
    create_user(db, subject="candidate", role_code="candidate", candidate_status="under_review")
    response = client.get(
        "/api/v1/auth/access?area=agent",
        headers={"X-Dev-Auth-Sub": "candidate", "X-Dev-Auth-AAL": "aal2"},
    )
    assert response.status_code == 403


def test_linked_admin_requires_aal2_for_access_and_protected_routes(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    create_user(db, subject="mfa-admin", role_code="brokerage_admin")
    aal1_headers = {"X-Dev-Auth-Sub": "mfa-admin", "X-Dev-Auth-AAL": "aal1"}
    assert client.get("/api/v1/auth/access?area=admin", headers=aal1_headers).status_code == 403
    assert client.get("/api/v1/admin/candidates", headers=aal1_headers).status_code == 403

    aal2_headers = {"X-Dev-Auth-Sub": "mfa-admin", "X-Dev-Auth-AAL": "aal2"}
    assert client.get("/api/v1/auth/access?area=admin", headers=aal2_headers).status_code == 200
    assert client.get("/api/v1/admin/candidates", headers=aal2_headers).status_code == 200


def test_return_intent_and_aal2_do_not_elevate_non_admin_or_unmapped_identity(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    create_user(
        db,
        subject="aal2-candidate",
        role_code="candidate",
        candidate_status="application_started",
    )
    candidate_response = client.get(
        "/api/v1/auth/access?area=admin",
        headers={"X-Dev-Auth-Sub": "aal2-candidate", "X-Dev-Auth-AAL": "aal2"},
    )
    unmapped_response = client.get(
        "/api/v1/auth/access?area=admin",
        headers={"X-Dev-Auth-Sub": "unmapped-aal2", "X-Dev-Auth-AAL": "aal2"},
    )
    assert candidate_response.status_code == 403
    assert unmapped_response.status_code == 403


def test_suspended_and_offboarded_candidates_are_denied(client: TestClient, db: Session) -> None:
    for subject, candidate_status in [("suspended", "suspended"), ("offboarded", "offboarded")]:
        create_user(db, subject=subject, role_code="candidate", candidate_status=candidate_status)
        response = client.get(
            "/api/v1/auth/access?area=candidate",
            headers={"X-Dev-Auth-Sub": subject},
        )
        assert response.status_code == 403


def test_inactive_application_user_is_denied(client: TestClient, db: Session) -> None:
    create_user(
        db,
        subject="inactive",
        role_code="candidate",
        candidate_status="application_started",
        active=False,
    )
    response = client.get(
        "/api/v1/auth/access?area=candidate",
        headers={"X-Dev-Auth-Sub": "inactive"},
    )
    assert response.status_code == 403
