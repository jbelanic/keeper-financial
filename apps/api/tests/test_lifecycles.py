import pytest
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import AgentProfile, AuditEvent, CandidateStatusHistory
from keeper_api.models.statuses import AgentProfileStatus, CandidateStatus
from keeper_api.services.agents import AgentProfileLifecycleService, InvalidAgentProfileTransition
from keeper_api.services.candidates import CandidateLifecycleService, InvalidCandidateTransition


def test_candidate_valid_transition_creates_history_and_audit(db: Session) -> None:
    actor, _ = create_user(db, subject="actor", role_code="brokerage_admin")
    _, candidate = create_user(
        db, subject="candidate", role_code="candidate", candidate_status="application_submitted"
    )
    assert candidate is not None
    CandidateLifecycleService(db).transition(
        candidate,
        CandidateStatus.UNDER_REVIEW,
        actor_user_id=actor.id,
    )
    assert candidate.status == "under_review"
    assert db.query(CandidateStatusHistory).count() == 1
    assert db.query(AuditEvent).filter_by(event_type="candidate.status_changed").count() == 1


def test_candidate_invalid_transition_is_rejected(db: Session) -> None:
    actor, _ = create_user(db, subject="actor", role_code="brokerage_admin")
    _, candidate = create_user(
        db, subject="candidate", role_code="candidate", candidate_status="prospect"
    )
    assert candidate is not None
    with pytest.raises(InvalidCandidateTransition):
        CandidateLifecycleService(db).transition(
            candidate,
            CandidateStatus.ACTIVE,
            actor_user_id=actor.id,
        )
    assert candidate.status == "prospect"


def test_decline_requires_reason(db: Session) -> None:
    actor, _ = create_user(db, subject="actor", role_code="brokerage_admin")
    _, candidate = create_user(
        db, subject="candidate", role_code="candidate", candidate_status="under_review"
    )
    assert candidate is not None
    with pytest.raises(InvalidCandidateTransition, match="reason"):
        CandidateLifecycleService(db).transition(
            candidate,
            CandidateStatus.DECLINED,
            actor_user_id=actor.id,
        )


def test_agent_profile_cannot_publish_without_approval(db: Session) -> None:
    actor, _ = create_user(db, subject="actor", role_code="brokerage_admin")
    agent, _ = create_user(db, subject="agent")
    profile = AgentProfile(
        user_id=agent.id,
        slug="synthetic-agent",
        licensed_name="Synthetic Agent",
        approved_title="Mortgage Agent",
        licence_number="SYNTHETIC-NOT-A-LICENCE",
        status=AgentProfileStatus.PENDING_APPROVAL.value,
    )
    db.add(profile)
    db.commit()
    with pytest.raises(InvalidAgentProfileTransition, match="approver"):
        AgentProfileLifecycleService(db).transition(
            profile,
            AgentProfileStatus.PUBLISHED,
            actor_user_id=actor.id,
            actor_can_approve=False,
        )
    assert profile.approved_at is None


def test_authorized_profile_publication_records_approval(db: Session) -> None:
    actor, _ = create_user(db, subject="actor", role_code="brokerage_admin")
    agent, _ = create_user(db, subject="agent")
    profile = AgentProfile(
        user_id=agent.id,
        slug="synthetic-agent",
        licensed_name="Synthetic Agent",
        approved_title="Mortgage Agent",
        licence_number="SYNTHETIC-NOT-A-LICENCE",
        status="pending_approval",
    )
    db.add(profile)
    db.commit()
    AgentProfileLifecycleService(db).transition(
        profile,
        AgentProfileStatus.PUBLISHED,
        actor_user_id=actor.id,
        actor_can_approve=True,
    )
    assert profile.status == "published"
    assert profile.approved_by_user_id == actor.id
    assert profile.approved_at is not None
