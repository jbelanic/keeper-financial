from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import (
    CandidateStatusHistory,
    ControlledDocument,
    DocumentVersion,
    OnboardingPlan,
    OnboardingTask,
)
from keeper_api.models.statuses import CandidateStatus

ADMIN_HEADERS = {"X-Dev-Auth-Sub": "review-admin", "X-Dev-Auth-AAL": "aal2"}


def create_admin(db: Session) -> None:
    create_user(db, subject="review-admin", role_code="brokerage_admin")


def make_candidate(
    db: Session, status: str, *, with_application: bool = True
) -> tuple[uuid.UUID, str]:
    subject = f"cand-{uuid.uuid4().hex[:8]}"
    _, candidate = create_user(db, subject=subject, role_code="candidate", candidate_status=status)
    assert candidate is not None
    return candidate.id, subject


# --------------------------------------------------------------------------- #
# REV-001 admin candidate queue
# --------------------------------------------------------------------------- #


def test_review_queue_requires_admin(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.APPLICATION_SUBMITTED.value)
    anon = client.get("/api/v1/admin/candidates")
    assert anon.status_code == 401
    ok = client.get("/api/v1/admin/candidates", headers=ADMIN_HEADERS)
    assert ok.status_code == 200
    assert ok.headers.get("Cache-Control") == "no-store"
    ids = [item["candidate_id"] for item in ok.json()["items"]]
    assert str(cid) in ids


def test_review_queue_excludes_terminal_states(client: TestClient, db: Session) -> None:
    create_admin(db)
    make_candidate(db, CandidateStatus.DECLINED.value)
    make_candidate(db, CandidateStatus.APPLICATION_SUBMITTED.value)
    ok = client.get("/api/v1/admin/candidates", headers=ADMIN_HEADERS).json()
    statuses = {item["status"] for item in ok["items"]}
    assert "declined" not in statuses
    assert "application_submitted" in statuses


# --------------------------------------------------------------------------- #
# REV-002 information requests
# --------------------------------------------------------------------------- #


def test_information_request_requires_reason_free_message(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW.value)
    resp = client.post(
        f"/api/v1/admin/candidates/{cid}/information-requests",
        json={"message": "Please upload your licensing certificate."},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "open"


# --------------------------------------------------------------------------- #
# REV-003 interview status
# --------------------------------------------------------------------------- #


def test_interview_status_recorded(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.INTERVIEW.value)
    resp = client.post(
        f"/api/v1/admin/candidates/{cid}/interview",
        json={"interview_status": "scheduled", "notes": "Panel on Tuesday"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["interview_status"] == "scheduled"
    assert resp.json()["interview_notes"] == "Panel on Tuesday"


# --------------------------------------------------------------------------- #
# REV-004 / REV-005 decisions (with reason + history)
# --------------------------------------------------------------------------- #


def test_decline_requires_reason(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED.value)
    no_reason = client.post(
        f"/api/v1/admin/candidates/{cid}/decision",
        json={"decision": "declined", "reason": None},
        headers=ADMIN_HEADERS,
    )
    assert no_reason.status_code == 409
    with_reason = client.post(
        f"/api/v1/admin/candidates/{cid}/decision",
        json={"decision": "declined", "reason": "Does not meet FSRA eligibility."},
        headers=ADMIN_HEADERS,
    )
    assert with_reason.status_code == 200
    assert with_reason.json()["status"] == "declined"


def test_withdrawal_records_history(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW.value)
    resp = client.post(
        f"/api/v1/admin/candidates/{cid}/decision",
        json={"decision": "withdrawn", "reason": "Candidate withdrew voluntarily."},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "withdrawn"
    history = (
        db.execute(select(CandidateStatusHistory).where(CandidateStatusHistory.candidate_id == cid))
        .scalars()
        .all()
    )
    assert any(h.new_status == "withdrawn" and h.reason for h in history)


# --------------------------------------------------------------------------- #
# REV-006 invalid transition rejection
# --------------------------------------------------------------------------- #


def test_invalid_transition_rejected(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW.value)
    resp = client.post(
        f"/api/v1/admin/candidates/{cid}/decision",
        json={"decision": "onboarding_in_progress", "reason": None},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 409


# --------------------------------------------------------------------------- #
# docs/00 §7 authorization — B1 lifecycle-denial pattern
# --------------------------------------------------------------------------- #


def test_suspended_candidate_detail_denied(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.SUSPENDED.value)
    resp = client.get(f"/api/v1/admin/candidates/{cid}", headers=ADMIN_HEADERS)
    assert resp.status_code == 403


def test_suspended_candidate_excluded_from_queue(client: TestClient, db: Session) -> None:
    create_admin(db)
    make_candidate(db, CandidateStatus.SUSPENDED.value)
    ok = client.get("/api/v1/admin/candidates", headers=ADMIN_HEADERS).json()
    assert ok["total"] == 0


# --------------------------------------------------------------------------- #
# ONB-001 plan + task templates
# --------------------------------------------------------------------------- #


def test_create_onboarding_plan(client: TestClient, db: Session) -> None:
    create_admin(db)
    resp = client.post(
        "/api/v1/admin/onboarding/plans",
        json={
            "name": "Standard Broker Onboarding",
            "description": "Baseline tasks for new brokers.",
            "tasks": [
                {
                    "title": "Complete compliance training",
                    "instructions": "Finish module 1",
                    "is_required": True,
                },
                {"title": "Upload licence", "instructions": "", "is_required": True},
            ],
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Standard Broker Onboarding"
    assert len(body["tasks"]) == 2
    assert body["tasks"][0]["sequence"] == 1


# --------------------------------------------------------------------------- #
# ONB-002 assignment + ONB-003 task lifecycle
# --------------------------------------------------------------------------- #


def test_assign_and_review_task(client: TestClient, db: Session) -> None:
    create_admin(db)
    plan = OnboardingPlan(name="Plan", description="d", is_active=True)
    db.add(plan)
    db.flush()
    task = OnboardingTask(plan_id=plan.id, title="T", instructions="", sequence=1, is_required=True)
    db.add(task)
    db.commit()
    cid, subject = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED.value)
    assign = client.post(
        f"/api/v1/admin/candidates/{cid}/assign-onboarding?plan_id={plan.id}",
        headers=ADMIN_HEADERS,
    )
    assert assign.status_code == 201
    # candidate dashboard should now expose the assigned task
    dash = client.get(
        "/api/v1/candidate/onboarding",
        headers={"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal2"},
    )
    assert dash.status_code == 200
    assert len(dash.json()["tasks"]) == 1


# --------------------------------------------------------------------------- #
# ONB-006 policy acknowledgement (candidate-only)
# --------------------------------------------------------------------------- #


def test_policy_acknowledgement(client: TestClient, db: Session) -> None:
    create_admin(db)
    doc = ControlledDocument(
        key="code-of-conduct",
        title="Code of Conduct",
        description="d",
        requires_acknowledgement=True,
    )
    db.add(doc)
    db.flush()
    version = DocumentVersion(
        controlled_document_id=doc.id,
        version_label="1.0",
        object_key=f"docs/{uuid.uuid4().hex}.pdf",
        sha256_digest="0" * 64,
        content_type="application/pdf",
        size_bytes=10,
        issued_at=datetime.now(UTC),
    )
    db.add(version)
    db.commit()
    cid, subject = make_candidate(db, CandidateStatus.ONBOARDING_IN_PROGRESS.value)
    headers = {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal2"}
    resp = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(version.id),
            "wording": "I have read and accept the Code of Conduct.",
        },
        headers=headers,
    )
    assert resp.status_code == 200


# --------------------------------------------------------------------------- #
# ONB-008 external e-sign envelope link (no embedded signature)
# --------------------------------------------------------------------------- #


def test_link_esign_envelope(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.ONBOARDING_IN_PROGRESS.value)
    resp = client.post(
        f"/api/v1/admin/onboarding/candidates/{cid}/esign-envelopes",
        json={
            "envelope_url": "https://esign.example.test/envelopes/abc",
            "envelope_id": "env-abc",
            "status": "sent",
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "sent"


# --------------------------------------------------------------------------- #
# ONB-009 activation gates
# --------------------------------------------------------------------------- #


def test_satisfy_activation_gate(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.ONBOARDING_IN_PROGRESS.value)
    resp = client.post(
        f"/api/v1/admin/onboarding/candidates/{cid}/gates",
        json={"code": "background_check"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "satisfied"


def test_unknown_gate_rejected(client: TestClient, db: Session) -> None:
    create_admin(db)
    cid, _ = make_candidate(db, CandidateStatus.ONBOARDING_IN_PROGRESS.value)
    resp = client.post(
        f"/api/v1/admin/onboarding/candidates/{cid}/gates",
        json={"code": "not_a_real_gate"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 409
