from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import (
    AuditEvent,
    Candidate,
    CandidateApplication,
    CandidateStatusHistory,
    RecruitmentPosting,
    Role,
    User,
    UserIdentity,
    UserRole,
)

PRIVACY_VERSION = "candidate-privacy-disclosure-2026-07-15-v1"
PRIVACY_PARAGRAPHS = [
    "Keeper Financial Inc. collects candidate information to create and administer your account, receive and review applications for the opportunities you select, communicate with you about those applications, protect the portal, maintain application and access records, and operate the recruitment process.",
    "We collect your verified account email and authentication/security metadata; the contact details you provide; the posting and application details you select; your availability, referral source, candidate statements, employment history, and education or training entries; any résumé or cover letter you choose to upload and its file metadata; privacy acknowledgements; and application status, candidate-visible communications, history, and audit records. Phase 1C does not ask you for government identity documents or numbers, background-check information, licence information, or financial information.",
    "You can access your own candidate record. Within Keeper Financial, access is limited to authorized brokerage administrators and recruitment reviewers who need the information for the recruitment process, security, support, or records administration. Internal notes are not shown to candidates. Service providers that host or support identity, application, database, private file-storage, security, monitoring, or communications functions may process information only to provide those services under Keeper Financial\u2019s direction and applicable safeguards. Candidate information is not provided to service providers for their own independent marketing.",
    "Candidate drafts, submitted applications, uploaded documents, acknowledgement records, and security/audit records are retained under Keeper Financial\u2019s approved, policy-controlled retention categories for only as long as reasonably needed for recruitment, records administration, security, dispute handling, and applicable obligations. Retention may differ for abandoned drafts, withdrawn or declined applications, active applications, documents, and security or audit records. Records are deleted or de-identified when the applicable approved policy permits, subject to a documented legal or security hold. This notice does not promise an unsupported fixed legal retention period.",
    "Required fields are needed to identify and contact you within this recruitment process, associate the application with the selected opportunity, review the application, and record that this disclosure was shown. If you omit required information or do not acknowledge this disclosure, you may save a draft but cannot submit the application. Optional answers and optional documents may be omitted without preventing submission, although reviewers will not have information you choose not to provide.",
    "For privacy questions or requests, contact support@keeperfinancial.ca. Do not email sensitive documents; use the authenticated portal for permitted uploads.",
]


def published_posting(
    db: Session, slug: str = "synthetic-candidate-opportunity"
) -> RecruitmentPosting:
    posting = RecruitmentPosting(
        slug=slug,
        title=f"Synthetic candidate opportunity {slug}",
        summary="An explicitly synthetic published fixture for candidate workflow tests.",
        body="This is not a real job posting.",
        status="published",
        version=3,
        published_at=datetime.now(UTC),
    )
    db.add(posting)
    db.commit()
    return posting


def start_headers(
    subject: str = "new-candidate",
    email: str = "new-candidate@example.test",
    *,
    verified: bool = True,
) -> dict[str, str]:
    return {
        "X-Dev-Auth-Sub": subject,
        "X-Dev-Auth-Email": email,
        "X-Dev-Auth-Verified": "true" if verified else "false",
    }


def candidate_headers(subject: str = "new-candidate", aal: str = "aal1") -> dict[str, str]:
    return {
        "Authorization": "Bearer local-dev-test-token",
        "X-Dev-Auth-Sub": subject,
        "X-Dev-Auth-AAL": aal,
    }


def start_application(
    client: TestClient,
    db: Session,
    *,
    subject: str = "new-candidate",
    email: str = "new-candidate@example.test",
    slug: str = "synthetic-candidate-opportunity",
) -> dict[str, object]:
    if db.query(RecruitmentPosting).filter_by(slug=slug).one_or_none() is None:
        published_posting(db, slug)
    response = client.post(
        f"/api/v1/recruitment/postings/{slug}/applications/start",
        headers=start_headers(subject, email),
    )
    assert response.status_code == 201
    return response.json()


def complete_draft(revision: int = 1) -> dict[str, object]:
    return {
        "expected_revision": revision,
        "given_name": "Synthetic",
        "family_name": "Candidate",
        "preferred_name": "Synth",
        "phone": "+1 (416) 555-0100",
        "city": "London",
        "region": "Ontario",
        "country_code": "CA",
        "preferred_contact_method": "email",
        "available_from": "2026-08-01",
        "referral_source": "other",
        "referral_detail": "Synthetic automated test",
        "interest_statement": "I am interested in this explicitly synthetic opportunity. " * 3,
        "relevant_experience": "General synthetic recruitment experience only.",
        "employment": [
            {
                "employer_name": "Synthetic Organization",
                "role_title": "Test Role",
                "start_month": "2024-01",
                "currently_employed": True,
                "summary": "Synthetic responsibilities.",
            }
        ],
        "education": [
            {
                "institution_name": "Synthetic Institute",
                "program_name": "Testing",
                "completion_year": 2025,
            }
        ],
        "privacy_acknowledged": True,
        "information_accuracy_confirmed": True,
    }


def test_candidate_privacy_disclosure_is_exact_server_owned_and_protected(
    client: TestClient, db: Session
) -> None:
    assert client.get("/api/v1/candidate/privacy-disclosure").status_code == 401
    start_application(client, db)
    response = client.get("/api/v1/candidate/privacy-disclosure", headers=candidate_headers())
    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.json() == {
        "title": "Candidate privacy disclosure",
        "version": PRIVACY_VERSION,
        "paragraphs": PRIVACY_PARAGRAPHS,
    }


def test_application_start_requires_verified_identity_and_published_posting(
    client: TestClient, db: Session
) -> None:
    published_posting(db)
    assert (
        client.post(
            "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start"
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
            headers=start_headers(verified=False),
        ).status_code
        == 403
    )
    draft = published_posting(db, "synthetic-draft")
    draft.status = "draft"
    db.commit()
    unavailable = client.post(
        "/api/v1/recruitment/postings/synthetic-draft/applications/start",
        headers=start_headers(),
    )
    assert unavailable.status_code == 404
    invalid_email = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers(email="not-an-email"),
    )
    assert invalid_email.status_code == 403


def test_application_start_atomically_provisions_only_candidate_relationships_and_is_idempotent(
    client: TestClient, db: Session
) -> None:
    published_posting(db)
    first = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers={**start_headers(), "X-Request-ID": "application-start"},
    )
    assert first.status_code == 201
    retry = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers(),
    )
    assert retry.status_code == 200
    assert retry.json()["id"] == first.json()["id"]

    user = db.query(User).filter_by(email="new-candidate@example.test").one()
    identity = db.query(UserIdentity).filter_by(user_id=user.id).one()
    candidate = db.query(Candidate).filter_by(user_id=user.id).one()
    application = db.query(CandidateApplication).one()
    roles = {
        role.code
        for role in db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
    }
    assert identity.provider_subject == "new-candidate"
    assert roles == {"candidate"}
    assert candidate.id == application.candidate_id
    assert application.source_posting_slug == "synthetic-candidate-opportunity"
    assert application.source_posting_version == 3
    assert [event.event_type for event in db.query(AuditEvent).order_by(AuditEvent.created_at)] == [
        "user_identity.linked",
        "role.granted",
        "candidate_application.started",
    ]


def test_application_start_retry_returns_the_existing_draft_without_resetting_content(
    client: TestClient, db: Session
) -> None:
    started = start_application(client, db)
    saved = client.patch(
        f"/api/v1/candidate/applications/{started['id']}",
        json={
            "expected_revision": 1,
            "given_name": "Preserved",
            "employment": [
                {
                    "employer_name": "Synthetic employer",
                    "role_title": "Synthetic role",
                    "start_month": "2025-01",
                    "currently_employed": True,
                }
            ],
        },
        headers=candidate_headers(),
    )
    assert saved.status_code == 200
    assert saved.headers["Cache-Control"] == "private, no-store"
    retry = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers(),
    )
    assert retry.status_code == 200
    assert retry.headers["Cache-Control"] == "private, no-store"
    assert retry.json()["id"] == started["id"]
    assert retry.json()["revision"] == 2
    assert retry.json()["given_name"] == "Preserved"
    assert retry.json()["employment"][0]["employer_name"] == "Synthetic employer"


def test_withdrawn_candidate_reapplies_as_a_distinct_attempt_without_overwrite(
    client: TestClient, db: Session
) -> None:
    first = start_application(client, db)
    withdrawn = client.post(
        f"/api/v1/candidate/applications/{first['id']}/withdraw",
        json={"expected_revision": 1},
        headers=candidate_headers(),
    )
    assert withdrawn.status_code == 200
    second = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers(),
    )
    assert second.status_code == 201
    assert second.json()["id"] != first["id"]
    attempts = db.query(CandidateApplication).order_by(CandidateApplication.attempt_number).all()
    assert [(item.attempt_number, item.state) for item in attempts] == [
        (1, "withdrawn"),
        (2, "draft"),
    ]


def test_application_start_rejects_subject_email_and_role_conflicts(
    client: TestClient, db: Session
) -> None:
    published_posting(db)
    create_user(db, subject="existing-subject")
    subject_conflict = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers("existing-subject", "different@example.test"),
    )
    assert subject_conflict.status_code == 409

    create_user(db, subject="email-owner")
    email_conflict = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers("different-subject", "email-owner@example.test"),
    )
    assert email_conflict.status_code == 409

    create_user(db, subject="admin-start", role_code="brokerage_admin")
    wrong_role = client.post(
        "/api/v1/recruitment/postings/synthetic-candidate-opportunity/applications/start",
        headers=start_headers("admin-start", "admin-start@example.test"),
    )
    assert wrong_role.status_code == 403
    assert db.query(CandidateApplication).count() == 0


def test_candidate_can_save_and_read_only_their_typed_draft(
    client: TestClient, db: Session
) -> None:
    started = start_application(client, db)
    application_id = started["id"]
    saved = client.patch(
        f"/api/v1/candidate/applications/{application_id}",
        json=complete_draft(),
        headers=candidate_headers(),
    )
    assert saved.status_code == 200
    assert saved.json()["revision"] == 2
    assert saved.json()["email"] == "new-candidate@example.test"
    assert saved.json()["employment"][0]["currently_employed"] is True
    assert saved.json()["privacy_disclosure_version"] is None
    assert "reason" not in saved.json()
    assert "internal_notes" not in saved.json()

    read = client.get(
        f"/api/v1/candidate/applications/{application_id}", headers=candidate_headers()
    )
    assert read.status_code == 200
    assert read.json() == saved.json()

    start_application(
        client,
        db,
        subject="other-candidate",
        email="other-candidate@example.test",
        slug="synthetic-other-opportunity",
    )
    cross = client.get(
        f"/api/v1/candidate/applications/{application_id}",
        headers=candidate_headers("other-candidate"),
    )
    assert cross.status_code == 404


@pytest.mark.parametrize(
    "override",
    [
        {"recruitment_posting_id": str(uuid.uuid4())},
        {"email": "caller@example.test"},
        {"privacy_disclosure_version": "caller-version"},
        {"state": "submitted"},
        {"revision": 99},
        {"internal_notes": "must never exist"},
    ],
)
def test_candidate_cannot_override_server_owned_application_fields(
    client: TestClient, db: Session, override: dict[str, object]
) -> None:
    application_id = start_application(client, db)["id"]
    payload = {"expected_revision": 1, **override}
    response = client.patch(
        f"/api/v1/candidate/applications/{application_id}",
        json=payload,
        headers=candidate_headers(),
    )
    assert response.status_code == 422


def test_submission_is_server_validated_transactional_idempotent_and_immutable(
    client: TestClient, db: Session
) -> None:
    application_id = start_application(client, db)["id"]
    incomplete = client.post(
        f"/api/v1/candidate/applications/{application_id}/submit",
        json={"expected_revision": 1},
        headers=candidate_headers(),
    )
    assert incomplete.status_code == 422

    saved = client.patch(
        f"/api/v1/candidate/applications/{application_id}",
        json=complete_draft(),
        headers=candidate_headers(),
    )
    assert saved.status_code == 200
    submitted = client.post(
        f"/api/v1/candidate/applications/{application_id}/submit",
        json={"expected_revision": 2},
        headers={**candidate_headers(), "X-Request-ID": "application-submit"},
    )
    assert submitted.status_code == 200
    assert submitted.json()["state"] == "submitted"
    assert submitted.json()["status"] == "application_submitted"
    assert submitted.json()["privacy_disclosure_version"] == PRIVACY_VERSION
    assert submitted.json()["privacy_acknowledged_at"] is not None
    repeated = client.post(
        f"/api/v1/candidate/applications/{application_id}/submit",
        json={"expected_revision": 2},
        headers=candidate_headers(),
    )
    assert repeated.status_code == 200
    assert repeated.json()["revision"] == submitted.json()["revision"]
    assert db.query(CandidateStatusHistory).count() == 1
    assert db.query(AuditEvent).filter_by(event_type="candidate_application.submitted").count() == 1

    edit = client.patch(
        f"/api/v1/candidate/applications/{application_id}",
        json={"expected_revision": submitted.json()["revision"], "city": "Toronto"},
        headers=candidate_headers(),
    )
    assert edit.status_code == 409


def test_posting_provenance_remains_immutable_after_posting_changes(
    client: TestClient, db: Session
) -> None:
    started = start_application(client, db)
    posting = db.query(RecruitmentPosting).filter_by(slug="synthetic-candidate-opportunity").one()
    posting.slug = "changed-after-start"
    posting.title = "Changed after application start"
    posting.version = 4
    posting.status = "closed"
    db.commit()
    application = client.get(
        f"/api/v1/candidate/applications/{started['id']}", headers=candidate_headers()
    ).json()
    assert application["source_posting_slug"] == "synthetic-candidate-opportunity"
    assert application["source_posting_title"].startswith("Synthetic candidate opportunity")
    assert application["source_posting_version"] == 3


def test_candidate_status_is_minimal_and_withdrawal_is_application_specific(
    client: TestClient, db: Session
) -> None:
    first = start_application(client, db)
    second = start_application(client, db, slug="synthetic-second-opportunity")
    saved = client.patch(
        f"/api/v1/candidate/applications/{first['id']}",
        json=complete_draft(),
        headers=candidate_headers(),
    )
    client.post(
        f"/api/v1/candidate/applications/{first['id']}/submit",
        json={"expected_revision": saved.json()["revision"]},
        headers=candidate_headers(),
    )
    withdrawn = client.post(
        f"/api/v1/candidate/applications/{first['id']}/withdraw",
        json={"expected_revision": 3},
        headers={**candidate_headers(), "X-Request-ID": "application-withdraw"},
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["state"] == "withdrawn"
    assert withdrawn.json()["status"] == "withdrawn"
    repeated = client.post(
        f"/api/v1/candidate/applications/{first['id']}/withdraw",
        json={"expected_revision": 3},
        headers=candidate_headers(),
    )
    assert repeated.status_code == 200
    assert db.query(AuditEvent).filter_by(event_type="candidate_application.withdrawn").count() == 1

    statuses = client.get("/api/v1/candidate/applications/status", headers=candidate_headers())
    assert statuses.status_code == 200
    assert set(statuses.json()) == {"applications"}
    status_by_application = {
        item["application_id"]: {"status": item["status"], "messages": item["messages"]}
        for item in statuses.json()["applications"]
    }
    assert status_by_application == {
        first["id"]: {"status": "withdrawn", "messages": []},
        second["id"]: {"status": "application_started", "messages": []},
    }
    assert "reason" not in statuses.text
    assert "actor" not in statuses.text

    edit = client.patch(
        f"/api/v1/candidate/applications/{first['id']}",
        json={"expected_revision": withdrawn.json()["revision"], "city": "Ottawa"},
        headers=candidate_headers(),
    )
    assert edit.status_code == 409

    clean_read = client.get(
        f"/api/v1/candidate/applications/{first['id']}", headers=candidate_headers()
    )
    assert clean_read.status_code == 200
    assert db.get(CandidateApplication, uuid.UUID(second["id"])).status == "application_started"
