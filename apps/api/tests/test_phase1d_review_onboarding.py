from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import (
    AuditEvent,
    Candidate,
    CandidateApplication,
    CandidateOnboardingAssignment,
    CandidateOnboardingTask,
    CandidateStatusHistory,
    ControlledDocument,
    DocumentVersion,
    OnboardingPlan,
    OnboardingTask,
    PolicyAcknowledgement,
    RecruitmentPosting,
)
from keeper_api.models.statuses import CandidateStatus

ADMIN_HEADERS = {"X-Dev-Auth-Sub": "review-admin", "X-Dev-Auth-AAL": "aal2"}


def create_admin(db: Session) -> None:
    create_user(db, subject="review-admin", role_code="brokerage_admin")


def add_application(
    db: Session,
    candidate: Candidate,
    status: CandidateStatus,
    *,
    attempt: int = 1,
    posting: RecruitmentPosting | None = None,
) -> CandidateApplication:
    if posting is None:
        posting = RecruitmentPosting(
            slug=f"synthetic-{uuid.uuid4().hex[:12]}",
            title="SYNTHETIC application-specific opportunity",
            summary="Synthetic test fixture.",
            body="Not a real recruitment posting.",
            status="published",
            version=1,
        )
        db.add(posting)
        db.flush()
    application = CandidateApplication(
        candidate_id=candidate.id,
        recruitment_posting_id=posting.id,
        attempt_number=attempt,
        source_posting_slug=posting.slug,
        source_posting_title=posting.title,
        source_posting_version=posting.version,
        schema_version="candidate-application-2026-07-15-v1",
        revision=2,
        state="submitted",
        status=status.value,
        email=f"candidate-{candidate.id}@example.test",
        given_name="Synthetic",
        family_name="Candidate",
        submitted_at=datetime.now(UTC),
    )
    db.add(application)
    db.commit()
    return application


def make_candidate(
    db: Session, status: CandidateStatus
) -> tuple[Candidate, CandidateApplication, str]:
    subject = f"cand-{uuid.uuid4().hex[:10]}"
    _, candidate = create_user(
        db,
        subject=subject,
        role_code="candidate",
        candidate_status=CandidateStatus.APPLICATION_SUBMITTED.value,
    )
    assert candidate is not None
    return candidate, add_application(db, candidate, status), subject


def make_plan(db: Session, *, active: bool = True, with_task: bool = True) -> OnboardingPlan:
    plan = OnboardingPlan(name=f"Plan {uuid.uuid4().hex[:6]}", description="d", is_active=active)
    db.add(plan)
    db.flush()
    if with_task:
        db.add(
            OnboardingTask(
                plan_id=plan.id,
                title="Complete synthetic task",
                instructions="Synthetic evidence only.",
                sequence=1,
                is_required=True,
            )
        )
    db.commit()
    return plan


def make_document(db: Session, *, label: str = "1.0") -> DocumentVersion:
    document = ControlledDocument(
        key=f"synthetic-policy-{uuid.uuid4().hex[:8]}",
        title="Synthetic assigned policy",
        description="Test-only controlled document.",
        requires_acknowledgement=True,
    )
    db.add(document)
    db.flush()
    version = DocumentVersion(
        controlled_document_id=document.id,
        version_label=label,
        object_key=f"docs/{uuid.uuid4().hex}.pdf",
        sha256_digest="0" * 64,
        content_type="application/pdf",
        size_bytes=10,
        issued_at=datetime.now(UTC),
    )
    db.add(version)
    db.commit()
    return version


def assign(
    client: TestClient,
    candidate: Candidate,
    application: CandidateApplication,
    plan: OnboardingPlan,
):
    return client.post(
        f"/api/v1/admin/candidates/{candidate.id}/assign-onboarding"
        f"?plan_id={plan.id}&application_id={application.id}",
        headers=ADMIN_HEADERS,
    )


def test_review_queue_is_admin_only_and_application_specific(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, first, _ = make_candidate(db, CandidateStatus.APPLICATION_SUBMITTED)
    second = add_application(db, candidate, CandidateStatus.UNDER_REVIEW)
    assert client.get("/api/v1/admin/candidates").status_code == 401

    response = client.get("/api/v1/admin/candidates", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    rows = response.json()["items"]
    assert {row["application_id"] for row in rows} == {str(first.id), str(second.id)}
    assert all(row["candidate_id"] == str(candidate.id) for row in rows)


def test_review_transition_changes_only_selected_application_and_preserves_history(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, selected, _ = make_candidate(db, CandidateStatus.APPLICATION_SUBMITTED)
    other = add_application(db, candidate, CandidateStatus.UNDER_REVIEW)

    response = client.post(
        f"/api/v1/admin/candidates/{candidate.id}/decision",
        json={
            "application_id": str(selected.id),
            "decision": "under_review",
            "reason": None,
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    db.refresh(selected)
    db.refresh(other)
    assert selected.status == "under_review"
    assert other.status == "under_review"
    history = db.scalars(
        select(CandidateStatusHistory).where(CandidateStatusHistory.application_id == selected.id)
    ).all()
    assert [(item.previous_status, item.new_status) for item in history] == [
        ("application_submitted", "under_review")
    ]
    assert not db.scalars(
        select(CandidateStatusHistory).where(CandidateStatusHistory.application_id == other.id)
    ).all()


def test_invalid_or_cross_application_transition_is_rejected(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    first_candidate, application, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW)
    second_candidate, second_application, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW)
    invalid = client.post(
        f"/api/v1/admin/candidates/{first_candidate.id}/decision",
        json={
            "application_id": str(application.id),
            "decision": "onboarding_in_progress",
            "reason": None,
        },
        headers=ADMIN_HEADERS,
    )
    cross = client.post(
        f"/api/v1/admin/candidates/{first_candidate.id}/decision",
        json={
            "application_id": str(second_application.id),
            "decision": "conditionally_selected",
            "reason": None,
        },
        headers=ADMIN_HEADERS,
    )
    assert invalid.status_code == 409
    assert cross.status_code == 404
    assert second_candidate.id != first_candidate.id


def test_decline_requires_reason_and_records_safe_application_audit(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.INTERVIEW)
    payload = {"application_id": str(application.id), "decision": "declined", "reason": None}
    assert (
        client.post(
            f"/api/v1/admin/candidates/{candidate.id}/decision",
            json=payload,
            headers=ADMIN_HEADERS,
        ).status_code
        == 409
    )
    payload["reason"] = "Synthetic bounded review reason."
    response = client.post(
        f"/api/v1/admin/candidates/{candidate.id}/decision",
        json=payload,
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["application_id"] == str(application.id)
    audit = db.scalar(
        select(AuditEvent).where(
            AuditEvent.event_type == "candidate_application.status_changed",
            AuditEvent.target_id == application.id,
        )
    )
    assert audit is not None
    assert "reason" not in audit.safe_metadata


def test_interview_and_information_request_are_application_specific(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW)
    other_application = add_application(db, candidate, CandidateStatus.UNDER_REVIEW)
    interview = client.post(
        f"/api/v1/admin/candidates/{candidate.id}/interview",
        json={
            "application_id": str(application.id),
            "interview_status": "scheduled",
            "notes": "Synthetic panel schedule.",
        },
        headers=ADMIN_HEADERS,
    )
    assert interview.status_code == 200
    assert interview.json()["status"] == "interview"
    request = client.post(
        f"/api/v1/admin/candidates/{candidate.id}/information-requests",
        json={
            "application_id": str(application.id),
            "message": "Please provide the requested general recruitment response.",
        },
        headers=ADMIN_HEADERS,
    )
    assert request.status_code == 201
    assert request.json()["application_id"] == str(application.id)
    db.refresh(application)
    db.refresh(other_application)
    assert application.status == "more_information_required"
    assert other_application.status == "under_review"
    assert (
        db.scalar(
            select(CandidateStatusHistory).where(
                CandidateStatusHistory.application_id == application.id,
                CandidateStatusHistory.new_status == "more_information_required",
            )
        )
        is not None
    )
    assert (
        db.scalar(
            select(AuditEvent).where(
                AuditEvent.event_type == "candidate_application.information_requested",
                AuditEvent.target_id == application.id,
            )
        )
        is not None
    )


@pytest.mark.parametrize(
    "application_status, expected_status",
    [
        (CandidateStatus.UNDER_REVIEW, 201),
        (CandidateStatus.INTERVIEW, 201),
        (CandidateStatus.APPLICATION_SUBMITTED, 409),
        (CandidateStatus.MORE_INFORMATION_REQUIRED, 409),
        (CandidateStatus.CONDITIONALLY_SELECTED, 409),
        (CandidateStatus.DECLINED, 409),
        (CandidateStatus.WITHDRAWN, 409),
    ],
)
def test_information_request_lifecycle_is_bounded_and_operation_specific(
    client: TestClient,
    db: Session,
    application_status: CandidateStatus,
    expected_status: int,
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, application_status)
    response = client.post(
        f"/api/v1/admin/candidates/{candidate.id}/information-requests",
        json={
            "application_id": str(application.id),
            "message": "Please provide the requested synthetic clarification.",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == expected_status
    if expected_status == 409:
        assert response.json()["detail"] == (
            "information request is not available for the selected application status"
        )
        assert "interview status" not in response.text.lower()


def test_information_request_rejects_candidate_application_mismatch(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, _, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW)
    _, other_application, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW)
    response = client.post(
        f"/api/v1/admin/candidates/{candidate.id}/information-requests",
        json={
            "application_id": str(other_application.id),
            "message": "Please provide the requested synthetic clarification.",
        },
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404


def test_assignment_requires_selected_application_and_active_plan(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.UNDER_REVIEW)
    active_plan = make_plan(db)
    inactive_plan = make_plan(db, active=False)
    assert assign(client, candidate, application, active_plan).status_code == 409
    application.status = CandidateStatus.CONDITIONALLY_SELECTED.value
    db.commit()
    assert assign(client, candidate, application, inactive_plan).status_code == 409
    assert not db.scalars(select(CandidateOnboardingAssignment)).all()


def test_assignment_is_idempotent_and_preserves_other_application(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, subject = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    other = add_application(db, candidate, CandidateStatus.UNDER_REVIEW)
    plan = make_plan(db)
    first = assign(client, candidate, application, plan)
    second = assign(client, candidate, application, plan)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["assignment_id"] == second.json()["assignment_id"]
    assert db.query(CandidateOnboardingAssignment).count() == 1
    assert db.query(CandidateOnboardingTask).count() == 1
    db.refresh(application)
    db.refresh(other)
    assert application.status == "onboarding_in_progress"
    assert other.status == "under_review"
    dashboard = client.get(
        "/api/v1/candidate/onboarding",
        headers={"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"},
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["assignment"]["application_id"] == str(application.id)
    availability = client.get(
        "/api/v1/candidate/onboarding/availability",
        headers={"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"},
    )
    assert availability.status_code == 200
    assert availability.json() == {"available": True}


def test_failed_reassignment_does_not_supersede_valid_assignment(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    plan = make_plan(db)
    assert assign(client, candidate, application, plan).status_code == 201
    inactive = make_plan(db, active=False)
    failed = assign(client, candidate, application, inactive)
    assert failed.status_code == 409
    assignment = db.scalar(select(CandidateOnboardingAssignment))
    assert assignment is not None
    assert assignment.status == "active"
    assert assignment.onboarding_plan_id == plan.id


def test_dashboard_requires_current_application_bound_assignment(
    client: TestClient, db: Session
) -> None:
    _, _, subject = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    response = client.get(
        "/api/v1/candidate/onboarding",
        headers={"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"},
    )
    availability = client.get(
        "/api/v1/candidate/onboarding/availability",
        headers={"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"},
    )
    assert availability.status_code == 200
    assert availability.json() == {"available": False}
    assert response.status_code == 200
    assert response.json() == {
        "assignment": None,
        "tasks": [],
        "gates": [],
        "documents": [],
        "acknowledgements": [],
        "esign_envelopes": [],
        "activation_ready": False,
    }


def test_only_exact_assigned_eligible_version_can_be_acknowledged(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    assigned_version = make_document(db)
    candidate, application, subject = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    plan = make_plan(db, with_task=False)
    assert assign(client, candidate, application, plan).status_code == 201
    unassigned_version = make_document(db)
    headers = {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"}
    unassigned = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(unassigned_version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=headers,
    )
    assert unassigned.status_code == 409
    accepted = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(assigned_version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=headers,
    )
    retry = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(assigned_version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=headers,
    )
    assert accepted.status_code == 200
    assert retry.status_code == 200
    assert accepted.json()["id"] == retry.json()["id"]
    assert db.query(PolicyAcknowledgement).count() == 1


def test_later_assignment_generation_reuses_exact_prior_acknowledgement(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    version = make_document(db)
    candidate, first_application, subject = make_candidate(
        db, CandidateStatus.CONDITIONALLY_SELECTED
    )
    assert (
        assign(client, candidate, first_application, make_plan(db, with_task=False)).status_code
        == 201
    )
    headers = {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"}
    first_ack = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=headers,
    )
    assert first_ack.status_code == 200

    later_application = add_application(db, candidate, CandidateStatus.CONDITIONALLY_SELECTED)
    assert (
        assign(client, candidate, later_application, make_plan(db, with_task=False)).status_code
        == 201
    )
    reused = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=headers,
    )
    assert reused.status_code == 200
    assert reused.json()["id"] == first_ack.json()["id"]
    dashboard = client.get("/api/v1/candidate/onboarding", headers=headers).json()
    assert [item["id"] for item in dashboard["acknowledgements"]] == [first_ack.json()["id"]]
    assert db.query(PolicyAcknowledgement).count() == 1


def test_superseded_and_cross_candidate_assignment_versions_are_rejected(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    first_version = make_document(db)
    first_candidate, first_application, first_subject = make_candidate(
        db, CandidateStatus.CONDITIONALLY_SELECTED
    )
    assert (
        assign(
            client, first_candidate, first_application, make_plan(db, with_task=False)
        ).status_code
        == 201
    )
    first_version.superseded_at = datetime.now(UTC)
    db.commit()
    for code in (
        "background_check",
        "fsra_authorization",
        "system_provisioning",
        "policy_acknowledgement",
        "executed_agreements",
    ):
        assert (
            client.post(
                f"/api/v1/admin/onboarding/candidates/{first_candidate.id}/gates",
                json={"code": code},
                headers=ADMIN_HEADERS,
            ).status_code
            == 200
        )
    first_dashboard = client.get(
        "/api/v1/candidate/onboarding",
        headers={"X-Dev-Auth-Sub": first_subject, "X-Dev-Auth-AAL": "aal1"},
    )
    assert first_dashboard.json()["activation_ready"] is False
    second_candidate, second_application, second_subject = make_candidate(
        db, CandidateStatus.CONDITIONALLY_SELECTED
    )
    assert assign(client, second_candidate, second_application, make_plan(db)).status_code == 201
    response = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(first_version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers={"X-Dev-Auth-Sub": second_subject, "X-Dev-Auth-AAL": "aal1"},
    )
    assert response.status_code == 409


def test_activation_ready_requires_assignment_tasks_policies_and_all_gates(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    version = make_document(db)
    candidate, application, subject = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assert assign(client, candidate, application, make_plan(db)).status_code == 201
    candidate_headers = {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": "aal1"}
    assert (
        client.get("/api/v1/candidate/onboarding", headers=candidate_headers).json()[
            "activation_ready"
        ]
        is False
    )
    task = db.scalar(select(CandidateOnboardingTask))
    assert task is not None
    reviewed = client.post(
        f"/api/v1/admin/onboarding/candidates/{candidate.id}/tasks/{task.id}/review",
        json={"approved": True, "review_notes": "Synthetic completion."},
        headers=ADMIN_HEADERS,
    )
    assert reviewed.status_code == 200
    acknowledged = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=candidate_headers,
    )
    assert acknowledged.status_code == 200
    for code in (
        "background_check",
        "fsra_authorization",
        "system_provisioning",
        "policy_acknowledgement",
        "executed_agreements",
    ):
        assert (
            client.post(
                f"/api/v1/admin/onboarding/candidates/{candidate.id}/gates",
                json={"code": code},
                headers=ADMIN_HEADERS,
            ).status_code
            == 200
        )
    dashboard = client.get("/api/v1/candidate/onboarding", headers=candidate_headers).json()
    assert dashboard["activation_ready"] is True
    assert application.status == "onboarding_in_progress"
    assert (
        client.post(
            f"/api/v1/admin/onboarding/candidates/{candidate.id}/activate",
            headers=ADMIN_HEADERS,
        ).status_code
        == 404
    )
