import json
import uuid
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.core.config import Settings
from keeper_api.models.domain import (
    AgentProfile,
    AuditEvent,
    ConsentRecord,
    LeadInquiry,
    User,
)
from keeper_api.services.audit import AuditService
from keeper_api.services.submission_guard import LeadSubmissionGuard, SubmissionRateLimited

SERVICE_WORDING_VERSION = "service-contact-draft-engineering-v1"
MARKETING_WORDING_VERSION = "marketing-draft-engineering-v1"
PRIVACY_NOTICE_VERSION = "privacy-notice-draft-legal-review-v1"


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


def test_prescribed_synthetic_smoke_address_is_accepted(client: TestClient) -> None:
    payload = valid_payload()
    payload["email"] = "phase1b@example.test"

    response = client.post("/api/v1/leads", json=payload)

    assert response.status_code == 201


@pytest.mark.parametrize("email", ["not-an-address", "visitor@", "@example.com"])
def test_malformed_email_is_rejected(client: TestClient, email: str) -> None:
    payload = valid_payload()
    payload["email"] = email

    assert client.post("/api/v1/leads", json=payload).status_code == 422


def test_marketing_consent_is_optional_and_separate(client: TestClient, db: Session) -> None:
    response = client.post("/api/v1/leads", json=valid_payload())
    assert response.status_code == 201
    assert response.json()["marketing_consent_recorded"] is False
    assert db.query(LeadInquiry).count() == 1
    assert [item.purpose for item in db.query(ConsentRecord).all()] == [
        "service_contact_acknowledgement"
    ]
    service = db.query(ConsentRecord).one()
    assert service.wording_version == SERVICE_WORDING_VERSION
    assert service.privacy_notice_version == PRIVACY_NOTICE_VERSION
    assert service.capture_source == "website_apply"

    audit_event = db.query(AuditEvent).one()
    assert audit_event.event_type == "lead.created"
    assert audit_event.target_id == uuid.UUID(response.json()["id"])
    assert audit_event.safe_metadata == {"status": "new", "source": "website_apply"}


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
    marketing = db.query(ConsentRecord).filter(ConsentRecord.purpose == "marketing").one()
    assert marketing.wording_version == MARKETING_WORDING_VERSION
    assert marketing.privacy_notice_version == PRIVACY_NOTICE_VERSION
    assert marketing.capture_source == "website_apply"
    audit_events = db.query(AuditEvent).order_by(AuditEvent.event_type).all()
    assert [event.event_type for event in audit_events] == [
        "lead.created",
        "marketing_consent.granted",
    ]
    assert all(event.request_id == response.headers["X-Request-ID"] for event in audit_events)


@pytest.mark.parametrize(
    "field",
    ["service_wording_version", "marketing_wording_version", "privacy_notice_version"],
)
def test_caller_cannot_override_server_owned_consent_versions(
    client: TestClient, field: str
) -> None:
    payload = valid_payload()
    payload[field] = "caller-selected-version"
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


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


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "Synthetic\x00Visitor"),
        ("message", "My medical diagnosis is attached."),
        ("message", "Here are the underwriting documents."),
        ("message", "My password is synthetic-secret."),
    ],
)
def test_contact_form_rejects_controls_and_sensitive_categories(
    client: TestClient, field: str, value: str
) -> None:
    payload = valid_payload()
    payload[field] = value
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


@pytest.mark.parametrize("profile_status,expected", [("published", 201), ("draft", 422)])
def test_contact_form_accepts_only_published_agent_profile_attribution(
    client: TestClient, db: Session, profile_status: str, expected: int
) -> None:
    user = User(
        email=f"agent-{profile_status}@example.test",
        display_name=f"Synthetic {profile_status} agent",
    )
    db.add(user)
    db.flush()
    db.add(
        AgentProfile(
            user_id=user.id,
            slug=f"agent-{profile_status}",
            licensed_name="Synthetic Agent",
            approved_title="Mortgage Agent",
            licence_number="SYNTHETIC",
            status=profile_status,
        )
    )
    db.commit()
    payload = valid_payload()
    payload["preferred_agent_slug"] = f"agent-{profile_status}"

    response = client.post("/api/v1/leads", json=payload)

    assert response.status_code == expected
    if expected == 201:
        assert db.query(LeadInquiry).one().preferred_agent_slug == "agent-published"
    else:
        assert db.query(LeadInquiry).count() == 0
        assert db.query(ConsentRecord).count() == 0
        assert db.query(AuditEvent).count() == 0


def test_contact_form_rejects_filled_automation_trap(client: TestClient) -> None:
    payload = valid_payload()
    payload["website"] = "https://bot.example"
    response = client.post("/api/v1/leads", json=payload)
    assert response.status_code == 422


def test_public_response_discloses_only_receipt_fields(client: TestClient) -> None:
    response = client.post("/api/v1/leads", json=valid_payload())
    assert response.status_code == 201
    assert set(response.json()) == {"id", "status", "marketing_consent_recorded"}
    assert not response.headers.get("Location")


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

    # A full table must not lock out an already tracked peer before its own boundary.
    guard.check("198.51.100.1", now=11)


def test_contact_form_rate_limit_boundary_reopens_after_window() -> None:
    guard = LeadSubmissionGuard(request_limit=1, window_seconds=60, tracked_clients=1)
    guard.check("198.51.100.1", now=10)
    with pytest.raises(SubmissionRateLimited) as denied:
        guard.check("198.51.100.1", now=69.1)
    assert denied.value.retry_after_seconds == 1
    guard.check("198.51.100.1", now=70)


def test_lead_consent_and_audit_persistence_is_atomic_on_failure(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = valid_payload()
    payload["marketing_consent"] = True
    original_record = AuditService.record

    def fail_marketing_audit(self: AuditService, event_type: str, *args: object, **kwargs: object):
        if event_type == "marketing_consent.granted":
            raise RuntimeError("synthetic persistence failure")
        return original_record(self, event_type, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(AuditService, "record", fail_marketing_audit)
    with pytest.raises(RuntimeError, match="synthetic persistence failure"):
        client.post("/api/v1/leads", json=payload)

    assert db.query(LeadInquiry).count() == 0
    assert db.query(ConsentRecord).count() == 0
    assert db.query(AuditEvent).count() == 0


def test_lead_audit_and_request_logs_exclude_contact_and_payload_data(
    client: TestClient, db: Session, caplog: pytest.LogCaptureFixture
) -> None:
    payload = valid_payload()
    payload["message"] = "Reference https://private.example/path?case=synthetic"
    payload["marketing_consent"] = True

    response = client.post(
        "/api/v1/leads",
        json=payload,
        headers={"X-Request-ID": "safe-request-id"},
    )
    assert response.status_code == 201
    serialized_audits = json.dumps(
        [event.safe_metadata for event in db.query(AuditEvent).all()], default=str
    )
    serialized_logs = " ".join(record.getMessage() for record in caplog.records)
    for forbidden in [
        str(payload["name"]),
        str(payload["email"]),
        str(payload["telephone"]),
        str(payload["message"]),
        "private.example",
        "case=synthetic",
    ]:
        assert forbidden not in serialized_audits
        assert forbidden not in serialized_logs


def _lead(
    db: Session,
    *,
    suffix: str,
    created_at: datetime,
    status: str = "new",
    marketing: bool = False,
) -> LeadInquiry:
    lead = LeadInquiry(
        name=f"Synthetic Lead {suffix}",
        email=f"lead-{suffix}@example.com",
        telephone=f"+1 416 555 01{suffix}",
        mortgage_objective="renewal",
        preferred_contact_method="email",
        message=f"Synthetic message {suffix}",
        source="website_apply",
        status=status,
        created_at=created_at,
    )
    db.add(lead)
    db.flush()
    db.add(
        ConsentRecord(
            lead_inquiry_id=lead.id,
            purpose="service_contact_acknowledgement",
            wording_version=SERVICE_WORDING_VERSION,
            privacy_notice_version=PRIVACY_NOTICE_VERSION,
            capture_source="website_apply",
            granted_at=created_at,
        )
    )
    if marketing:
        db.add(
            ConsentRecord(
                lead_inquiry_id=lead.id,
                purpose="marketing",
                wording_version=MARKETING_WORDING_VERSION,
                privacy_notice_version=PRIVACY_NOTICE_VERSION,
                capture_source="website_apply",
                granted_at=created_at,
            )
        )
    db.commit()
    return lead


def _admin_headers(subject: str = "lead-admin", aal: str = "aal2") -> dict[str, str]:
    return {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": aal}


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
        ("admin-aal2", 200),
    ],
)
@pytest.mark.parametrize("operation", ["list", "withdraw", "status"])
def test_admin_lead_operations_enforce_full_denial_matrix(
    client: TestClient,
    db: Session,
    settings: Settings,
    case: str,
    expected: int,
    operation: str,
) -> None:
    settings.require_admin_mfa = True
    lead = _lead(db, suffix=f"{case}-{operation}", created_at=datetime.now(UTC), marketing=True)
    headers: dict[str, str] = {}
    if case == "unmapped":
        headers = _admin_headers("not-mapped")
    elif case == "identity-only":
        create_user(db, subject=f"identity-only-{operation}")
        headers = _admin_headers(f"identity-only-{operation}")
    elif case == "wrong-role":
        create_user(db, subject=f"wrong-role-{operation}", role_code="operations")
        headers = _admin_headers(f"wrong-role-{operation}")
    elif case == "inactive":
        create_user(db, subject=f"inactive-{operation}", role_code="brokerage_admin", active=False)
        headers = _admin_headers(f"inactive-{operation}")
    elif case == "candidate":
        create_user(
            db,
            subject=f"candidate-{operation}",
            role_code="candidate",
            candidate_status="application_started",
        )
        headers = _admin_headers(f"candidate-{operation}")
    elif case == "admin-aal1":
        create_user(db, subject=f"admin-aal1-{operation}", role_code="brokerage_admin")
        headers = _admin_headers(f"admin-aal1-{operation}", "aal1")
    elif case == "admin-aal2":
        create_user(db, subject=f"admin-aal2-{operation}", role_code="brokerage_admin")
        headers = _admin_headers(f"admin-aal2-{operation}")

    if operation == "list":
        response = client.get("/api/v1/leads", headers=headers)
    elif operation == "withdraw":
        response = client.post(
            f"/api/v1/leads/{lead.id}/marketing-consent/withdrawal", headers=headers
        )
    else:
        response = client.post(
            f"/api/v1/leads/{lead.id}/status",
            headers=headers,
            json={"status": "contacted"},
        )

    assert response.status_code == expected
    assert response.headers["Cache-Control"] == "no-store"


def test_admin_lead_list_is_bounded_ordered_filtered_and_no_store(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    now = datetime.now(UTC)
    older = _lead(db, suffix="01", created_at=now - timedelta(days=2), status="contacted")
    first_new = _lead(db, suffix="02", created_at=now - timedelta(days=1), marketing=True)
    newest = _lead(db, suffix="03", created_at=now, marketing=True)

    first_page = client.get("/api/v1/leads?limit=2&offset=0", headers=_admin_headers())
    assert first_page.status_code == 200
    assert first_page.headers["Cache-Control"] == "no-store"
    body = first_page.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [item["id"] for item in body["items"]] == [str(newest.id), str(first_new.id)]
    assert body["items"][0]["service_consent"]["state"] == "granted"
    assert body["items"][0]["marketing_consent"]["state"] == "granted"
    assert body["items"][0]["marketing_consent"]["granted_at"] is not None
    assert body["items"][0]["marketing_consent"]["withdrawn_at"] is None

    second_page = client.get("/api/v1/leads?limit=2&offset=2", headers=_admin_headers())
    assert [item["id"] for item in second_page.json()["items"]] == [str(older.id)]

    filtered = client.get("/api/v1/leads?status=contacted", headers=_admin_headers())
    assert filtered.json()["total"] == 1
    assert [item["id"] for item in filtered.json()["items"]] == [str(older.id)]
    assert client.get("/api/v1/leads?limit=101", headers=_admin_headers()).status_code == 422
    assert client.get("/api/v1/leads?status=pending", headers=_admin_headers()).status_code == 422
    assert (
        client.get("/api/v1/leads?email=visitor@example.com", headers=_admin_headers()).status_code
        == 422
    )


def test_marketing_withdrawal_is_idempotent_and_preserves_service_consent(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    admin, _ = create_user(db, subject="lead-admin", role_code="brokerage_admin")
    lead = _lead(db, suffix="withdraw", created_at=datetime.now(UTC), marketing=True)
    marketing = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.lead_inquiry_id == lead.id, ConsentRecord.purpose == "marketing")
        .one()
    )
    service = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.lead_inquiry_id == lead.id,
            ConsentRecord.purpose == "service_contact_acknowledgement",
        )
        .one()
    )
    granted_at = marketing.granted_at
    service_granted_at = service.granted_at

    first = client.post(
        f"/api/v1/leads/{lead.id}/marketing-consent/withdrawal",
        headers={**_admin_headers(), "X-Request-ID": "withdraw-request"},
    )
    assert first.status_code == 200
    assert first.headers["Cache-Control"] == "no-store"
    assert first.json()["state"] == "withdrawn"
    withdrawn_at = first.json()["withdrawn_at"]
    second = client.post(
        f"/api/v1/leads/{lead.id}/marketing-consent/withdrawal",
        headers={**_admin_headers(), "X-Request-ID": "second-request"},
    )
    assert second.status_code == 200
    assert second.json()["withdrawn_at"] == withdrawn_at

    db.expire_all()
    assert db.get(ConsentRecord, marketing.id).granted_at == granted_at  # type: ignore[union-attr]
    assert db.get(ConsentRecord, service.id).granted_at == service_granted_at  # type: ignore[union-attr]
    assert db.get(ConsentRecord, service.id).withdrawn_at is None  # type: ignore[union-attr]
    withdrawal_audits = (
        db.query(AuditEvent).filter(AuditEvent.event_type == "marketing_consent.withdrawn").all()
    )
    assert len(withdrawal_audits) == 1
    audit = withdrawal_audits[0]
    assert audit.actor_user_id == admin.id
    assert audit.request_id == "withdraw-request"
    assert audit.target_type == "consent_record"
    assert audit.target_id == marketing.id
    assert audit.safe_metadata == {"capture_source": "website_apply"}


def test_admin_can_update_lead_status_with_safe_audit_and_no_store(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    admin, _ = create_user(db, subject="lead-status-admin", role_code="brokerage_admin")
    lead = _lead(db, suffix="status", created_at=datetime.now(UTC), status="new")

    first = client.post(
        f"/api/v1/leads/{lead.id}/status",
        headers={**_admin_headers("lead-status-admin"), "X-Request-ID": "lead-status-change"},
        json={"status": "contacted"},
    )

    assert first.status_code == 200
    assert first.headers["Cache-Control"] == "no-store"
    assert first.json() == {"id": str(lead.id), "status": "contacted"}
    db.expire_all()
    assert db.get(LeadInquiry, lead.id).status == "contacted"  # type: ignore[union-attr]
    audit = db.query(AuditEvent).filter(AuditEvent.event_type == "lead.status_changed").one()
    assert audit.actor_user_id == admin.id
    assert audit.target_type == "lead_inquiry"
    assert audit.target_id == lead.id
    assert audit.request_id == "lead-status-change"
    assert audit.safe_metadata == {"from_status": "new", "to_status": "contacted"}

    second = client.post(
        f"/api/v1/leads/{lead.id}/status",
        headers=_admin_headers("lead-status-admin"),
        json={"status": "contacted"},
    )
    assert second.status_code == 200
    assert db.query(AuditEvent).filter(AuditEvent.event_type == "lead.status_changed").count() == 1


def test_admin_lead_status_update_rejects_unknown_lead_or_status(
    client: TestClient, db: Session, settings: Settings
) -> None:
    settings.require_admin_mfa = True
    create_user(db, subject="lead-status-admin", role_code="brokerage_admin")
    lead = _lead(db, suffix="status-invalid", created_at=datetime.now(UTC), status="new")

    invalid_status = client.post(
        f"/api/v1/leads/{lead.id}/status",
        headers=_admin_headers("lead-status-admin"),
        json={"status": "pending"},
    )
    missing = client.post(
        "/api/v1/leads/00000000-0000-4000-8000-000000000001/status",
        headers=_admin_headers("lead-status-admin"),
        json={"status": "closed"},
    )

    assert invalid_status.status_code == 422
    assert missing.status_code == 404
    assert missing.headers["Cache-Control"] == "no-store"
    assert db.get(LeadInquiry, lead.id).status == "new"  # type: ignore[union-attr]


@pytest.mark.parametrize("marketing", [False, True])
def test_marketing_withdrawal_unknown_or_absent_consent_fails_safely(
    client: TestClient, db: Session, settings: Settings, marketing: bool
) -> None:
    settings.require_admin_mfa = True
    create_user(db, subject="lead-admin", role_code="brokerage_admin")
    lead = _lead(
        db, suffix=f"missing-{marketing}", created_at=datetime.now(UTC), marketing=marketing
    )
    lead_id = lead.id if not marketing else "00000000-0000-4000-8000-000000000001"

    response = client.post(
        f"/api/v1/leads/{lead_id}/marketing-consent/withdrawal", headers=_admin_headers()
    )

    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
    assert db.query(AuditEvent).count() == 0


class FakeLeadSMTP:
    messages: ClassVar[list[EmailMessage]] = []

    def __init__(self, host: str, port: int, timeout: int = 10) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def __enter__(self) -> "FakeLeadSMTP":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def starttls(self) -> None:
        return None

    def send_message(self, message: EmailMessage) -> None:
        self.messages.append(message)


def message_text(message: EmailMessage) -> str:
    if message.is_multipart():
        return "\n".join(
            part.get_content()
            for part in message.iter_parts()
            if part.get_content_type() == "text/plain"
        )
    return message.get_content()


def enable_lead_notifications(settings: Settings) -> None:
    settings.smtp_enabled = True
    settings.lead_notification_email_enabled = True
    settings.lead_notification_admin_email = "admin@example.test"
    settings.lead_notification_broker_email = "broker@example.test"


def test_contact_lead_notifies_selected_agent_and_admin_without_pii(
    client: TestClient, db: Session, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    enable_lead_notifications(settings)
    settings.smtp_port = 1025
    FakeLeadSMTP.messages = []
    monkeypatch.setattr("keeper_api.services.lead_notifications.smtplib.SMTP", FakeLeadSMTP)
    agent = User(email="agent@example.test", display_name="Synthetic Agent")
    db.add(agent)
    db.flush()
    db.add(
        AgentProfile(
            user_id=agent.id,
            slug="published-agent",
            licensed_name="Synthetic Agent",
            approved_title="Mortgage Agent",
            licence_number="SYNTHETIC",
            status="published",
        )
    )
    db.commit()
    payload = valid_payload()
    payload["preferred_agent_slug"] = "published-agent"

    response = client.post("/api/v1/leads", json=payload)

    assert response.status_code == 201
    assert [message["To"] for message in FakeLeadSMTP.messages] == [
        "agent@example.test",
        "admin@example.test",
    ]
    bodies = "\n".join(message_text(message) for message in FakeLeadSMTP.messages)
    assert str(response.json()["id"]) in bodies
    assert "/admin/leads" in bodies
    assert "Synthetic Visitor" not in bodies
    assert "visitor@example.com" not in bodies
    assert "+1 (416) 555-0100" not in bodies
    assert "Please contact me next week" not in bodies


def test_contact_lead_notifies_broker_and_admin_when_no_agent_selected(
    client: TestClient, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    enable_lead_notifications(settings)
    settings.smtp_port = 1025
    FakeLeadSMTP.messages = []
    monkeypatch.setattr("keeper_api.services.lead_notifications.smtplib.SMTP", FakeLeadSMTP)

    response = client.post("/api/v1/leads", json=valid_payload())

    assert response.status_code == 201
    assert [message["To"] for message in FakeLeadSMTP.messages] == [
        "broker@example.test",
        "admin@example.test",
    ]


def test_contact_lead_notification_uses_local_mailpit_http_api(
    client: TestClient, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    enable_lead_notifications(settings)
    settings.smtp_host = "host.docker.internal"
    FakeLeadSMTP.messages = []
    attempted_urls: list[str] = []
    sent_payloads: list[dict[str, object]] = []

    class LocalMailpitResponse:
        status = 200

        def __enter__(self) -> "LocalMailpitResponse":
            return self

        def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
            return None

    def fake_urlopen(api_request: object, timeout: int) -> LocalMailpitResponse:
        attempted_urls.append(api_request.full_url)  # type: ignore[attr-defined]
        if api_request.full_url.startswith("http://host.docker.internal"):  # type: ignore[attr-defined]
            raise OSError("synthetic host gateway is unavailable on host API")
        sent_payloads.append(json.loads(api_request.data.decode("utf-8")))  # type: ignore[attr-defined]
        return LocalMailpitResponse()

    monkeypatch.setattr("keeper_api.services.lead_notifications.request.urlopen", fake_urlopen)
    monkeypatch.setattr("keeper_api.services.lead_notifications.smtplib.SMTP", FakeLeadSMTP)

    response = client.post("/api/v1/leads", json=valid_payload())

    assert response.status_code == 201
    assert attempted_urls == [
        "http://host.docker.internal:54324/api/v1/send",
        "http://127.0.0.1:54324/api/v1/send",
        "http://host.docker.internal:54324/api/v1/send",
        "http://127.0.0.1:54324/api/v1/send",
    ]
    assert [payload["To"] for payload in sent_payloads] == [
        [{"Email": "broker@example.test"}],
        [{"Email": "admin@example.test"}],
    ]
    assert [payload["Tags"] for payload in sent_payloads] == [
        ["keeper-local-lead-notification"],
        ["keeper-local-lead-notification"],
    ]
    assert FakeLeadSMTP.messages == []


def test_contact_lead_notification_falls_back_to_loopback_smtp_for_host_api(
    client: TestClient, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    enable_lead_notifications(settings)
    settings.smtp_host = "host.docker.internal"
    settings.smtp_port = 1025
    FakeLeadSMTP.messages = []
    attempted_hosts: list[str] = []

    class LocalFallbackSMTP(FakeLeadSMTP):
        def __init__(self, host: str, port: int, timeout: int) -> None:
            attempted_hosts.append(host)
            if host == "host.docker.internal":
                raise OSError("synthetic host gateway is unavailable on host API")
            super().__init__(host, port, timeout)

    monkeypatch.setattr("keeper_api.services.lead_notifications.smtplib.SMTP", LocalFallbackSMTP)

    response = client.post("/api/v1/leads", json=valid_payload())

    assert response.status_code == 201
    assert attempted_hosts == [
        "host.docker.internal",
        "127.0.0.1",
        "host.docker.internal",
        "127.0.0.1",
    ]
    assert [message["To"] for message in FakeLeadSMTP.messages] == [
        "broker@example.test",
        "admin@example.test",
    ]


def test_contact_lead_submission_succeeds_when_notification_smtp_fails(
    client: TestClient, db: Session, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    enable_lead_notifications(settings)

    class FailingSMTP(FakeLeadSMTP):
        def send_message(self, message: EmailMessage) -> None:
            raise OSError("synthetic SMTP outage")

    monkeypatch.setattr("keeper_api.services.lead_notifications.smtplib.SMTP", FailingSMTP)

    response = client.post("/api/v1/leads", json=valid_payload())

    assert response.status_code == 201
    assert db.query(LeadInquiry).count() == 1
