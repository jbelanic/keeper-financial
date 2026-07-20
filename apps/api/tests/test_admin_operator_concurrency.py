from __future__ import annotations

import os
import threading
import uuid
from collections.abc import Generator, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from keeper_api.core.config import Settings, get_settings
from keeper_api.models.domain import (
    Candidate,
    CandidateApplication,
    CandidateEsignEnvelope,
    CandidateOnboardingAssignment,
    GateEvidenceEvent,
    OnboardingPlan,
    ProgrammaticGate,
)
from keeper_api.services.onboarding import (
    OnboardingError,
    assign_onboarding_plan,
    refresh_esign_envelope,
    replace_esign_envelope,
    satisfy_gate,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEEPER_RUN_SCHEMA_MIGRATION_E2E") != "1",
    reason="set KEEPER_RUN_SCHEMA_MIGRATION_E2E=1 to run PostgreSQL concurrency tests",
)

API_ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def _alembic_config(database_url: str) -> Iterator[Config]:
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    try:
        config = Config(str(API_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(API_ROOT / "alembic"))
        yield config
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        get_settings.cache_clear()


@pytest.fixture
def postgres_session_factory() -> Generator[sessionmaker[Session], None, None]:
    configured = make_url(get_settings().database_url)
    if not configured.drivername.startswith("postgresql"):
        pytest.skip("configured DATABASE_URL is not PostgreSQL")

    admin_url = configured.set(database="postgres")
    database_name = f"keeper_concurrency_{uuid.uuid4().hex}"
    temporary_url = configured.set(database=database_name)
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))

    engine = create_engine(temporary_url)
    try:
        with _alembic_config(temporary_url.render_as_string(hide_password=False)) as config:
            command.upgrade(config, "head")
        yield sessionmaker(bind=engine, expire_on_commit=False)
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
        admin_engine.dispose()


def _seed_assignment(
    session_factory: sessionmaker[Session], *, envelope_status: str = "rejected"
) -> dict[str, uuid.UUID]:
    identifiers = {
        key: uuid.uuid4()
        for key in (
            "admin",
            "candidate_user",
            "candidate",
            "posting",
            "application",
            "plan",
            "assignment",
            "envelope",
            "executed_gate",
            "manual_gate",
        )
    }
    now = datetime.now(UTC)
    with session_factory.begin() as session:
        session.execute(
            text(
                """
                INSERT INTO users
                    (id, email, display_name, is_active, created_at, updated_at)
                VALUES
                    (:admin, 'admin@concurrency.invalid', 'Concurrency Admin',
                     true, :now, :now),
                    (:candidate_user, 'candidate@concurrency.invalid',
                     'Concurrency Candidate', true, :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO recruitment_postings
                    (id, slug, title, summary, body, status, version, created_at, updated_at)
                VALUES
                    (:posting, 'concurrency-posting', 'Concurrency posting',
                     'Synthetic fixture.', 'Synthetic fixture.', 'published', 1, :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO candidates
                    (id, user_id, status, created_at, updated_at)
                VALUES
                    (:candidate, :candidate_user, 'onboarding_in_progress', :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO candidate_applications
                    (id, candidate_id, recruitment_posting_id, attempt_number,
                     source_posting_slug, source_posting_title, source_posting_version,
                     schema_version, revision, state, status, email, submitted_at,
                     created_at, updated_at)
                VALUES
                    (:application, :candidate, :posting, 1, 'concurrency-posting',
                     'Concurrency posting', 1, 'synthetic-concurrency-v1', 1, 'submitted',
                     'onboarding_in_progress', 'candidate@concurrency.invalid',
                     :now, :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO onboarding_plans
                    (id, name, description, is_active, created_at, updated_at)
                VALUES
                    (:plan, 'Concurrency plan', 'Synthetic fixture.', true, :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO candidate_onboarding_assignments
                    (id, candidate_id, application_id, onboarding_plan_id, generation,
                     status, assigned_by_user_id, created_at, updated_at)
                VALUES
                    (:assignment, :candidate, :application, :plan, 1, 'active',
                     :admin, :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO programmatic_gates
                    (id, candidate_id, assignment_id, code, label, status, created_at, updated_at)
                VALUES
                    (:executed_gate, :candidate, :assignment, 'executed_agreements',
                     'Executed agreements', 'open', :now, :now),
                    (:manual_gate, :candidate, :assignment, 'background_check',
                     'Background check', 'open', :now, :now)
                """
            ),
            {**identifiers, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO candidate_esign_envelopes
                    (id, candidate_id, assignment_id, provider, envelope_id, status,
                     created_by_user_id, created_at, updated_at)
                VALUES
                    (:envelope, :candidate, :assignment, 'documenso',
                     'concurrency-predecessor', :envelope_status, :admin, :now, :now)
                """
            ),
            {**identifiers, "envelope_status": envelope_status, "now": now},
        )
    return identifiers


def test_delayed_completed_refresh_cannot_satisfy_replaced_predecessor(
    postgres_session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    identifiers = _seed_assignment(postgres_session_factory)
    provider_started = threading.Event()
    release_provider = threading.Event()

    def delayed_completed(*_args: object, **_kwargs: object) -> str:
        provider_started.set()
        if not release_provider.wait(timeout=5):
            raise AssertionError("replacement did not release delayed provider response")
        return "COMPLETED"

    monkeypatch.setattr(
        "keeper_api.services.documenso.fetch_envelope_status", delayed_completed
    )
    settings = Settings(
        esign_provider="documenso",
        documenso_api_base_url="https://sign.keeperfinancial.ca/api/v2",
        documenso_public_base_url="https://sign.keeperfinancial.ca",
        documenso_api_token="synthetic-token",
    )

    def refresh() -> CandidateEsignEnvelope | Exception:
        with postgres_session_factory() as session:
            assignment = session.get(CandidateOnboardingAssignment, identifiers["assignment"])
            envelope = session.get(CandidateEsignEnvelope, identifiers["envelope"])
            assert assignment is not None and envelope is not None
            try:
                return refresh_esign_envelope(
                    session,
                    assignment=assignment,
                    envelope=envelope,
                    settings=settings,
                    actor_user_id=identifiers["admin"],
                    request_id="concurrency-refresh",
                )
            except Exception as exc:  # returned for exact assertion in the parent thread
                return exc

    with ThreadPoolExecutor(max_workers=1) as executor:
        refresh_result = executor.submit(refresh)
        assert provider_started.wait(timeout=5)
        with postgres_session_factory() as session:
            assignment = session.get(CandidateOnboardingAssignment, identifiers["assignment"])
            envelope = session.get(CandidateEsignEnvelope, identifiers["envelope"])
            assert assignment is not None and envelope is not None
            replacement = replace_esign_envelope(
                session,
                assignment=assignment,
                envelope=envelope,
                provider_envelope_id="concurrency-replacement",
                actor_user_id=identifiers["admin"],
                request_id="concurrency-replace",
            )
            replacement_id = replacement.id
        release_provider.set()
        delayed_result = refresh_result.result(timeout=5)

    assert isinstance(delayed_result, OnboardingError)
    with postgres_session_factory() as session:
        predecessor = session.get(CandidateEsignEnvelope, identifiers["envelope"])
        replacement = session.get(CandidateEsignEnvelope, replacement_id)
        gate = session.get(ProgrammaticGate, identifiers["executed_gate"])
        assert predecessor is not None and predecessor.superseded_at is not None
        assert predecessor.status == "rejected"
        assert replacement is not None and replacement.status == "sent"
        assert gate is not None and gate.status == "open"


def test_concurrent_manual_satisfy_records_one_evidence_transition(
    postgres_session_factory: sessionmaker[Session],
) -> None:
    identifiers = _seed_assignment(postgres_session_factory, envelope_status="sent")
    start = threading.Barrier(2)

    def satisfy(request_id: str) -> ProgrammaticGate | Exception:
        with postgres_session_factory() as session:
            assignment = session.get(CandidateOnboardingAssignment, identifiers["assignment"])
            assert assignment is not None
            start.wait(timeout=5)
            try:
                return satisfy_gate(
                    session,
                    assignment=assignment,
                    code="background_check",
                    verified_on=date(2026, 7, 19),
                    evidence_source="Synthetic concurrency test",
                    evidence_reference=request_id,
                    actor_user_id=identifiers["admin"],
                    request_id=request_id,
                )
            except Exception as exc:  # returned for exact assertion in the parent thread
                return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(satisfy, ("gate-a", "gate-b")))

    assert sum(isinstance(result, ProgrammaticGate) for result in results) == 1
    assert sum(isinstance(result, OnboardingError) for result in results) == 1
    with postgres_session_factory() as session:
        gate = session.get(ProgrammaticGate, identifiers["manual_gate"])
        events = session.query(GateEvidenceEvent).filter_by(gate_id=identifiers["manual_gate"]).all()
        assert gate is not None and gate.status == "satisfied"
        assert [event.event_type for event in events] == ["satisfied"]


def test_concurrent_assignments_across_applications_leave_one_active_assignment(
    postgres_session_factory: sessionmaker[Session],
) -> None:
    identifiers = _seed_assignment(postgres_session_factory, envelope_status="sent")
    race_ids = {
        key: uuid.uuid4()
        for key in (
            "posting_a",
            "posting_b",
            "application_a",
            "application_b",
            "plan_a",
            "plan_b",
        )
    }
    now = datetime.now(UTC)
    with postgres_session_factory.begin() as session:
        session.execute(
            text(
                """
                INSERT INTO recruitment_postings
                    (id, slug, title, summary, body, status, version, created_at, updated_at)
                VALUES
                    (:posting_a, 'concurrency-posting-a', 'Concurrency posting A',
                     'Synthetic fixture.', 'Synthetic fixture.', 'published', 1, :now, :now),
                    (:posting_b, 'concurrency-posting-b', 'Concurrency posting B',
                     'Synthetic fixture.', 'Synthetic fixture.', 'published', 1, :now, :now)
                """
            ),
            {**race_ids, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO candidate_applications
                    (id, candidate_id, recruitment_posting_id, attempt_number,
                     source_posting_slug, source_posting_title, source_posting_version,
                     schema_version, revision, state, status, email, submitted_at,
                     created_at, updated_at)
                VALUES
                    (:application_a, :candidate, :posting_a, 1, 'concurrency-posting-a',
                     'Concurrency posting A', 1, 'synthetic-concurrency-v1', 2,
                     'submitted', 'conditionally_selected', 'candidate@concurrency.invalid',
                     :now, :now, :now),
                    (:application_b, :candidate, :posting_b, 1, 'concurrency-posting-b',
                     'Concurrency posting B', 1, 'synthetic-concurrency-v1', 3,
                     'submitted', 'conditionally_selected', 'candidate@concurrency.invalid',
                     :now, :now, :now)
                """
            ),
            {**identifiers, **race_ids, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO onboarding_plans
                    (id, name, description, is_active, created_at, updated_at)
                VALUES
                    (:plan_a, 'Concurrency plan A', 'Synthetic fixture.', true, :now, :now),
                    (:plan_b, 'Concurrency plan B', 'Synthetic fixture.', true, :now, :now)
                """
            ),
            {**race_ids, "now": now},
        )

    start = threading.Barrier(2)

    def assign(pair: tuple[uuid.UUID, uuid.UUID]) -> uuid.UUID:
        application_id, plan_id = pair
        with postgres_session_factory() as session:
            candidate = session.get(Candidate, identifiers["candidate"])
            application = session.get(CandidateApplication, application_id)
            plan = session.get(OnboardingPlan, plan_id)
            assert candidate is not None and application is not None and plan is not None
            start.wait(timeout=5)
            assignment = assign_onboarding_plan(
                session,
                candidate=candidate,
                application=application,
                plan=plan,
                actor_user_id=identifiers["admin"],
                request_id=str(application_id),
            )
            return assignment.id

    pairs = (
        (race_ids["application_a"], race_ids["plan_a"]),
        (race_ids["application_b"], race_ids["plan_b"]),
    )
    with ThreadPoolExecutor(max_workers=2) as executor:
        new_assignment_ids = list(executor.map(assign, pairs))

    with postgres_session_factory() as session:
        assignments = (
            session.query(CandidateOnboardingAssignment)
            .filter_by(candidate_id=identifiers["candidate"])
            .all()
        )
        active = [assignment for assignment in assignments if assignment.status == "active"]
        assert len(active) == 1
        assert {assignment.id for assignment in assignments}.issuperset(new_assignment_ids)
        assert active[0].application_id in {
            race_ids["application_a"],
            race_ids["application_b"],
        }
