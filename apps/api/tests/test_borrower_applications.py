from __future__ import annotations

import base64
import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from keeper_api.core.config import Settings
from keeper_api.db.base import Base
from keeper_api.db.session import get_db
from keeper_api.main import app
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerApplicationStatusHistory,
    BorrowerAssignmentHistory,
)
from keeper_api.services.borrower_applications import (
    assign_application,
    create_consent_record,
    get_application_summary,
    get_latest_payload,
    has_submission_evidence,
    revoke_capability,
    save_draft_payload,
    start_borrower_application,
    transition_lifecycle,
)
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoState,
    load_borrower_crypto_state,
)


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_keys() -> dict[str, bytes]:
    return {
        "v1": os.urandom(32),
    }


@pytest.fixture
def test_hmac_key() -> bytes:
    return os.urandom(32)


@pytest.fixture
def keyring_file(test_keys: dict[str, bytes]) -> Path:
    import base64

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        keyring_data = {
            "version": 1,
            "keys": {k: base64.b64encode(v).decode() for k, v in test_keys.items()},
        }
        json.dump(keyring_data, f)
        f.flush()
        return Path(f.name)


@pytest.fixture
def hmac_key_file(test_hmac_key: bytes) -> Path:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(test_hmac_key)
        f.flush()
        return Path(f.name)


@pytest.fixture
def crypto_state(
    keyring_file: Path,
    hmac_key_file: Path,
) -> BorrowerCryptoState:
    return load_borrower_crypto_state(
        keyring_path=keyring_file,
        hmac_key_path=hmac_key_file,
        active_key_id="v1",
        borrower_origin="https://apply.keeperfinancial.ca",
        production=False,
    )


class TestStartBorrowerApplication:
    def test_start_creates_application(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        assert application is not None
        assert application.id is not None
        assert application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value
        assert application.revision == 0
        assert application.payload_revision == 0
        assert application.capability_digest is not None
        assert application.capability_session_id is not None
        assert application.draft_expires_at is not None
        assert capability is not None

    def test_start_records_status_history(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        history = (
            db_session.query(BorrowerApplicationStatusHistory)
            .filter(BorrowerApplicationStatusHistory.application_id == application.id)
            .all()
        )

        assert len(history) == 1
        assert history[0].to_status == BorrowerApplicationLifecycleStatus.DRAFT.value
        assert history[0].actor_source == "public"
        assert history[0].reason_category == "start"

    def test_start_sets_draft_expires_at(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        assert application.draft_expires_at is not None
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        assert application.draft_expires_at > now_utc


class TestSaveDraftPayload:
    def test_save_draft_payload(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        payload_data = {
            "primary_borrower": {
                "first_name": "John",
                "last_name": "Doe",
                "sin": "123456789",
            },
        }

        original_activity_at = application.last_activity_at

        db_session.expire(application)

        updated_application = save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=payload_data,
            settings=None,
        )

        assert updated_application.revision == 1
        assert updated_application.payload_revision == 1
        assert updated_application.last_activity_at > original_activity_at

    def test_save_draft_payload_stale_revision(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        payload_data = {"primary_borrower": {"first_name": "John"}}

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=payload_data,
            settings=None,
        )

        with pytest.raises(ValueError, match="stale revision"):
            save_draft_payload(
                db=db_session,
                crypto_state=crypto_state,
                application_id=application.id,
                capability_session_id=application.capability_session_id,
                expected_revision=0,
                payload_data=payload_data,
                settings=None,
            )

    def test_save_draft_payload_no_payload_change(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        payload_data = {"primary_borrower": {"first_name": "John"}}

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=payload_data,
            settings=None,
        )

        original_activity_at = db_session.get(BorrowerApplication, application.id).last_activity_at

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data=payload_data,
            settings=None,
        )

        updated_application = db_session.get(BorrowerApplication, application.id)
        assert updated_application.last_activity_at >= original_activity_at


class TestGetLatestPayload:
    def test_get_latest_payload(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        payload_data = {"primary_borrower": {"first_name": "John"}}

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=payload_data,
            settings=None,
        )

        payload = get_latest_payload(
            db_session,
            crypto_state,
            application.id,
            1,
        )

        assert payload is not None
        assert payload["primary_borrower"]["first_name"] == "John"

    def test_get_latest_payload_not_found(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        payload = get_latest_payload(
            db_session,
            crypto_state,
            uuid.uuid4(),
            1,
        )

        assert payload is None


class TestGetApplicationSummary:
    def test_get_application_summary(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        summary = get_application_summary(db_session, application)

        assert summary["id"] == str(application.id)
        assert summary["lifecycle_status"] == BorrowerApplicationLifecycleStatus.DRAFT.value
        assert summary["revision"] == 0
        assert summary["has_sin"] is False
        assert summary["has_co_borrower"] is False


class TestTransitionLifecycle:
    def test_transition_lifecycle(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        transition_lifecycle(
            db=db_session,
            application_id=application.id,
            from_status=BorrowerApplicationLifecycleStatus.DRAFT,
            to_status=BorrowerApplicationLifecycleStatus.SUBMITTED,
            actor_user_id=None,
            actor_source="public",
            reason_category="submission",
            capability_session_id=application.capability_session_id,
        )

        updated_application = db_session.get(BorrowerApplication, application.id)
        assert (
            updated_application.lifecycle_status
            == BorrowerApplicationLifecycleStatus.SUBMITTED.value
        )
        assert updated_application.submitted_at is not None
        assert updated_application.retention_due_at is not None
        assert updated_application.capability_revoked_at is not None

    def test_transition_lifecycle_invalid_transition(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        with pytest.raises(ValueError, match="cannot transition"):
            transition_lifecycle(
                db=db_session,
                application_id=application.id,
                from_status=BorrowerApplicationLifecycleStatus.SUBMITTED,
                to_status=BorrowerApplicationLifecycleStatus.COMPLETED,
                actor_user_id=None,
                actor_source="public",
            )

    def test_transition_to_withdrawn_revokes_capability(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        transition_lifecycle(
            db=db_session,
            application_id=application.id,
            from_status=BorrowerApplicationLifecycleStatus.DRAFT,
            to_status=BorrowerApplicationLifecycleStatus.WITHDRAWN,
            actor_user_id=None,
            actor_source="public",
            reason_category="withdrawal",
        )

        updated_application = db_session.get(BorrowerApplication, application.id)
        assert updated_application.capability_revoked_at is not None


class TestAssignApplication:
    def test_assign_application(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        agent_user_id = uuid.uuid4()

        assign_application(
            db=db_session,
            application_id=application.id,
            agent_user_id=agent_user_id,
            actor_user_id=uuid.uuid4(),
            reason_category="initial_assignment",
        )

        updated_application = db_session.get(BorrowerApplication, application.id)
        assert updated_application.assigned_agent_id == agent_user_id
        assert updated_application.assigned_at is not None

    def test_unassign_application(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        agent_user_id = uuid.uuid4()

        assign_application(
            db=db_session,
            application_id=application.id,
            agent_user_id=agent_user_id,
            actor_user_id=uuid.uuid4(),
            reason_category="initial_assignment",
        )

        assign_application(
            db=db_session,
            application_id=application.id,
            agent_user_id=None,
            actor_user_id=uuid.uuid4(),
            reason_category="unassignment",
        )

        updated_application = db_session.get(BorrowerApplication, application.id)
        assert updated_application.assigned_agent_id is None

    def test_unassign_requires_unassignment_reason(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        with pytest.raises(ValueError, match="unassignment requires reason_category"):
            assign_application(
                db=db_session,
                application_id=application.id,
                agent_user_id=None,
                actor_user_id=uuid.uuid4(),
                reason_category="other_reason",
            )

    def test_assignment_history_recorded(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        agent_user_id = uuid.uuid4()

        assign_application(
            db=db_session,
            application_id=application.id,
            agent_user_id=agent_user_id,
            actor_user_id=uuid.uuid4(),
            reason_category="initial_assignment",
            reason_detail="Test assignment",
        )

        history = (
            db_session.query(BorrowerAssignmentHistory)
            .filter(BorrowerAssignmentHistory.application_id == application.id)
            .all()
        )

        assert len(history) == 1
        assert history[0].agent_user_id == agent_user_id
        assert history[0].reason_category == "initial_assignment"
        assert history[0].reason_detail == "Test assignment"


class TestRevokeCapability:
    def test_revoke_capability(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        revoke_capability(db_session, application.id)

        updated_application = db_session.get(BorrowerApplication, application.id)
        assert updated_application.capability_revoked_at is not None

    def test_revoke_capability_nonexistent(self, db_session: Session) -> None:
        revoke_capability(db_session, uuid.uuid4())


class TestCreateConsentRecord:
    def test_create_consent_record(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        consent = create_consent_record(
            db=db_session,
            application_id=application.id,
            submission_revision=1,
            consent_version="v1.0",
            wording_digest="abc123",
            borrower_coverage="primary_only",
            borrower_count=1,
            capture_source="borrower_draft",
            capability_session_id=application.capability_session_id,
            acknowledged_at=datetime.now(UTC),
        )

        assert consent is not None
        assert consent.application_id == application.id
        assert consent.consent_version == "v1.0"
        assert consent.wording_digest == "abc123"


class TestHasSubmissionEvidence:
    def test_has_submission_evidence_draft(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        assert has_submission_evidence(db_session, application.id) is False


class TestIncrementalDraftMerge:
    """Phase C API correction: a partial PATCH must merge into the prior saved
    draft (not replace it), preserve a previously stored SIN when the partial
    omits it, and reject unknown keys (fail closed)."""

    def test_partial_save_merges_prior_sections(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(
            db=db_session, crypto_state=crypto_state, settings=None
        )

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data={"mortgage_request": {"mortgage_objective": "purchase"}},
            settings=None,
        )

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data={
                "primary_borrower": {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "sin": "046454286",
                }
            },
            settings=None,
        )

        merged = get_latest_payload(db_session, crypto_state, application.id, 2)
        assert merged["mortgage_request"]["mortgage_objective"] == "purchase"
        assert merged["primary_borrower"]["first_name"] == "Jane"
        assert merged["primary_borrower"]["sin"] == "046454286"

    def test_sin_preserved_when_partial_omits_sin(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(
            db=db_session, crypto_state=crypto_state, settings=None
        )

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data={
                "primary_borrower": {
                    "first_name": "Jane",
                    "sin": "046454286",
                }
            },
            settings=None,
        )
        summary_with_sin = get_application_summary(
            db_session,
            db_session.get(BorrowerApplication, application.id),
        )
        assert summary_with_sin["has_sin"] is True

        # Partial save that updates only the last name must not wipe the SIN.
        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data={
                "primary_borrower": {"first_name": "Janet"},
            },
            settings=None,
        )
        summary_after = get_application_summary(
            db_session,
            db_session.get(BorrowerApplication, application.id),
        )
        assert summary_after["has_sin"] is True
        merged = get_latest_payload(db_session, crypto_state, application.id, 2)
        assert merged["primary_borrower"]["first_name"] == "Janet"
        # SIN is stored in a dedicated ciphertext, never returned in the payload.
        assert "sin" not in merged["primary_borrower"]

    def test_unknown_key_rejected_fail_closed(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        from pydantic import ValidationError

        from keeper_api.schemas.borrower_payload import validate_borrower_draft

        with pytest.raises(ValidationError):
            validate_borrower_draft(
                {"mortgage_request": {"mortgage_objective": "purchase"}, "bogus_field": 1}
            )

    def test_subject_property_optional_fields_accepted(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        from keeper_api.schemas.borrower_payload import validate_borrower_draft

        draft = validate_borrower_draft(
            {
                "subject_property": {
                    "property_style": "detached",
                    "occupancy": "owner_occupied",
                    "lot_details": "50ft x 120ft",
                    "garage_details": "attached 2-car",
                }
            }
        )
        assert draft.subject_property.property_style.value == "detached"
        assert draft.subject_property.occupancy.value == "owner_occupied"
        assert draft.subject_property.lot_details == "50ft x 120ft"
        assert draft.subject_property.garage_details == "attached 2-car"

    def test_has_submission_evidence_submitted(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        transition_lifecycle(
            db=db_session,
            application_id=application.id,
            from_status=BorrowerApplicationLifecycleStatus.DRAFT,
            to_status=BorrowerApplicationLifecycleStatus.SUBMITTED,
            actor_user_id=None,
            actor_source="public",
            reason_category="submission",
            capability_session_id=application.capability_session_id,
        )

        assert has_submission_evidence(db_session, application.id) is False

    def test_has_submission_evidence_with_snapshot_and_consent(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        transition_lifecycle(
            db=db_session,
            application_id=application.id,
            from_status=BorrowerApplicationLifecycleStatus.DRAFT,
            to_status=BorrowerApplicationLifecycleStatus.SUBMITTED,
            actor_user_id=None,
            actor_source="public",
            reason_category="submission",
            capability_session_id=application.capability_session_id,
        )

        from keeper_api.models.borrower import BorrowerApplicationSnapshot

        snapshot = BorrowerApplicationSnapshot(
            application_id=application.id,
            submission_revision=1,
            key_id="v1",
            nonce=os.urandom(12),
            ciphertext_hash="abc123",
            plaintext_hash="def456",
            object_key="snapshots/test.key",
            size_bytes=1024,
        )
        db_session.add(snapshot)
        db_session.commit()

        create_consent_record(
            db=db_session,
            application_id=application.id,
            submission_revision=1,
            consent_version="v1.0",
            wording_digest="abc123",
            borrower_coverage="primary_only",
            borrower_count=1,
            capture_source="borrower_draft",
            capability_session_id=application.capability_session_id,
            acknowledged_at=datetime.now(UTC),
        )

        assert has_submission_evidence(db_session, application.id) is True


class TestBorrowerDraftRouteIntegration:
    """End-to-end route tests proving the Phase C API correction: a partial
    PATCH now validates (200, not 422) and merges into the prior draft, while
    unknown keys still fail closed (422)."""

    @pytest.fixture
    def route_client(self, tmp_path: Path, monkeypatch):
        keyring_path = tmp_path / "keyring.json"
        hmac_path = tmp_path / "hmac.key"
        keyring_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "keys": {
                        "v1": base64.b64encode(os.urandom(32)).decode(),
                    },
                }
            )
        )
        hmac_path.write_bytes(os.urandom(32))

        settings = Settings(
            _env_file=None,
            app_env="local",
            database_url="sqlite+pysqlite:///:memory:",
            borrower_application_enabled=True,
            borrower_application_origin="http://localhost:8000",
            borrower_encryption_keyring_file=str(keyring_path),
            borrower_capability_hmac_key_file=str(hmac_path),
        )

        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)

        def override_db():
            with SessionLocal() as session:
                yield session

        from keeper_api.core.config import get_settings as _real_get_settings

        monkeypatch.setattr(_real_get_settings, "cache_clear", lambda: None)
        monkeypatch.setattr("keeper_api.core.config.get_settings", lambda: settings)
        monkeypatch.setattr(
            "keeper_api.api.routes.borrower_applications.get_settings",
            lambda: settings,
        )
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[_real_get_settings] = lambda: settings
        try:
            with TestClient(app) as client:
                yield client
        finally:
            app.dependency_overrides.clear()

    def _start(self, client: TestClient) -> tuple[str, str]:
        resp = client.post(
            "/api/v1/borrower-applications/start",
            headers={
                "Host": "localhost:8000",
                "Origin": "http://localhost:8000",
                "x-keeper-borrower-csrf": "1",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        return body["application_id"], resp.cookies.get("__Host-keeper-borrower-draft")

    def test_partial_patch_merges_and_returns_200(self, route_client: TestClient) -> None:
        application_id, _ = self._start(route_client)
        headers = {
            "Host": "localhost:8000",
            "Origin": "http://localhost:8000",
            "x-keeper-borrower-csrf": "1",
        }

        first = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=headers,
            json={
                "expected_revision": 0,
                "payload": {"mortgage_request": {"mortgage_objective": "purchase"}},
            },
        )
        assert first.status_code == 200, first.text
        assert first.json()["revision"] == 1

        second = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=headers,
            json={
                "expected_revision": 1,
                "payload": {
                    "primary_borrower": {
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "sin": "046454286",
                    }
                },
            },
        )
        assert second.status_code == 200, second.text
        assert second.json()["revision"] == 2
        assert second.json()["has_sin"] is True

    def test_partial_patch_rejects_unknown_key(self, route_client: TestClient) -> None:
        application_id, _ = self._start(route_client)
        resp = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers={
                "Host": "localhost:8000",
                "Origin": "http://localhost:8000",
                "x-keeper-borrower-csrf": "1",
            },
            json={
                "expected_revision": 0,
                "payload": {
                    "mortgage_request": {"mortgage_objective": "purchase"},
                    "bogus_field": 1,
                },
            },
        )
        assert resp.status_code == 422, resp.text

    def test_web_shaped_subject_property_partial_merges(self, route_client: TestClient) -> None:
        application_id, _ = self._start(route_client)
        headers = {
            "Host": "localhost:8000",
            "Origin": "http://localhost:8000",
            "x-keeper-borrower-csrf": "1",
        }
        first = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=headers,
            json={
                "expected_revision": 0,
                "payload": {
                    "subject_property": {
                        "address": "123 Main St",
                        "city": "Toronto",
                        "province": "ON",
                        "postal_code": "M5V 2T6",
                        "property_type": "single_family",
                        "property_style": "detached",
                        "occupancy": "owner_occupied",
                    }
                },
            },
        )
        assert first.status_code == 200, first.text

        second = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=headers,
            json={
                "expected_revision": 1,
                "payload": {
                    "subject_property": {
                        "lot_details": "50ft frontage",
                        "garage_details": "attached 2-car",
                    }
                },
            },
        )
        assert second.status_code == 200, second.text
        assert second.json()["revision"] == 2
