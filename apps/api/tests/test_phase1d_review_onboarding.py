from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.api.routes import onboarding as onboarding_routes
from keeper_api.models.domain import (
    AuditEvent,
    Candidate,
    CandidateApplication,
    CandidateEsignEnvelope,
    CandidateOnboardingAssignment,
    CandidateOnboardingTask,
    CandidateStatusHistory,
    ControlledDocument,
    DocumentVersion,
    GateEvidenceEvent,
    OnboardingPlan,
    OnboardingTask,
    PolicyAcknowledgement,
    ProgrammaticGate,
    RecruitmentPosting,
    Role,
    User,
    UserRole,
)
from keeper_api.models.statuses import CandidateStatus
from keeper_api.services import documenso as documenso_service
from keeper_api.services import onboarding as onboarding_service
from keeper_api.services.documenso import DocumensoError, IssuedEnvelope

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


def test_admin_issues_configured_ica_to_assignment_linked_user(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    user = db.get(User, candidate.user_id)
    assert user is not None
    user.email = "authoritative@example.test"
    user.display_name = "Authoritative Candidate"
    db.commit()
    assignment_id = assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    observed: dict[str, str] = {}

    def fake_issue(_settings: object, **kwargs: str) -> IssuedEnvelope:
        observed.update(kwargs)
        return IssuedEnvelope(
            envelope_id="issued-envelope",
            status="PENDING",
            signing_url="https://sign.keeperfinancial.ca/sign/issued-envelope",
        )

    monkeypatch.setattr(documenso_service, "issue_ica_envelope", fake_issue)
    response = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 201
    assert observed == {
        "assignment_id": assignment_id,
        "candidate_email": "authoritative@example.test",
        "candidate_name": "Authoritative Candidate",
    }
    envelope = db.scalar(
        select(CandidateEsignEnvelope).where(
            CandidateEsignEnvelope.assignment_id == uuid.UUID(assignment_id)
        )
    )
    assert envelope is not None
    assert envelope.envelope_id == "issued-envelope"
    assert envelope.envelope_url == "https://sign.keeperfinancial.ca/sign/issued-envelope"
    assert envelope.status == "sent"
    assert envelope.last_synced_at is not None


def test_ica_issue_requires_admin_and_rejects_provider_failure_and_duplicate(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    candidate, application, candidate_subject = make_candidate(
        db, CandidateStatus.CONDITIONALLY_SELECTED
    )
    assignment_id = uuid.UUID(
        assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    )
    endpoint = f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica"
    assert client.post(endpoint).status_code == 401
    assert client.post(endpoint, headers={"X-Dev-Auth-Sub": candidate_subject}).status_code == 403

    def fail_issue(_settings: object, **_kwargs: str) -> IssuedEnvelope:
        raise DocumensoError("safe synthetic provider failure")

    monkeypatch.setattr(documenso_service, "issue_ica_envelope", fail_issue)
    assert client.post(endpoint, headers=ADMIN_HEADERS).status_code == 503
    assert (
        db.scalar(
            select(CandidateEsignEnvelope.id).where(
                CandidateEsignEnvelope.assignment_id == assignment_id
            )
        )
        is None
    )

    calls = 0

    def issue_once(_settings: object, **_kwargs: str) -> IssuedEnvelope:
        nonlocal calls
        calls += 1
        return IssuedEnvelope(
            envelope_id="issued-once",
            status="PENDING",
            signing_url="https://sign.keeperfinancial.ca/sign/issued-once",
        )

    monkeypatch.setattr(documenso_service, "issue_ica_envelope", issue_once)
    assert client.post(endpoint, headers=ADMIN_HEADERS).status_code == 201
    assert client.post(endpoint, headers=ADMIN_HEADERS).status_code == 409
    assert calls == 1
    assert (
        len(
            db.scalars(
                select(CandidateEsignEnvelope).where(
                    CandidateEsignEnvelope.assignment_id == assignment_id
                )
            ).all()
        )
        == 1
    )


def test_ica_issue_rejects_withdrawn_application_before_provider_call(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    application.state = "withdrawn"
    application.status = "withdrawn"
    db.commit()

    def unexpected_issue(*_args: object, **_kwargs: object) -> IssuedEnvelope:
        raise AssertionError("withdrawn application reached the Documenso adapter")

    monkeypatch.setattr(documenso_service, "issue_ica_envelope", unexpected_issue)
    response = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409
    assert (
        db.scalar(
            select(CandidateEsignEnvelope.id).where(
                CandidateEsignEnvelope.assignment_id == uuid.UUID(assignment_id)
            )
        )
        is None
    )


def test_rejected_keeper_issued_agreement_can_be_safely_reissued(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    provider_results = iter(
        [
            IssuedEnvelope(
                envelope_id="rejected-envelope",
                status="REJECTED",
                signing_url="https://sign.keeperfinancial.ca/sign/rejected-envelope",
            ),
            IssuedEnvelope(
                envelope_id="replacement-envelope",
                status="PENDING",
                signing_url="https://sign.keeperfinancial.ca/sign/replacement-envelope",
            ),
        ]
    )
    monkeypatch.setattr(
        documenso_service,
        "issue_ica_envelope",
        lambda *_args, **_kwargs: next(provider_results),
    )
    endpoint = f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica"

    rejected = client.post(endpoint, headers=ADMIN_HEADERS)
    replacement = client.post(endpoint, headers=ADMIN_HEADERS)

    assert rejected.status_code == 201
    assert replacement.status_code == 201
    predecessor = db.get(CandidateEsignEnvelope, uuid.UUID(rejected.json()["id"]))
    assert predecessor is not None
    assert predecessor.superseded_at is not None
    assert predecessor.replacement_envelope_id == uuid.UUID(replacement.json()["id"])
    assert replacement.json()["status"] == "sent"
    assert replacement.json()["superseded_at"] is None


def test_completion_requires_aal2_even_when_global_admin_mfa_is_disabled(
    client: TestClient, db: Session, settings
) -> None:
    create_admin(db)
    settings.require_admin_mfa = False
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db)).json()["assignment_id"]

    response = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/complete",
        headers={"X-Dev-Auth-Sub": "review-admin", "X-Dev-Auth-AAL": "aal1"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "administrator MFA is required"


def test_manual_recovery_envelope_cannot_satisfy_completion(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch, settings
) -> None:
    create_admin(db)
    if db.scalar(select(Role).where(Role.code == "agent")) is None:
        db.add(Role(code="agent", description="Synthetic existing agent role"))
        db.commit()
    settings.esign_provider = "documenso"
    settings.documenso_api_base_url = "https://sign.keeperfinancial.ca/api/v2"
    settings.documenso_public_base_url = "https://sign.keeperfinancial.ca"
    settings.documenso_api_token = "synthetic-token"
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db, with_task=False)).json()[
        "assignment_id"
    ]
    linked = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes",
        json={"provider_envelope_id": "manual-recovery-envelope"},
        headers=ADMIN_HEADERS,
    )
    assert linked.status_code == 201
    monkeypatch.setattr(
        "keeper_api.services.documenso.fetch_envelope_status",
        lambda *_args, **_kwargs: "COMPLETED",
    )
    refreshed = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{linked.json()['id']}/refresh",
        headers=ADMIN_HEADERS,
    )
    assert refreshed.status_code == 200
    for gate in db.scalars(
        select(ProgrammaticGate).where(ProgrammaticGate.assignment_id == uuid.UUID(assignment_id))
    ):
        gate.status = "satisfied"
        gate.satisfied_at = datetime.now(UTC)
    db.commit()

    response = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/complete",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "the current contractor agreement is not provider-confirmed"

    monkeypatch.setattr(
        documenso_service,
        "issue_ica_envelope",
        lambda *_args, **_kwargs: IssuedEnvelope(
            envelope_id="verified-envelope-after-recovery",
            status="PENDING",
            signing_url="https://sign.keeperfinancial.ca/sign/verified-envelope-after-recovery",
        ),
    )
    verified = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica",
        headers=ADMIN_HEADERS,
    )
    assert verified.status_code == 201
    recovery = db.get(CandidateEsignEnvelope, uuid.UUID(linked.json()["id"]))
    assert recovery is not None
    assert recovery.superseded_at is not None
    assert recovery.replacement_envelope_id == uuid.UUID(verified.json()["id"])


@pytest.mark.parametrize(
    ("application_state", "application_status", "candidate_status"),
    [
        ("withdrawn", "withdrawn", None),
        ("submitted", "onboarding_in_progress", "offboarding"),
    ],
)
def test_completion_rejects_stale_application_or_relationship_lifecycle(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
    application_state: str,
    application_status: str,
    candidate_status: str | None,
) -> None:
    create_admin(db)
    if db.scalar(select(Role).where(Role.code == "agent")) is None:
        db.add(Role(code="agent", description="Synthetic existing agent role"))
        db.commit()
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db, with_task=False)).json()[
        "assignment_id"
    ]
    monkeypatch.setattr(
        documenso_service,
        "issue_ica_envelope",
        lambda *_args, **_kwargs: IssuedEnvelope(
            envelope_id="lifecycle-envelope",
            status="COMPLETED",
            signing_url="https://sign.keeperfinancial.ca/sign/lifecycle-envelope",
        ),
    )
    issued = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica",
        headers=ADMIN_HEADERS,
    )
    assert issued.status_code == 201
    for gate in db.scalars(
        select(ProgrammaticGate).where(ProgrammaticGate.assignment_id == uuid.UUID(assignment_id))
    ):
        gate.status = "satisfied"
        gate.satisfied_at = datetime.now(UTC)
    application.state = application_state
    application.status = application_status
    if candidate_status is not None:
        candidate.status = candidate_status
    db.commit()

    response = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/complete",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409
    db.refresh(application)
    db.refresh(candidate)
    assert application.status == application_status
    if candidate_status is not None:
        assert candidate.status == candidate_status


def test_completion_requires_readiness_provider_evidence_and_active_assignment(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    if db.scalar(select(Role).where(Role.code == "agent")) is None:
        db.add(Role(code="agent", description="Synthetic existing agent role"))
        db.commit()
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = uuid.UUID(
        assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    )
    db.refresh(candidate)
    db.refresh(application)
    previous_candidate_status = candidate.status
    previous_application_status = application.status
    endpoint = f"/api/v1/admin/onboarding/assignments/{assignment_id}/complete"

    assert client.post(endpoint, headers=ADMIN_HEADERS).status_code == 409
    task = db.scalar(
        select(CandidateOnboardingTask).where(
            CandidateOnboardingTask.assignment_id == assignment_id
        )
    )
    assert task is not None
    task.status = "completed"
    for gate in db.scalars(
        select(ProgrammaticGate).where(ProgrammaticGate.assignment_id == assignment_id)
    ):
        gate.status = "satisfied"
        gate.satisfied_at = datetime.now(UTC)
    db.commit()
    assert client.post(endpoint, headers=ADMIN_HEADERS).status_code == 409

    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    assert assignment is not None
    assignment.status = "superseded"
    db.commit()
    assert client.post(endpoint, headers=ADMIN_HEADERS).status_code == 409
    db.refresh(candidate)
    db.refresh(application)
    assert candidate.status == previous_candidate_status
    assert application.status == previous_application_status
    agent_role = db.scalar(select(Role).where(Role.code == "agent"))
    assert agent_role is not None
    assert (
        db.scalar(
            select(UserRole.id).where(
                UserRole.user_id == candidate.user_id,
                UserRole.role_id == agent_role.id,
            )
        )
        is None
    )


def test_completion_rolls_back_all_transitions_on_failure(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    if db.scalar(select(Role).where(Role.code == "agent")) is None:
        db.add(Role(code="agent", description="Synthetic existing agent role"))
        db.commit()
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = uuid.UUID(
        assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    )
    db.refresh(candidate)
    db.refresh(application)
    previous_candidate_status = candidate.status
    previous_application_status = application.status
    task = db.scalar(
        select(CandidateOnboardingTask).where(
            CandidateOnboardingTask.assignment_id == assignment_id
        )
    )
    assert task is not None
    task.status = "completed"
    for gate in db.scalars(
        select(ProgrammaticGate).where(ProgrammaticGate.assignment_id == assignment_id)
    ):
        gate.status = "satisfied"
        gate.satisfied_at = datetime.now(UTC)
    db.add(
        CandidateEsignEnvelope(
            candidate_id=candidate.id,
            assignment_id=assignment_id,
            provider="documenso",
            envelope_id="rollback-envelope",
            envelope_url="https://sign.keeperfinancial.ca/sign/rollback-envelope",
            status="completed",
            last_synced_at=datetime.now(UTC),
        )
    )
    db.commit()

    def force_failure(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("synthetic forced rollback")

    monkeypatch.setattr(onboarding_service.AuditService, "record", force_failure)
    actor_user_id = db.scalar(select(User.id).where(User.email == "review-admin@example.test"))
    assert actor_user_id is not None
    with pytest.raises(RuntimeError, match="forced rollback"):
        onboarding_service.complete_onboarding_assignment(
            db,
            assignment_id=assignment_id,
            actor_user_id=actor_user_id,
            request_id="rollback-test",
        )
    db.rollback()
    db.expire_all()
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    candidate = db.get(Candidate, candidate.id)
    application = db.get(CandidateApplication, application.id)
    assert assignment is not None and assignment.status == "active"
    assert candidate is not None and candidate.status == previous_candidate_status
    assert application is not None and application.status == previous_application_status
    agent_role = db.scalar(select(Role).where(Role.code == "agent"))
    assert agent_role is not None
    assert (
        db.scalar(
            select(UserRole.id).where(
                UserRole.user_id == candidate.user_id,
                UserRole.role_id == agent_role.id,
            )
        )
        is None
    )
    assert not db.scalars(
        select(CandidateStatusHistory).where(
            CandidateStatusHistory.candidate_id == candidate.id,
            CandidateStatusHistory.new_status == "active",
        )
    ).all()


def test_admin_completion_atomically_activates_and_grants_agent_once(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    if db.scalar(select(Role).where(Role.code == "agent")) is None:
        db.add(Role(code="agent", description="Synthetic existing agent role"))
        db.commit()
    candidate, application, candidate_subject = make_candidate(
        db, CandidateStatus.CONDITIONALLY_SELECTED
    )
    assignment_id = uuid.UUID(
        assign(client, candidate, application, make_plan(db)).json()["assignment_id"]
    )
    task = db.scalar(
        select(CandidateOnboardingTask).where(
            CandidateOnboardingTask.assignment_id == assignment_id
        )
    )
    assert task is not None
    task.status = "completed"
    for gate in db.scalars(
        select(ProgrammaticGate).where(ProgrammaticGate.assignment_id == assignment_id)
    ):
        gate.status = "satisfied"
        gate.satisfied_at = datetime.now(UTC)
    db.add(
        CandidateEsignEnvelope(
            candidate_id=candidate.id,
            assignment_id=assignment_id,
            provider="documenso",
            envelope_id="completed-envelope",
            envelope_url="https://sign.keeperfinancial.ca/sign/completed-envelope",
            status="completed",
            last_synced_at=datetime.now(UTC),
        )
    )
    db.commit()

    first = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/complete",
        headers=ADMIN_HEADERS,
    )
    second = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/complete",
        headers=ADMIN_HEADERS,
    )

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert first.json()["status"] == "completed"
    db.refresh(candidate)
    db.refresh(application)
    assignment = db.get(CandidateOnboardingAssignment, assignment_id)
    assert assignment is not None and assignment.status == "completed"
    assert application.status == candidate.status == "active"
    role_codes = set(
        db.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == candidate.user_id)
        )
    )
    assert role_codes == {"candidate", "agent"}
    assert (
        db.scalar(
            select(AuditEvent).where(
                AuditEvent.event_type == "onboarding.completed",
                AuditEvent.target_id == assignment_id,
            )
        )
        is not None
    )
    eligible = client.get("/api/v1/admin/eligible-agents", headers=ADMIN_HEADERS)
    assert eligible.status_code == 200
    assert str(candidate.user_id) in {item["user_id"] for item in eligible.json()}
    candidate_headers = {"X-Dev-Auth-Sub": candidate_subject}
    assert client.get(
        "/api/v1/candidate/onboarding/availability", headers=candidate_headers
    ).json() == {"available": True}
    dashboard = client.get("/api/v1/candidate/onboarding", headers=candidate_headers).json()
    assert dashboard["assignment"]["status"] == "completed"
    assert dashboard["activation_ready"] is False
    assert dashboard["esign_envelopes"][0]["envelope_url"] is None


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


def test_unused_plan_is_editable_and_first_assignment_locks_it(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    plan = make_plan(db)
    update = client.patch(
        f"/api/v1/admin/onboarding/plans/{plan.id}",
        json={
            "name": "SYNTHETIC revised plan",
            "description": "Revised before first use.",
            "tasks": [
                {
                    "title": "Second task first",
                    "instructions": "Synthetic instructions.",
                    "is_required": True,
                },
                {
                    "title": "Optional follow-up",
                    "instructions": "Synthetic optional instructions.",
                    "is_required": False,
                },
            ],
        },
        headers=ADMIN_HEADERS,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "SYNTHETIC revised plan"
    assert update.json()["is_locked"] is False
    assert [task["title"] for task in update.json()["tasks"]] == [
        "Second task first",
        "Optional follow-up",
    ]

    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assert assign(client, candidate, application, plan).status_code == 201
    detail = client.get(f"/api/v1/admin/onboarding/plans/{plan.id}", headers=ADMIN_HEADERS)
    assert detail.status_code == 200
    assert detail.json()["is_locked"] is True
    listed = client.get("/api/v1/admin/onboarding/plans", headers=ADMIN_HEADERS)
    assert listed.status_code == 200
    assert next(item for item in listed.json() if item["id"] == str(plan.id))["is_locked"] is True
    locked = client.patch(
        f"/api/v1/admin/onboarding/plans/{plan.id}",
        json={
            "name": "Forbidden mutation",
            "description": "Must not persist.",
            "tasks": [],
        },
        headers=ADMIN_HEADERS,
    )
    assert locked.status_code == 409
    locked_availability = client.patch(
        f"/api/v1/admin/onboarding/plans/{plan.id}/availability",
        json={"is_active": False},
        headers=ADMIN_HEADERS,
    )
    assert locked_availability.status_code == 409
    db.refresh(plan)
    assert plan.name == "SYNTHETIC revised plan"
    assert plan.is_active is True
    assert [task.title for task in sorted(plan.tasks, key=lambda item: item.sequence)] == [
        "Second task first",
        "Optional follow-up",
    ]


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


def test_admin_plan_list_includes_inactive_unused_plans_for_reactivation(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    inactive_plan = make_plan(db, active=False)

    response = client.get("/api/v1/admin/onboarding/plans", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    listed = {item["id"]: item for item in response.json()}
    assert listed[str(inactive_plan.id)]["is_active"] is False
    assert listed[str(inactive_plan.id)]["is_locked"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "   ", "description": "Synthetic", "tasks": []},
        {
            "name": "Synthetic plan",
            "description": "Synthetic",
            "tasks": [
                {
                    "title": "<strong>Unsafe task</strong>",
                    "instructions": "Synthetic",
                    "is_required": True,
                }
            ],
        },
    ],
)
def test_admin_plan_inputs_reject_blank_or_markup_content(
    client: TestClient, db: Session, payload: dict[str, object]
) -> None:
    create_admin(db)

    response = client.post("/api/v1/admin/onboarding/plans", json=payload, headers=ADMIN_HEADERS)

    assert response.status_code == 422


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
    second_ack = client.post(
        "/api/v1/candidate/onboarding/acknowledgements",
        json={
            "document_version_id": str(version.id),
            "wording": "Synthetic acknowledgement wording.",
        },
        headers=headers,
    )
    assert second_ack.status_code == 200
    assert second_ack.json()["id"] != first_ack.json()["id"]
    dashboard = client.get("/api/v1/candidate/onboarding", headers=headers).json()
    assert [item["id"] for item in dashboard["acknowledgements"]] == [second_ack.json()["id"]]
    assert db.query(PolicyAcknowledgement).count() == 2


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
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    version = make_document(db)
    candidate, application, subject = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assigned = assign(client, candidate, application, make_plan(db))
    assert assigned.status_code == 201
    assignment_id = assigned.json()["assignment_id"]
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
    for code in ("background_check", "fsra_authorization", "system_provisioning"):
        assert (
            client.post(
                f"/api/v1/admin/onboarding/assignments/{assignment_id}/gates/{code}/satisfy",
                json={
                    "verified_on": "2026-07-19",
                    "evidence_source": "Synthetic owner review",
                    "evidence_reference": f"SYNTHETIC-{code}",
                },
                headers=ADMIN_HEADERS,
            ).status_code
            == 200
        )
    monkeypatch.setattr(
        documenso_service,
        "issue_ica_envelope",
        lambda *_args, **_kwargs: IssuedEnvelope(
            envelope_id="envelope_activation_ready",
            status="COMPLETED",
            signing_url="https://sign.keeperfinancial.ca/sign/envelope_activation_ready",
        ),
    )
    issued = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica",
        headers=ADMIN_HEADERS,
    )
    assert issued.status_code == 201
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


def test_assignment_scoped_manual_gates_require_evidence_and_can_be_reopened(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    response = assign(client, candidate, application, make_plan(db, with_task=False))
    assignment_id = response.json()["assignment_id"]

    derived = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/gates/policy_acknowledgement/satisfy",
        json={
            "verified_on": "2026-07-19",
            "evidence_source": "Owner review",
            "evidence_reference": "synthetic-reference",
        },
        headers=ADMIN_HEADERS,
    )
    assert derived.status_code == 409

    satisfied = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/gates/background_check/satisfy",
        json={
            "verified_on": "2026-07-19",
            "evidence_source": "Synthetic provider",
            "evidence_reference": "SYNTHETIC-REF-1",
        },
        headers=ADMIN_HEADERS,
    )
    assert satisfied.status_code == 200, satisfied.text
    assert satisfied.json()["assignment_id"] == assignment_id
    assert satisfied.json()["status"] == "satisfied"
    assert satisfied.json()["evidence_kind"] == "manual"
    gate = db.scalar(
        select(ProgrammaticGate).where(
            ProgrammaticGate.assignment_id == uuid.UUID(assignment_id),
            ProgrammaticGate.code == "background_check",
        )
    )
    assert gate is not None
    assert (
        db.scalar(select(GateEvidenceEvent).where(GateEvidenceEvent.gate_id == gate.id)) is not None
    )

    reopened = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/gates/background_check/reopen",
        json={"reason": "Synthetic correction required."},
        headers=ADMIN_HEADERS,
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "open"
    events = db.scalars(
        select(GateEvidenceEvent)
        .where(GateEvidenceEvent.gate_id == gate.id)
        .order_by(GateEvidenceEvent.created_at)
    ).all()
    assert [event.event_type for event in events] == ["satisfied", "reopened"]


def test_new_assignment_cannot_reuse_prior_assignment_gates_or_envelopes(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, first_application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    first = assign(client, candidate, first_application, make_plan(db, with_task=False)).json()
    for code in ("background_check", "fsra_authorization", "system_provisioning"):
        response = client.post(
            f"/api/v1/admin/onboarding/assignments/{first['assignment_id']}/gates/{code}/satisfy",
            json={
                "verified_on": "2026-07-19",
                "evidence_source": "Synthetic owner review",
                "evidence_reference": f"SYNTHETIC-{code}",
            },
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200

    later_application = add_application(db, candidate, CandidateStatus.CONDITIONALLY_SELECTED)
    second = assign(client, candidate, later_application, make_plan(db, with_task=False)).json()
    assert second["assignment_id"] != first["assignment_id"]
    current_gates = db.scalars(
        select(ProgrammaticGate).where(
            ProgrammaticGate.assignment_id == uuid.UUID(second["assignment_id"])
        )
    ).all()
    assert len(current_gates) == 5
    assert all(gate.status == "open" for gate in current_gates)


def test_documenso_status_refresh_is_authoritative_and_assignment_bound(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch, settings
) -> None:
    create_admin(db)
    settings.esign_provider = "documenso"
    settings.documenso_api_base_url = "https://sign.keeperfinancial.ca/api/v2"
    settings.documenso_public_base_url = "https://sign.keeperfinancial.ca"
    settings.documenso_api_token = "synthetic-token"
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db, with_task=False)).json()[
        "assignment_id"
    ]

    linked = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes",
        json={"provider_envelope_id": "envelope_synthetic_1"},
        headers=ADMIN_HEADERS,
    )
    assert linked.status_code == 201, linked.text
    envelope_id = linked.json()["id"]
    assert linked.json()["status"] == "sent"
    assert linked.json()["envelope_url"] is None

    monkeypatch.setattr(
        "keeper_api.services.documenso.fetch_envelope_status",
        lambda *_args, **_kwargs: "COMPLETED",
    )
    refreshed = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{envelope_id}/refresh",
        headers=ADMIN_HEADERS,
    )
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["status"] == "completed"
    assert refreshed.json()["last_synced_at"] is not None
    gate = db.scalar(
        select(ProgrammaticGate).where(
            ProgrammaticGate.assignment_id == uuid.UUID(assignment_id),
            ProgrammaticGate.code == "executed_agreements",
        )
    )
    assert gate is not None and gate.status == "open"
    assert db.scalar(select(CandidateEsignEnvelope)).assignment_id == uuid.UUID(assignment_id)

    def unavailable(*_args: object, **_kwargs: object) -> str:
        raise DocumensoError("Documenso status could not be verified")

    monkeypatch.setattr("keeper_api.services.documenso.fetch_envelope_status", unavailable)
    failed_refresh = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{envelope_id}/refresh",
        headers=ADMIN_HEADERS,
    )
    assert failed_refresh.status_code == 503
    db.expire_all()
    preserved_envelope = db.get(CandidateEsignEnvelope, uuid.UUID(envelope_id))
    assert preserved_envelope is not None
    assert preserved_envelope.status == "completed"
    gate = db.scalar(
        select(ProgrammaticGate).where(
            ProgrammaticGate.assignment_id == uuid.UUID(assignment_id),
            ProgrammaticGate.code == "executed_agreements",
        )
    )
    assert gate is not None and gate.status == "open"
    failed_audit = db.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "esign.envelope_refresh_failed")
    )
    assert failed_audit is not None

    monkeypatch.setattr(
        "keeper_api.services.documenso.fetch_envelope_status",
        lambda *_args, **_kwargs: "COMPLETED",
    )
    assert (
        client.post(
            f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{envelope_id}/refresh",
            headers=ADMIN_HEADERS,
        ).status_code
        == 200
    )
    monkeypatch.setattr(
        "keeper_api.services.documenso.fetch_envelope_status",
        lambda *_args, **_kwargs: "DRAFT",
    )
    draft_refresh = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{envelope_id}/refresh",
        headers=ADMIN_HEADERS,
    )
    assert draft_refresh.status_code == 409
    db.expire_all()
    gate = db.scalar(
        select(ProgrammaticGate).where(
            ProgrammaticGate.assignment_id == uuid.UUID(assignment_id),
            ProgrammaticGate.code == "executed_agreements",
        )
    )
    assert gate is not None and gate.status == "open"


def test_rejected_documenso_envelope_can_be_replaced_without_losing_history(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch, settings
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    assignment_id = assign(client, candidate, application, make_plan(db, with_task=False)).json()[
        "assignment_id"
    ]
    settings.esign_provider = "documenso"
    settings.documenso_api_base_url = "https://sign.keeperfinancial.ca/api/v2"
    settings.documenso_public_base_url = "https://sign.keeperfinancial.ca"
    settings.documenso_api_token = "synthetic-token"
    linked = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes",
        json={"provider_envelope_id": "envelope_rejected"},
        headers=ADMIN_HEADERS,
    )
    monkeypatch.setattr(
        "keeper_api.services.documenso.fetch_envelope_status",
        lambda *_args, **_kwargs: "REJECTED",
    )
    refreshed = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{linked.json()['id']}/refresh",
        headers=ADMIN_HEADERS,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["status"] == "rejected"

    replacement = client.post(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{linked.json()['id']}/replace",
        json={"provider_envelope_id": "envelope_replacement"},
        headers=ADMIN_HEADERS,
    )
    assert replacement.status_code == 201, replacement.text
    assert replacement.json()["envelope_id"] == "envelope_replacement"
    old = db.get(CandidateEsignEnvelope, uuid.UUID(linked.json()["id"]))
    assert old is not None
    assert old.superseded_at is not None
    assert old.replacement_envelope_id == uuid.UUID(replacement.json()["id"])


def test_admin_assignment_list_and_detail_use_human_context(
    client: TestClient, db: Session
) -> None:
    create_admin(db)
    candidate, application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    plan = make_plan(db)
    assignment_id = assign(client, candidate, application, plan).json()["assignment_id"]
    user = db.get(User, candidate.user_id)
    assert user is not None
    user.display_name = "Authoritative Candidate"
    user.email = "authoritative-summary@example.test"
    db.commit()

    listed = client.get("/api/v1/admin/onboarding/assignments", headers=ADMIN_HEADERS)
    assert listed.status_code == 200
    assert listed.json()[0]["candidate_name"] == "Authoritative Candidate"
    assert listed.json()[0]["candidate_email"] == "authoritative-summary@example.test"
    assert listed.json()[0]["opportunity_title"] == application.source_posting_title
    assert listed.json()[0]["plan_name"] == plan.name

    detail = client.get(
        f"/api/v1/admin/onboarding/assignments/{assignment_id}", headers=ADMIN_HEADERS
    )
    assert detail.status_code == 200
    assert detail.json()["application_id"] == str(application.id)
    assert detail.json()["candidate_name"] == "Authoritative Candidate"
    assert detail.json()["candidate_email"] == "authoritative-summary@example.test"
    assert len(detail.json()["gates"]) == 5
    assert detail.json()["activation_ready"] is False


def test_admin_assignment_summaries_project_readiness_for_the_exact_assignment(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_admin(db)
    candidate, first_application, _ = make_candidate(db, CandidateStatus.CONDITIONALLY_SELECTED)
    first_assignment_id = assign(client, candidate, first_application, make_plan(db)).json()[
        "assignment_id"
    ]
    second_application = add_application(
        db, candidate, CandidateStatus.CONDITIONALLY_SELECTED, attempt=2
    )
    second_assignment_id = assign(client, candidate, second_application, make_plan(db)).json()[
        "assignment_id"
    ]
    projected_assignment_ids: list[uuid.UUID] = []

    def exact_readiness(_db: Session, *, candidate_id: uuid.UUID, assignment_id: uuid.UUID) -> bool:
        assert candidate_id == candidate.id
        projected_assignment_ids.append(assignment_id)
        return assignment_id == uuid.UUID(second_assignment_id)

    monkeypatch.setattr(onboarding_routes, "activation_ready", exact_readiness)

    response = client.get("/api/v1/admin/onboarding/assignments", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    by_id = {item["assignment_id"]: item for item in response.json()}
    assert by_id[first_assignment_id]["status"] == "superseded"
    assert by_id[first_assignment_id]["activation_ready"] is False
    assert by_id[second_assignment_id]["status"] == "active"
    assert by_id[second_assignment_id]["activation_ready"] is True
    assert set(projected_assignment_ids) == {
        uuid.UUID(first_assignment_id),
        uuid.UUID(second_assignment_id),
    }
