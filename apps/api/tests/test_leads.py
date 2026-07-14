import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from keeper_api.models.domain import AuditEvent, ConsentRecord, LeadInquiry
from keeper_api.services.submission_guard import LeadSubmissionGuard, SubmissionRateLimited


def valid_payload() -> dict[str, object]:
    return {
        "name": "Synthetic Visitor",
        "email": "visitor@example.com",
        "telephone": "+1 (416) 555-0100",
        "mortgage_objective": "renewal",
        "preferred_contact_method": "email",
        "message": "Please contact me next week.",
        "service_contact_acknowledged": True,
        "marketing_consent": False,
    }


def test_marketing_consent_is_optional_and_separate(client: TestClient, db: Session) -> None:
    response = client.post("/api/v1/leads", json=valid_payload())
    assert response.status_code == 201
    assert response.json()["marketing_consent_recorded"] is False
    assert db.query(LeadInquiry).count() == 1
    assert [item.purpose for item in db.query(ConsentRecord).all()] == [
        "service_contact_acknowledgement"
    ]


def test_selected_marketing_consent_creates_separate_record(
    client: TestClient, db: Session
) -> None:
    payload = valid_payload()
    payload["marketing_consent"] = True
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 201
    assert sorted(item.purpose for item in db.query(ConsentRecord).all()) == [
        "marketing",
        "service_contact_acknowledgement",
    ]
    audit_event = db.query(AuditEvent).one()
    assert audit_event.event_type == "marketing_consent.granted"
    assert audit_event.request_id == response.headers["X-Request-ID"]


def test_service_acknowledgement_is_required(client: TestClient) -> None:
    payload = valid_payload()
    payload["service_contact_acknowledged"] = False
    assert client.post("/api/v1/leads", json=payload).status_code == 422


def test_contact_form_rejects_disallowed_and_excessive_input(client: TestClient) -> None:
    payload = valid_payload()
    payload["message"] = "My credit card number is in this message."
    assert client.post("/api/v1/leads", json=payload).status_code == 422
    payload["message"] = "x" * 1001
    assert client.post("/api/v1/leads", json=payload).status_code == 422


def test_contact_form_rejects_unapproved_fields(client: TestClient) -> None:
    payload = valid_payload()
    payload["bank_account"] = "123"
    # The explicit forbid policy prevents silent collection when clients send unexpected fields.
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_contact_form_rejects_unknown_agent_attribution(client: TestClient) -> None:
    payload = valid_payload()
    payload["preferred_agent_slug"] = "unapproved-agent"
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_contact_form_rejects_filled_automation_trap(client: TestClient) -> None:
    payload = valid_payload()
    payload["website"] = "https://bot.example"
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_contact_form_rate_limit_fails_closed_and_ignores_forwarded_headers(
    client: TestClient,
) -> None:
    guard = LeadSubmissionGuard(request_limit=2, window_seconds=60, tracked_clients=100)
    client.app.state.lead_submission_guard = guard

    first = client.post(
        "/api/v1/leads",
        json=valid_payload(),
        headers={"X-Forwarded-For": "198.51.100.1"},
    )
    second = client.post(
        "/api/v1/leads",
        json=valid_payload(),
        headers={"X-Forwarded-For": "198.51.100.2"},
    )
    denied = client.post(
        "/api/v1/leads",
        json=valid_payload(),
        headers={"X-Forwarded-For": "198.51.100.3"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert denied.status_code == 429
    assert denied.headers["Retry-After"] == "60"


def test_contact_form_rate_limit_denies_new_clients_when_tracking_is_full() -> None:
    guard = LeadSubmissionGuard(request_limit=2, window_seconds=60, tracked_clients=1)
    guard.check("198.51.100.1", now=10)

    with pytest.raises(SubmissionRateLimited, match="rate limit exceeded"):
        guard.check("198.51.100.2", now=10)
