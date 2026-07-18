from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.api.routes import agents as agent_routes
from keeper_api.models.domain import AgentProfile, AuditEvent
from keeper_api.services.agents import get_admin_profile

ADMIN_HEADERS = {"X-Dev-Auth-Sub": "phase1e-admin", "X-Dev-Auth-AAL": "aal2"}


def _agent_account(db: Session, subject: str = "phase1e-agent"):
    user, candidate = create_user(
        db,
        subject=subject,
        role_code="agent",
        candidate_status="active",
    )
    assert candidate is not None
    return user, candidate


def _profile_payload(user_id: str) -> dict[str, object]:
    return {
        "user_id": user_id,
        "slug": "synthetic-agent",
        "licensed_name": "Synthetic Agent",
        "approved_title": "Mortgage Agent Level 2",
        "licence_number": "M00000000",
        "biography": "Synthetic, public-safe biography for deterministic tests.",
        "languages": ["English", "French"],
        "service_areas": ["London", "Southwestern Ontario"],
        "specialties": ["Purchases", "Renewals"],
        "photo_url": "https://media.keeper.example/agents/synthetic-agent.jpg",
        "photo_alt_text": "Synthetic Agent in a professional office",
        "public_email": "synthetic.agent@example.test",
        "public_phone": "+1 555 010 0200",
        "social_links": [
            {
                "label": "LinkedIn",
                "url": "https://www.linkedin.com/in/synthetic-agent",
            }
        ],
    }


def _create_admin_and_agent(db: Session):
    admin, _ = create_user(db, subject="phase1e-admin", role_code="brokerage_admin")
    agent, candidate = _agent_account(db)
    return admin, agent, candidate


def _create_profile(client: TestClient, db: Session) -> dict[str, object]:
    _, agent, _ = _create_admin_and_agent(db)
    response = client.post(
        "/api/v1/admin/agent-profiles",
        json=_profile_payload(str(agent.id)),
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def test_admin_create_list_get_and_update_profile(client: TestClient, db: Session) -> None:
    created = _create_profile(client, db)
    assert created["status"] == "draft"
    assert created["version"] == 1
    assert created["licensed_name"] == "Synthetic Agent"

    listed = client.get("/api/v1/admin/agent-profiles?limit=25&offset=0", headers=ADMIN_HEADERS)
    assert listed.status_code == 200
    assert listed.headers["cache-control"] == "no-store"
    assert listed.json()["items"] == [created]

    detail = client.get(f"/api/v1/admin/agent-profiles/{created['id']}", headers=ADMIN_HEADERS)
    assert detail.status_code == 200
    assert detail.headers["cache-control"] == "no-store"
    assert detail.json() == created

    updated = client.patch(
        f"/api/v1/admin/agent-profiles/{created['id']}",
        json={"biography": "Updated public-safe biography."},
        headers=ADMIN_HEADERS,
    )
    assert updated.status_code == 200
    assert updated.headers["cache-control"] == "no-store"
    assert updated.json()["biography"] == "Updated public-safe biography."
    assert updated.json()["version"] == 2


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({}, 401),
        ({"X-Dev-Auth-Sub": "phase1e-wrong-role"}, 403),
    ],
)
def test_admin_profile_management_denies_anonymous_and_wrong_role(
    client: TestClient,
    db: Session,
    headers: dict[str, str],
    expected: int,
) -> None:
    _agent_account(db)
    if headers:
        create_user(
            db,
            subject="phase1e-wrong-role",
            role_code="candidate",
            candidate_status="active",
        )
    response = client.get("/api/v1/admin/agent-profiles", headers=headers)
    assert response.status_code == expected


def test_admin_profile_management_enforces_configured_aal2(
    client: TestClient, db: Session, settings
) -> None:
    create_user(db, subject="phase1e-admin", role_code="brokerage_admin")
    settings.require_admin_mfa = True
    response = client.get(
        "/api/v1/admin/agent-profiles",
        headers={"X-Dev-Auth-Sub": "phase1e-admin", "X-Dev-Auth-AAL": "aal1"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "candidate_status", ["declined", "withdrawn", "suspended", "offboarding", "offboarded"]
)
def test_denied_admin_account_lifecycle_is_rejected_before_profile_rows(
    client: TestClient, db: Session, candidate_status: str
) -> None:
    create_user(
        db,
        subject=f"denied-admin-{candidate_status}",
        role_code="brokerage_admin",
        candidate_status=candidate_status,
    )
    response = client.get(
        "/api/v1/admin/agent-profiles",
        headers={
            "X-Dev-Auth-Sub": f"denied-admin-{candidate_status}",
            "X-Dev-Auth-AAL": "aal2",
        },
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "candidate_status",
    [
        "prospect",
        "application_started",
        "application_submitted",
        "under_review",
        "more_information_required",
        "interview",
        "conditionally_selected",
        "declined",
        "withdrawn",
        "onboarding_in_progress",
        "pending_fsra_authorization",
        "pending_system_provisioning",
        "suspended",
        "offboarding",
        "offboarded",
    ],
)
def test_nonactive_agent_relationship_is_rejected_before_profile_access(
    client: TestClient, db: Session, candidate_status: str
) -> None:
    create_user(db, subject="phase1e-admin", role_code="brokerage_admin")
    agent, candidate = _agent_account(db)
    candidate.status = candidate_status
    profile = AgentProfile(
        user_id=agent.id,
        slug="denied-agent",
        licensed_name="Denied Agent",
        approved_title="Mortgage Agent",
        licence_number="M00000001",
        status="published",
        published_at=datetime.now(UTC),
    )
    db.add(profile)
    db.commit()

    response = client.get(f"/api/v1/admin/agent-profiles/{profile.id}", headers=ADMIN_HEADERS)
    assert response.status_code == 404
    assert client.get("/api/v1/agents/denied-agent").status_code == 404


def test_agent_role_without_candidate_relationship_remains_profile_eligible(
    client: TestClient, db: Session
) -> None:
    create_user(db, subject="phase1e-admin", role_code="brokerage_admin")
    agent, candidate = create_user(db, subject="agent-without-candidate", role_code="agent")
    assert candidate is None
    profile = AgentProfile(
        user_id=agent.id,
        slug="agent-without-candidate",
        licensed_name="Established Agent",
        approved_title="Mortgage Agent",
        licence_number="M00000003",
        status="published",
        published_at=datetime.now(UTC),
    )
    db.add(profile)
    db.commit()

    assert (
        client.get(f"/api/v1/admin/agent-profiles/{profile.id}", headers=ADMIN_HEADERS).status_code
        == 200
    )
    assert client.get("/api/v1/agents/agent-without-candidate").status_code == 200


def test_profile_mutations_request_the_same_postgresql_row_lock(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = _create_profile(client, db)
    lock_requests: list[bool] = []
    original = agent_routes.get_admin_profile

    def record_lock(session: Session, profile_id, *, lock: bool = False):  # type: ignore[no-untyped-def]
        lock_requests.append(lock)
        return original(session, profile_id)

    monkeypatch.setattr(agent_routes, "get_admin_profile", record_lock)
    patched = client.patch(
        f"/api/v1/admin/agent-profiles/{created['id']}",
        json={"biography": "Serialized profile content."},
        headers=ADMIN_HEADERS,
    )
    transitioned = client.post(
        f"/api/v1/agents/{created['id']}/status",
        json={"status": "pending_approval"},
        headers=ADMIN_HEADERS,
    )

    assert patched.status_code == 200
    assert transitioned.status_code == 200
    assert lock_requests == [True, True]


def test_protected_profile_fetch_compiles_postgresql_for_update() -> None:
    db = Mock(spec=Session)
    get_admin_profile(db, uuid.uuid4(), lock=True)
    statement = db.scalar.call_args.args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE OF agent_profiles" in sql


@pytest.mark.parametrize("duplicate", ["slug", "user"])
def test_duplicate_profile_returns_conflict_without_partial_audit(
    client: TestClient, db: Session, duplicate: str
) -> None:
    create_user(db, subject="phase1e-admin", role_code="brokerage_admin")
    first_agent, _ = _agent_account(db, subject=f"first-{duplicate}-agent")
    second_agent, _ = _agent_account(db, subject=f"second-{duplicate}-agent")
    first_payload = _profile_payload(str(first_agent.id))
    created = client.post("/api/v1/admin/agent-profiles", json=first_payload, headers=ADMIN_HEADERS)
    assert created.status_code == 201

    duplicate_payload = _profile_payload(
        str(first_agent.id if duplicate == "user" else second_agent.id)
    )
    if duplicate == "user":
        duplicate_payload["slug"] = "different-synthetic-agent"
    response = client.post(
        "/api/v1/admin/agent-profiles", json=duplicate_payload, headers=ADMIN_HEADERS
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "agent profile user or slug is already in use"}
    assert (
        db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.event_type == "agent_profile.created")
        )
        == 1
    )
    assert db.scalar(select(func.count()).select_from(AgentProfile)) == 1


def test_editing_published_content_returns_profile_to_pending_approval(
    client: TestClient, db: Session
) -> None:
    created = _create_profile(client, db)
    for target in ["pending_approval", "published"]:
        response = client.post(
            f"/api/v1/agents/{created['id']}/status",
            json={"status": target},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200

    updated = client.patch(
        f"/api/v1/admin/agent-profiles/{created['id']}",
        json={"biography": "Material content requiring renewed approval."},
        headers=ADMIN_HEADERS,
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "pending_approval"
    assert updated.json()["approved_at"] is None
    assert client.get("/api/v1/agents/synthetic-agent").status_code == 404


def test_lifecycle_requires_authorized_publication_and_maps_conflicts(
    client: TestClient, db: Session
) -> None:
    created = _create_profile(client, db)
    profile_id = created["id"]

    invalid = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "published"},
        headers=ADMIN_HEADERS,
    )
    assert invalid.status_code == 409

    submitted = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "pending_approval"},
        headers=ADMIN_HEADERS,
    )
    assert submitted.status_code == 200
    assert submitted.json() == {"status": "pending_approval"}

    denied = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "published"},
        headers={"X-Dev-Auth-Sub": "phase1e-agent", "X-Dev-Auth-AAL": "aal2"},
    )
    assert denied.status_code == 403

    published = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "published"},
        headers=ADMIN_HEADERS,
    )
    assert published.status_code == 200
    assert published.json() == {"status": "published"}


def test_suspension_requires_reason_and_hides_profile(client: TestClient, db: Session) -> None:
    created = _create_profile(client, db)
    profile_id = created["id"]
    for target in ["pending_approval", "published"]:
        response = client.post(
            f"/api/v1/agents/{profile_id}/status",
            json={"status": target},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200

    missing_reason = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "suspended"},
        headers=ADMIN_HEADERS,
    )
    assert missing_reason.status_code == 409

    suspended = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "suspended", "reason": "Public profile review required."},
        headers=ADMIN_HEADERS,
    )
    assert suspended.status_code == 200
    assert client.get("/api/v1/agents/synthetic-agent").status_code == 404
    assert client.get("/api/v1/agents").json()["items"] == []

    republished = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "published"},
        headers=ADMIN_HEADERS,
    )
    assert republished.status_code == 200
    archived = client.post(
        f"/api/v1/agents/{profile_id}/status",
        json={"status": "archived"},
        headers=ADMIN_HEADERS,
    )
    assert archived.status_code == 200
    assert client.get("/api/v1/agents/synthetic-agent").status_code == 404
    assert client.get("/api/v1/agents").json()["items"] == []


def test_only_published_profiles_are_public_and_projection_is_safe(
    client: TestClient, db: Session
) -> None:
    created = _create_profile(client, db)
    assert client.get("/api/v1/agents").json()["items"] == []
    assert client.get("/api/v1/agents/synthetic-agent").status_code == 404

    for target in ["pending_approval", "published"]:
        response = client.post(
            f"/api/v1/agents/{created['id']}/status",
            json={"status": target},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200

    directory = client.get("/api/v1/agents")
    assert directory.status_code == 200
    assert directory.headers["cache-control"] == "no-store"
    assert directory.json()["total"] == 1
    detail = client.get("/api/v1/agents/synthetic-agent")
    assert detail.status_code == 200
    body = detail.json()
    assert body["slug"] == "synthetic-agent"
    assert body["licence_number"] == "M00000000"
    serialized = str(body)
    for forbidden in [
        "user_id",
        "approved_by_user_id",
        "approved_at",
        "published_at",
        "created_at",
        "updated_at",
        "status",
        "version",
        "internal_notes",
        "audit",
        "reason",
    ]:
        assert forbidden not in serialized


@pytest.mark.parametrize(
    "profile_status",
    ["draft", "pending_approval", "suspended", "archived"],
)
def test_nonpublished_profile_detail_is_not_found(
    client: TestClient, db: Session, profile_status: str
) -> None:
    agent, _ = _agent_account(db, subject=f"agent-{profile_status}")
    profile = AgentProfile(
        user_id=agent.id,
        slug=f"agent-{profile_status}",
        licensed_name="Private Agent",
        approved_title="Mortgage Agent",
        licence_number="M00000002",
        status=profile_status,
    )
    db.add(profile)
    db.commit()
    assert client.get(f"/api/v1/agents/{profile.slug}").status_code == 404


@pytest.mark.parametrize(
    "unexpected",
    [
        {"status": "published"},
        {"approved_by_user_id": "00000000-0000-4000-8000-000000000001"},
        {"internal_notes": "must never be accepted"},
        {"borrower_sin": "000-000-000"},
    ],
)
def test_profile_create_rejects_server_owned_sensitive_and_unknown_fields(
    client: TestClient, db: Session, unexpected: dict[str, str]
) -> None:
    _, agent, _ = _create_admin_and_agent(db)
    payload = _profile_payload(str(agent.id)) | unexpected
    response = client.post("/api/v1/admin/agent-profiles", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 422


def test_agent_attribution_uses_only_approved_mapping_and_fails_closed(
    client: TestClient, db: Session, settings
) -> None:
    _create_profile(client, db)
    settings.mortgage_application_provider = "synthetic-provider"
    settings.mortgage_application_url = "https://apply.keeper.example/"
    settings.mortgage_application_allowed_hosts = "apply.keeper.example"
    settings.mortgage_application_agent_links = {}
    unavailable = client.get(
        "/api/v1/integrations/mortgage-application?agent=synthetic-agent",
        follow_redirects=False,
    )
    assert unavailable.status_code == 503
    assert "location" not in unavailable.headers

    settings.mortgage_application_agent_links = {
        "synthetic-agent": "https://apply.keeper.example/synthetic-agent"
    }
    approved = client.get(
        "/api/v1/integrations/mortgage-application?agent=synthetic-agent",
        follow_redirects=False,
    )
    assert approved.status_code == 307
    assert approved.headers["location"] == "https://apply.keeper.example/synthetic-agent"
