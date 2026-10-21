"""Administrator lead assignment and agent-scoped lead visibility."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import (
    AgentReferralLink,
    AuditEvent,
    Candidate,
    LeadInquiry,
    Role,
    UserRole,
)


def _headers(subject: str, aal: str = "aal2") -> dict[str, str]:
    return {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": aal}


def _lead_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Synthetic Visitor",
        "email": "visitor@example.com",
        "telephone": "+1 (416) 555-0100",
        "mortgage_objective": "purchase",
        "preferred_contact_method": "telephone",
        "message": "Call me about a first purchase.",
        "service_contact_acknowledged": True,
        "marketing_consent": False,
    }
    payload.update(overrides)
    return payload


def _make_agent(db: Session, subject: str, *, with_link: bool = False):
    user, _ = create_user(db, subject=subject, role_code="agent", candidate_status="active")
    link = None
    if with_link:
        link = AgentReferralLink(user_id=user.id, code=uuid.uuid4().hex[:20])
        db.add(link)
    db.commit()
    return user, link


def _create_lead(client: TestClient, **overrides: object) -> uuid.UUID:
    response = client.post("/api/v1/leads", json=_lead_payload(**overrides))
    assert response.status_code == 201, response.text
    return uuid.UUID(response.json()["id"])


def test_admin_assigns_reassigns_and_clears_a_lead(client: TestClient, db: Session) -> None:
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    first, _ = _make_agent(db, "assign-agent-a")
    second, _ = _make_agent(db, "assign-agent-b")
    lead_id = _create_lead(client)

    assigned = client.post(
        f"/api/v1/leads/{lead_id}/assignment",
        json={"agent_user_id": str(first.id)},
        headers=_headers("lead-admin"),
    )
    assert assigned.status_code == 200
    assert assigned.json() == {"id": str(lead_id), "status": "assigned"}
    lead = db.get(LeadInquiry, lead_id)
    assert lead is not None
    assert lead.assigned_agent_user_id == first.id
    assert lead.assigned_by_user_id is not None
    assert lead.assigned_at is not None
    assert lead.attribution_source == "administrator"

    reassigned = client.post(
        f"/api/v1/leads/{lead_id}/assignment",
        json={"agent_user_id": str(second.id)},
        headers=_headers("lead-admin"),
    )
    assert reassigned.status_code == 200
    db.refresh(lead)
    assert lead.assigned_agent_user_id == second.id

    cleared = client.post(
        f"/api/v1/leads/{lead_id}/assignment",
        json={"agent_user_id": None},
        headers=_headers("lead-admin"),
    )
    assert cleared.status_code == 200
    assert cleared.json()["status"] == "new"
    db.refresh(lead)
    assert lead.assigned_agent_user_id is None
    assert lead.attribution_source is None

    events = [
        row.event_type
        for row in db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.asc())).all()
        if row.target_id == lead_id
    ]
    assert "lead.assigned" in events
    assert "lead.unassigned" in events


def test_assignment_rejects_an_account_that_is_not_an_onboarded_agent(
    client: TestClient, db: Session
) -> None:
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    candidate_only, _ = create_user(
        db, subject="plain-candidate", role_code="candidate", candidate_status="active"
    )
    lead_id = _create_lead(client)

    response = client.post(
        f"/api/v1/leads/{lead_id}/assignment",
        json={"agent_user_id": str(candidate_only.id)},
        headers=_headers("lead-admin"),
    )

    assert response.status_code == 409
    lead = db.get(LeadInquiry, lead_id)
    assert lead is not None and lead.assigned_agent_user_id is None


def test_assignable_agents_lists_only_onboarded_agents(client: TestClient, db: Session) -> None:
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    onboarded, link = _make_agent(db, "listable-agent", with_link=True)
    assert link is not None
    _make_agent(db, "linkless-agent")
    create_user(db, subject="not-an-agent", role_code="candidate", candidate_status="active")

    response = client.get("/api/v1/leads/assignable-agents", headers=_headers("lead-admin"))

    assert response.status_code == 200
    items = response.json()["items"]
    listed = {item["user_id"]: item for item in items}
    assert listed[str(onboarded.id)]["has_referral_link"] is True
    assert listed[str(onboarded.id)]["display_name"]
    assert len(items) == 2


def test_agent_reads_only_inquiries_assigned_to_them(client: TestClient, db: Session) -> None:
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    owner, _ = _make_agent(db, "owner-agent")
    other, _ = _make_agent(db, "other-agent")
    lead_id = _create_lead(client, name="Assigned Applicant", agent_reference=None)
    # Assignment is explicit here: no reference was submitted.
    assert (
        client.post(
            f"/api/v1/leads/{lead_id}/assignment",
            json={"agent_user_id": str(owner.id)},
            headers=_headers("lead-admin"),
        ).status_code
        == 200
    )

    listing = client.get("/api/v1/agent/leads", headers=_headers("owner-agent"))
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    item = listing.json()["items"][0]
    assert item["id"] == str(lead_id)
    assert item["name"] == "Assigned Applicant"
    # The list is a summary: contact details require the audited detail read.
    assert "email" not in item

    detail = client.get(f"/api/v1/agent/leads/{lead_id}", headers=_headers("owner-agent"))
    assert detail.status_code == 200
    body = detail.json()
    assert body["name"] == "Assigned Applicant"
    assert body["email"] == "visitor@example.com"
    assert body["telephone"] == "+1 (416) 555-0100"
    assert body["message"] == "Call me about a first purchase."
    assert body["preferred_contact_method"] == "telephone"
    assert body["service_consent"]["state"] == "granted"

    other_list = client.get("/api/v1/agent/leads", headers=_headers("other-agent"))
    assert other_list.status_code == 200
    assert other_list.json()["total"] == 0
    # An inquiry owned by another agent is indistinguishable from a missing one.
    assert (
        client.get(f"/api/v1/agent/leads/{lead_id}", headers=_headers("other-agent")).status_code
        == 404
    )

    views = [
        row
        for row in db.scalars(
            select(AuditEvent).where(AuditEvent.event_type == "agent_lead_viewed")
        ).all()
    ]
    assert len(views) == 1
    assert views[0].target_id == lead_id


def test_agent_lead_access_requires_agent_role_and_mfa(client: TestClient, db: Session) -> None:
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    agent, _ = _make_agent(db, "mfa-agent")
    candidate_only, _ = create_user(
        db, subject="mfa-candidate", role_code="candidate", candidate_status="active"
    )
    lead_id = _create_lead(client)
    client.post(
        f"/api/v1/leads/{lead_id}/assignment",
        json={"agent_user_id": str(agent.id)},
        headers=_headers("lead-admin"),
    )

    low_assurance = client.get("/api/v1/agent/leads", headers=_headers("mfa-agent", aal="aal1"))
    assert low_assurance.status_code == 403
    assert "MFA" in low_assurance.json()["detail"]

    wrong_role = client.get("/api/v1/agent/leads", headers=_headers("mfa-candidate"))
    assert wrong_role.status_code == 403

    anonymous = client.get("/api/v1/agent/leads")
    assert anonymous.status_code == 401


def test_inactive_agent_relationship_revokes_lead_visibility(
    client: TestClient, db: Session
) -> None:
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    agent, _ = _make_agent(db, "revoked-agent")
    lead_id = _create_lead(client)
    client.post(
        f"/api/v1/leads/{lead_id}/assignment",
        json={"agent_user_id": str(agent.id)},
        headers=_headers("lead-admin"),
    )
    candidate = db.scalar(select(Candidate).where(Candidate.user_id == agent.id))
    assert candidate is not None
    candidate.status = "offboarded"
    db.commit()

    response = client.get("/api/v1/agent/leads", headers=_headers("revoked-agent"))

    assert response.status_code == 403


def test_role_grant_alone_does_not_authorise_a_lead_without_an_active_relationship(
    client: TestClient, db: Session
) -> None:
    user, _ = create_user(db, subject="role-only-agent")
    role = db.scalar(select(Role).where(Role.code == "agent"))
    if role is None:
        role = Role(code="agent", description="Synthetic agent")
        db.add(role)
        db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()

    response = client.get("/api/v1/agent/leads", headers=_headers("role-only-agent"))

    assert response.status_code == 403
