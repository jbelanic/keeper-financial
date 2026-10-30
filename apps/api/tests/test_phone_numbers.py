"""Phone entry and display rules across the public and internal forms.

The applicant types a phone number the way people actually write one. These
tests pin the canonical stored value (E.164) and the display form
``(519) 123-4567`` so the public contact form, the candidate application, and the
agent profile stay consistent.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.core.phone import (
    format_phone_display,
    nanp_national_number,
    normalize_nanp_phone,
    normalize_phone,
    phone_tel_href,
)
from keeper_api.models.domain import LeadInquiry

ADMIN_HEADERS = {"X-Dev-Auth-Sub": "phone-admin", "X-Dev-Auth-AAL": "aal2"}


def _admin(db: Session) -> None:
    create_user(db, subject="phone-admin", role_code="brokerage_admin")


def _lead_payload(telephone: str) -> dict[str, object]:
    return {
        "name": "Synthetic Phone Applicant",
        "email": "phone-applicant@example.test",
        "telephone": telephone,
        "mortgage_objective": "purchase",
        "preferred_contact_method": "telephone",
        "service_contact_acknowledged": True,
        "marketing_consent": False,
        "website": "",
    }


def _agent_payload(user_id: str, telephone: str) -> dict[str, object]:
    return {
        "user_id": user_id,
        "slug": "phone-format-agent",
        "licensed_name": "Synthetic Phone Agent",
        "approved_title": "Mortgage Agent Level 2",
        "licence_number": "M00000001",
        "biography": "Synthetic, public-safe biography for deterministic tests.",
        "languages": ["English"],
        "service_areas": ["London"],
        "specialties": ["Purchases"],
        "public_email": "phone.synthetic.agent@example.test",
        "public_phone": telephone,
        "social_links": [],
    }


class TestNormalization:
    def test_accepts_the_ways_people_type_a_number(self) -> None:
        for typed in ["5195550123", "519-555-0123", "(519) 555-0123", "+1 519 555 0123"]:
            assert normalize_nanp_phone(typed) == "+15195550123", typed

    def test_rejects_short_and_alphanumeric_values(self) -> None:
        for typed in ["519555012", "51955", "call me", "519-555-01234"]:
            assert nanp_national_number(typed) is None, typed

    def test_keeps_an_explicit_international_number_when_allowed(self) -> None:
        assert normalize_phone("+44 20 7946 0958", allow_international=True) == "+442079460958"
        assert normalize_phone("+44207946", allow_international=True) == "+44207946"

    def test_refuses_an_international_number_when_not_allowed(self) -> None:
        try:
            normalize_phone("+44 20 7946 0958", allow_international=False)
        except ValueError as exc:
            assert "10-digit" in str(exc)
        else:  # pragma: no cover - the value must be refused
            raise AssertionError("international number was accepted")

    def test_blank_stays_blank(self) -> None:
        assert normalize_nanp_phone(None) is None
        assert normalize_nanp_phone("   ") is None


class TestDisplay:
    def test_renders_the_north_american_form(self) -> None:
        assert format_phone_display("+15195550123") == "(519) 555-0123"
        assert format_phone_display("519-555-0123") == "(519) 555-0123"
        assert format_phone_display("5551231234") == "(555) 123-1234"

    def test_leaves_an_unrecognised_historical_value_untouched(self) -> None:
        assert format_phone_display("555-123") == "555-123"
        assert format_phone_display(None) is None

    def test_tel_href_is_dialable(self) -> None:
        assert phone_tel_href("+15195550123") == "tel:+15195550123"
        assert phone_tel_href("(519) 555-0123") == "tel:+15195550123"
        assert phone_tel_href("+442079460958") == "tel:+442079460958"


def test_contact_form_stores_one_canonical_number(client: TestClient, db: Session) -> None:
    response = client.post("/api/v1/leads", json=_lead_payload("519-555-0142"))
    assert response.status_code == 201, response.text

    stored = db.scalar(
        select(LeadInquiry).where(LeadInquiry.email == "phone-applicant@example.test")
    )
    assert stored is not None
    assert stored.telephone == "+15195550142"


def test_contact_form_refuses_an_unusable_number(client: TestClient) -> None:
    response = client.post("/api/v1/leads", json=_lead_payload("51955501"))
    assert response.status_code == 422
    assert "10-digit" in response.text


def test_agent_profile_stores_e164_and_the_page_shows_the_display_form(
    client: TestClient, db: Session
) -> None:
    _admin(db)
    agent, _ = create_user(db, subject="phone-agent", role_code="agent", candidate_status="active")
    created = client.post(
        "/api/v1/admin/agent-profiles",
        json=_agent_payload(str(agent.id), "(519) 123-4567"),
        headers=ADMIN_HEADERS,
    )
    assert created.status_code == 201, created.text
    assert created.json()["public_phone"] == "+15191234567"
    assert format_phone_display(created.json()["public_phone"]) == "(519) 123-4567"


def test_agent_profile_refuses_an_unusable_public_phone(client: TestClient, db: Session) -> None:
    _admin(db)
    agent, _ = create_user(
        db, subject="phone-agent-2", role_code="agent", candidate_status="active"
    )
    rejected = client.post(
        "/api/v1/admin/agent-profiles",
        json=_agent_payload(str(agent.id), "519-123"),
        headers=ADMIN_HEADERS,
    )
    assert rejected.status_code == 422
    assert "10-digit" in rejected.text


def test_candidate_draft_accepts_a_normally_typed_number(client: TestClient, db: Session) -> None:
    from test_candidate_applications import candidate_headers, start_application

    started = start_application(client, db, subject="phone-candidate")
    saved = client.patch(
        f"/api/v1/candidate/applications/{started['id']}",
        json={"expected_revision": 1, "phone": "519-555-0164"},
        headers=candidate_headers("phone-candidate"),
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["phone"] == "+15195550164"


def test_candidate_draft_still_accepts_an_international_number(
    client: TestClient, db: Session
) -> None:
    from test_candidate_applications import candidate_headers, start_application

    started = start_application(client, db, subject="phone-candidate-intl")
    saved = client.patch(
        f"/api/v1/candidate/applications/{started['id']}",
        json={"expected_revision": 1, "phone": "+44 20 7946 0958"},
        headers=candidate_headers("phone-candidate-intl"),
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["phone"] == "+442079460958"


def test_candidate_draft_refuses_an_unusable_number(client: TestClient, db: Session) -> None:
    from test_candidate_applications import candidate_headers, start_application

    started = start_application(client, db, subject="phone-candidate-bad")
    rejected = client.patch(
        f"/api/v1/candidate/applications/{started['id']}",
        json={"expected_revision": 1, "phone": "519-555"},
        headers=candidate_headers("phone-candidate-bad"),
    )
    assert rejected.status_code == 422
    assert "10-digit" in rejected.text
