from __future__ import annotations

import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from keeper_api.models.domain import (
    AuditEvent,
    CandidateApplication,
    CandidateStatusHistory,
    RecruitmentPosting,
)
from keeper_api.services.auth import ExternalIdentity
from keeper_api.services.candidate_applications import (
    owned_application,
    provision_application,
    submit_application,
)

DATABASE_URL = os.getenv("PHASE1C_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="PHASE1C_TEST_DATABASE_URL is required for isolated PostgreSQL concurrency proof",
)


def session_factory():  # type: ignore[no-untyped-def]
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, pool_size=4)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_concurrent_application_start_and_submission_are_exactly_once() -> None:
    sessions = session_factory()
    suffix = uuid.uuid4().hex
    slug = f"synthetic-concurrency-{suffix}"
    subject = f"synthetic-concurrency-{suffix}"
    email = f"{subject}@example.test"
    with sessions.begin() as db:
        db.add(
            RecruitmentPosting(
                slug=slug,
                title="SYNTHETIC PostgreSQL concurrency opportunity",
                summary="Synthetic isolated PostgreSQL test fixture.",
                body="Not a real job posting.",
                status="published",
                version=1,
            )
        )

    barrier = threading.Barrier(2)

    def start() -> tuple[uuid.UUID, bool]:
        with sessions() as db:
            barrier.wait()
            application, created = provision_application(
                db,
                identity=ExternalIdentity(
                    subject=subject,
                    email=email,
                    verified=True,
                    aal="aal1",
                ),
                posting_slug=slug,
                request_id=f"concurrent-start-{uuid.uuid4()}",
            )
            return application.id, created

    with ThreadPoolExecutor(max_workers=2) as executor:
        start_results = list(executor.map(lambda _: start(), range(2)))
    assert len({application_id for application_id, _created in start_results}) == 1
    assert sorted(created for _application_id, created in start_results) == [False, True]
    application_id = start_results[0][0]

    with sessions.begin() as db:
        application = db.get(CandidateApplication, application_id)
        assert application is not None
        application.given_name = "Synthetic"
        application.family_name = "Candidate"
        application.phone = "+14165550100"
        application.city = "London"
        application.country_code = "CA"
        application.preferred_contact_method = "email"
        application.interest_statement = "Synthetic PostgreSQL concurrency evidence. " * 4
        application.privacy_acknowledged = True
        application.information_accuracy_confirmed = True
        actor_user_id = db.scalar(
            select(AuditEvent.actor_user_id).where(
                AuditEvent.event_type == "candidate_application.started",
                AuditEvent.target_id == application_id,
            )
        )
        assert actor_user_id is not None

    submit_barrier = threading.Barrier(2)

    def submit() -> tuple[int, str]:
        with sessions() as db:
            submit_barrier.wait()
            application = owned_application(
                db,
                application_id,
                db.get(CandidateApplication, application_id).candidate_id,  # type: ignore[union-attr]
                lock=True,
            )
            result = submit_application(
                db,
                application,
                expected_revision=1,
                actor_user_id=actor_user_id,
                request_id=f"concurrent-submit-{uuid.uuid4()}",
            )
            return result.revision, result.state

    with ThreadPoolExecutor(max_workers=2) as executor:
        submit_results = list(executor.map(lambda _: submit(), range(2)))
    assert submit_results == [(2, "submitted"), (2, "submitted")]

    with sessions() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(CandidateApplication)
                .where(CandidateApplication.id == application_id)
            )
            == 1
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(CandidateStatusHistory)
                .where(CandidateStatusHistory.application_id == application_id)
            )
            == 1
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.event_type == "candidate_application.submitted",
                    AuditEvent.target_id == application_id,
                )
            )
            == 1
        )
