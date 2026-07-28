from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from keeper_api.core.config import Settings
from keeper_api.db.base import Base
from keeper_api.db.session import get_db
from keeper_api.main import app
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerApplicationPayload,
    BorrowerApplicationSnapshot,
    BorrowerApplicationStatusHistory,
    BorrowerAssignmentHistory,
    BorrowerConsentCatalog,
    BorrowerConsentRecord,
    BorrowerDocument,
    BorrowerSinRevealAudit,
)
from keeper_api.models.domain import AuditEvent, Candidate, Role, User, UserIdentity, UserRole
from keeper_api.models.statuses import CandidateStatus
from keeper_api.services.audit import AuditService
from keeper_api.services.borrower_applications import (
    assign_application,
    create_consent_record,
    get_application_summary,
    get_latest_payload,
    has_submission_evidence,
    revoke_capability,
    save_draft_payload,
    start_borrower_application,
    submit_borrower_application,
    transition_lifecycle,
)
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoState,
    load_borrower_crypto_state,
)
from keeper_api.services.borrower_documents import BorrowerDocumentStorageError
from keeper_api.services.malware_scanner import MalwareScannerUnavailable, ScanDecision


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

    def test_locked_save_refreshes_stale_identity_map_lifecycle(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )
        db_session.execute(
            update(BorrowerApplication)
            .where(BorrowerApplication.id == application.id)
            .values(lifecycle_status=BorrowerApplicationLifecycleStatus.SUBMITTED.value)
            .execution_options(synchronize_session=False)
        )
        assert application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value

        with pytest.raises(ValueError, match="not in draft"):
            save_draft_payload(
                db=db_session,
                crypto_state=crypto_state,
                application_id=application.id,
                capability_session_id=application.capability_session_id,
                expected_revision=0,
                payload_data={"primary_borrower": {"first_name": "John"}},
                settings=None,
            )


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
        assert merged is not None
        assert merged["primary_borrower"]["first_name"] == "Janet"
        # The internal submit projection restores the dedicated ciphertext;
        # public recovery responses strip it before serialization.
        assert merged["primary_borrower"]["sin"] == "046454286"

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
            with TestClient(
                app,
                base_url="https://localhost:8000",
                backend_options={"use_uvloop": True},
            ) as client:
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


class _DeterministicBorrowerScanner:
    def scan(self, content: bytes) -> ScanDecision:
        from document_samples import eicar_bytes

        if eicar_bytes() in content:
            return ScanDecision(status="rejected", source="test")
        return ScanDecision(status="clean", source="test")


def _borrower_route_settings(tmp_path: Path) -> Settings:
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

    return Settings(
        _env_file=None,
        app_env="local",
        database_url="sqlite+pysqlite:///:memory:",
        dev_auth_enabled=True,
        storage_backend="local",
        local_storage_path=tmp_path / "borrower-objects",
        borrower_application_enabled=True,
        borrower_application_origin="http://localhost:8000",
        borrower_encryption_keyring_file=str(keyring_path),
        borrower_capability_hmac_key_file=str(hmac_path),
    )


def _valid_submit_payload(*, with_co_borrower: bool = False) -> dict[str, object]:
    borrower = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.test",
        "phone": "14165550123",
        "preferred_contact_method": "email",
        "date_of_birth": "1988-01-01",
        "sin": "046454286",
        "marital_status": "married",
        "number_of_dependants": 1,
        "current_address": {
            "street": "1 King St",
            "city": "London",
            "province": "ON",
            "postal_code": "N6A1A1",
            "years_at_address": 3,
            "months_at_address": 0,
        },
        "employment": [
            {
                "employment_type": "employed",
                "employer_name": "Synthetic Employer",
                "job_title": "Analyst",
                "occupation_category": "finance",
                "industry": "financial_services",
                "duration_years": 2,
                "duration_months": 6,
                "annual_gross_income": "120000.00",
            }
        ],
    }
    payload: dict[str, object] = {
        "mortgage_request": {
            "mortgage_objective": "purchase",
            "requested_amount": "500000.00",
            "estimated_property_value": "750000.00",
        },
        "primary_borrower": borrower,
        "assets_complete": True,
        "liabilities_complete": True,
    }
    if with_co_borrower:
        co_borrower = dict(borrower)
        co_borrower.update(
            {
                "first_name": "Alex",
                "last_name": "Smith",
                "email": "alex@example.test",
                "relationship_to_primary": "spouse",
            }
        )
        payload["co_borrower"] = co_borrower
    return payload


def _create_review_user(
    session: Session,
    *,
    subject: str,
    role_code: str,
    active: bool = True,
    candidate_status: str | None = None,
) -> User:
    user = User(
        email=f"{subject}@example.test",
        display_name=f"Synthetic {subject}",
        is_active=active,
    )
    session.add(user)
    session.flush()
    session.add(
        UserIdentity(
            user_id=user.id,
            provider="supabase",
            provider_subject=subject,
            verified_at=datetime.now(UTC),
        )
    )
    role = session.query(Role).filter(Role.code == role_code).one_or_none()
    if role is None:
        role = Role(code=role_code, description=f"Synthetic {role_code}")
        session.add(role)
        session.flush()
    session.add(UserRole(user_id=user.id, role_id=role.id))
    if candidate_status is not None:
        session.add(Candidate(user_id=user.id, status=candidate_status))
    session.commit()
    return user


class TestBorrowerPhaseDRouteIntegration:
    @pytest.fixture
    def route_client(self, tmp_path: Path, monkeypatch):
        settings = _borrower_route_settings(tmp_path)
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        wording_text = "Synthetic local borrower consent wording for tests only."
        wording_digest = hashlib.sha256(wording_text.encode("utf-8")).hexdigest()

        def override_db():
            with SessionLocal() as session:
                if (
                    session.query(BorrowerConsentCatalog)
                    .filter(BorrowerConsentCatalog.consent_version == "test-v1")
                    .one_or_none()
                    is None
                ):
                    session.add(
                        BorrowerConsentCatalog(
                            consent_version="test-v1",
                            wording_digest=wording_digest,
                            wording_text=wording_text,
                            is_active=True,
                            effective_from=datetime.now(UTC),
                        )
                    )
                    session.commit()
                yield session

        from keeper_api.core.config import get_settings as _real_get_settings

        monkeypatch.setattr(_real_get_settings, "cache_clear", lambda: None)
        monkeypatch.setattr("keeper_api.core.config.get_settings", lambda: settings)
        monkeypatch.setattr(
            "keeper_api.api.routes.borrower_applications.get_settings",
            lambda: settings,
        )
        monkeypatch.setattr(
            "keeper_api.services.borrower_documents.build_malware_scanner",
            lambda _settings: _DeterministicBorrowerScanner(),
        )
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[_real_get_settings] = lambda: settings
        try:
            if hasattr(app.state, "borrower_crypto_state"):
                delattr(app.state, "borrower_crypto_state")
            with TestClient(
                app,
                base_url="https://localhost:8000",
                backend_options={"use_uvloop": True},
            ) as client:
                client._keeper_session_factory = SessionLocal
                client._keeper_consent_digest = wording_digest
                client._keeper_settings = settings
                yield client
        finally:
            app.dependency_overrides.clear()
            if hasattr(app.state, "borrower_crypto_state"):
                delattr(app.state, "borrower_crypto_state")

    def _headers(self) -> dict[str, str]:
        return {
            "Host": "localhost:8000",
            "Origin": "http://localhost:8000",
            "x-keeper-borrower-csrf": "1",
        }

    def _start(self, client: TestClient) -> str:
        resp = client.post(
            "/api/v1/borrower-applications/start",
            headers=self._headers(),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["application_id"]

    def test_start_cookie_satisfies_host_prefix_requirements(
        self, route_client: TestClient
    ) -> None:
        response = route_client.post(
            "/api/v1/borrower-applications/start",
            headers=self._headers(),
        )

        assert response.status_code == 201, response.text
        cookie = response.headers["set-cookie"]
        assert cookie.startswith("__Host-keeper-borrower-draft=")
        assert "; Secure" in cookie
        assert "; HttpOnly" in cookie
        assert "; Path=/" in cookie
        assert "; Domain=" not in cookie

    def test_invalid_sensitive_draft_returns_private_json_validation_errors(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        payload = _valid_submit_payload(with_co_borrower=True)
        primary_borrower = payload["primary_borrower"]
        co_borrower = payload["co_borrower"]
        assert isinstance(primary_borrower, dict)
        assert isinstance(co_borrower, dict)
        primary_borrower["sin"] = "123123123"
        primary_borrower["current_address"]["months_at_address"] = 12
        co_borrower["sin"] = "123456789"

        response = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=self._headers(),
            json={"expected_revision": 0, "payload": payload},
        )

        assert response.status_code == 422, response.text
        assert response.headers["content-type"] == "application/json"
        assert "123123123" not in response.text
        assert "123456789" not in response.text
        errors = response.json()["detail"]
        assert any(error["loc"] == ["primary_borrower", "sin"] for error in errors)
        assert all("input" not in error and "ctx" not in error for error in errors)

    def _save_full_payload(
        self,
        client: TestClient,
        application_id: str,
        *,
        with_co_borrower: bool = False,
    ) -> int:
        resp = client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=self._headers(),
            json={
                "expected_revision": 0,
                "payload": _valid_submit_payload(with_co_borrower=with_co_borrower),
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["revision"]

    def test_get_draft_returns_resumable_payload_without_sin(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        self._save_full_payload(
            route_client,
            application_id,
            with_co_borrower=True,
        )

        response = route_client.get(
            f"/api/v1/borrower-applications/{application_id}",
            headers=self._headers(),
        )

        assert response.status_code == 200, response.text
        assert "no-store" in response.headers["cache-control"]
        payload = response.json()["payload"]
        assert payload["mortgage_request"]["mortgage_objective"] == "purchase"
        assert payload["primary_borrower"]["first_name"] == "Jane"
        assert payload["co_borrower"]["first_name"] == "Alex"
        assert "sin" not in payload["primary_borrower"]
        assert "sin" not in payload["co_borrower"]

    def test_get_draft_response_includes_payload_revision(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)

        response = route_client.get(
            f"/api/v1/borrower-applications/{application_id}",
            headers=self._headers(),
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["payload_revision"] == revision
        assert body["revision"] == revision

    def test_submit_preserves_sin_across_later_section_revisions(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)

        later_save = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=self._headers(),
            json={
                "expected_revision": revision,
                "payload": {"additional_notes": "Synthetic later section save."},
            },
        )
        assert later_save.status_code == 200, later_save.text

        # Recreate the legacy partial-save defect: the newer row carried the
        # prior SIN ciphertext even though its AAD remained bound to the older
        # payload revision. Existing local drafts must remain recoverable.
        with route_client._keeper_session_factory() as session:
            payload_rows = (
                session.query(BorrowerApplicationPayload)
                .filter(BorrowerApplicationPayload.application_id == uuid.UUID(application_id))
                .order_by(BorrowerApplicationPayload.revision)
                .all()
            )
            first_payload, latest_payload = payload_rows
            latest_payload.encrypted_sin_ciphertext = first_payload.encrypted_sin_ciphertext
            latest_payload.encrypted_sin_nonce = first_payload.encrypted_sin_nonce
            session.commit()

        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": later_save.json()["revision"],
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["lifecycle_status"] == "submitted"

    def _submit_full_application(
        self,
        client: TestClient,
        *,
        with_document: bool = False,
    ) -> str:
        application_id = self._start(client)
        revision = self._save_full_payload(client, application_id)
        if with_document:
            from document_samples import valid_pdf

            upload = client.post(
                f"/api/v1/borrower-applications/{application_id}/documents",
                headers=self._headers(),
                data={"category": "property"},
                files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
            )
            assert upload.status_code == 201, upload.text
        resp = client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )
        assert resp.status_code == 200, resp.text
        return application_id

    def _auth_headers(self, subject: str, *, aal: str = "aal2") -> dict[str, str]:
        return {"X-Dev-Auth-Sub": subject, "X-Dev-Auth-AAL": aal}

    def test_upload_clean_pdf_records_metadata(self, route_client: TestClient) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["filename"] == "notice.pdf"
        assert resp.json()["scan_status"] == "clean"

        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            document = session.query(BorrowerDocument).one()
            assert str(document.application_id) == application_id
            assert document.mime_type == "application/pdf"
            assert document.size_bytes == len(valid_pdf())
            assert document.scan_status == "clean"
            assert document.uploaded_by == "borrower"
            assert document.minio_object_key.startswith("borrower/documents/")
            assert application_id not in document.minio_object_key
            assert "notice" not in document.minio_object_key

    def test_document_category_list_and_delete_contract(self, route_client: TestClient) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            started_expiry = session.get(
                BorrowerApplication, uuid.UUID(application_id)
            ).draft_expires_at
        uploaded = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "other", "description": "Synthetic supporting record"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert uploaded.status_code == 201, uploaded.text
        assert uploaded.json()["category"] == "other"
        assert uploaded.json()["description"] == "Synthetic supporting record"
        with session_factory() as session:
            uploaded_expiry = session.get(
                BorrowerApplication, uuid.UUID(application_id)
            ).draft_expires_at
        assert uploaded_expiry > started_expiry

        listed = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/draft-documents",
            headers=self._headers(),
        )
        assert listed.status_code == 200, listed.text
        assert "no-store" in listed.headers["cache-control"]
        assert listed.json()["items"] == [uploaded.json()]

        deleted = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/"
            f"{uploaded.json()['document_id']}",
            headers=self._headers(),
        )
        assert deleted.status_code == 204, deleted.text
        with session_factory() as session:
            deleted_expiry = session.get(
                BorrowerApplication, uuid.UUID(application_id)
            ).draft_expires_at
        assert deleted_expiry > uploaded_expiry
        assert (
            route_client.get(
                f"/api/v1/borrower-applications/{application_id}/draft-documents",
                headers=self._headers(),
            ).json()["items"]
            == []
        )
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            audit_events = (
                session.query(AuditEvent)
                .filter(AuditEvent.target_id == uuid.UUID(uploaded.json()["document_id"]))
                .order_by(AuditEvent.created_at.asc(), AuditEvent.id.asc())
                .all()
            )
            assert sorted(event.event_type for event in audit_events) == [
                "borrower_document_removed",
                "borrower_document_uploaded",
            ]
            audit_payload = json.dumps(
                [event.safe_metadata for event in audit_events], sort_keys=True
            )
            assert "notice.pdf" not in audit_payload
            assert "borrower/documents" not in audit_payload
            assert "capability" not in audit_payload

    def test_delete_metadata_failure_is_bounded_and_retryable(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        uploaded = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert uploaded.status_code == 201, uploaded.text
        document_id = uploaded.json()["document_id"]

        original_record = AuditService.record
        monkeypatch.setattr(
            AuditService,
            "record",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                RuntimeError("synthetic delete metadata failure")
            ),
        )
        failed = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/{document_id}",
            headers=self._headers(),
        )
        assert failed.status_code == 503, failed.text
        assert failed.json()["detail"] == "storage_unavailable"

        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            document = session.query(BorrowerDocument).one()
            assert document.deletion_pending_at is not None
        pending_list = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/draft-documents",
            headers=self._headers(),
        )
        assert pending_list.status_code == 200, pending_list.text
        assert [item["document_id"] for item in pending_list.json()["items"]] == [document_id]
        assert not any(
            path.is_file() for path in route_client._keeper_settings.local_storage_path.rglob("*")
        )

        monkeypatch.setattr(AuditService, "record", original_record)
        retried = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/{document_id}",
            headers=self._headers(),
        )
        assert retried.status_code == 204, retried.text
        with session_factory() as session:
            assert session.query(BorrowerDocument).count() == 0

    def test_submission_waits_for_pending_document_removal_recovery(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        uploaded = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert uploaded.status_code == 201, uploaded.text
        document_id = uploaded.json()["document_id"]

        original_record = AuditService.record
        monkeypatch.setattr(
            AuditService,
            "record",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                RuntimeError("synthetic delete metadata failure")
            ),
        )
        failed = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/{document_id}",
            headers=self._headers(),
        )
        assert failed.status_code == 503, failed.text
        monkeypatch.setattr(AuditService, "record", original_record)

        revision = self._save_full_payload(route_client, application_id)
        submit_body = {
            "consent_version": "test-v1",
            "consent_wording_digest": route_client._keeper_consent_digest,
            "borrower_coverage": "primary",
            "expected_revision": revision,
        }
        blocked = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json=submit_body,
        )
        assert blocked.status_code == 409, blocked.text
        assert blocked.json()["detail"] == "document_operation_pending"

        recovered = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/{document_id}",
            headers=self._headers(),
        )
        assert recovered.status_code == 204, recovered.text
        submitted = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json=submit_body,
        )
        assert submitted.status_code == 200, submitted.text

    def test_delete_object_failure_preserves_recoverable_pending_metadata(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from document_samples import valid_pdf
        from keeper_api.services import borrower_documents

        application_id = self._start(route_client)
        uploaded = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert uploaded.status_code == 201, uploaded.text
        document_id = uploaded.json()["document_id"]

        original_delete = borrower_documents.delete_borrower_object
        monkeypatch.setattr(
            borrower_documents,
            "delete_borrower_object",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                BorrowerDocumentStorageError("storage_unavailable")
            ),
        )
        failed = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/{document_id}",
            headers=self._headers(),
        )
        assert failed.status_code == 503, failed.text

        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            document = session.query(BorrowerDocument).one()
            assert document.deletion_pending_at is not None
        assert any(
            path.is_file() for path in route_client._keeper_settings.local_storage_path.rglob("*")
        )

        monkeypatch.setattr(borrower_documents, "delete_borrower_object", original_delete)
        recovered = route_client.delete(
            f"/api/v1/borrower-applications/{application_id}/draft-documents/{document_id}",
            headers=self._headers(),
        )
        assert recovered.status_code == 204, recovered.text
        with session_factory() as session:
            assert session.query(BorrowerDocument).count() == 0

    def test_other_description_and_extra_upload_field_are_rejected(
        self, route_client: TestClient
    ) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        missing = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "other"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert missing.status_code == 422
        extra = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property", "unexpected": "denied"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )
        assert extra.status_code == 422

    def test_active_consent_is_no_store(self, route_client: TestClient) -> None:
        application_id = self._start(route_client)
        response = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/consent",
            headers=self._headers(),
        )
        assert response.status_code == 200, response.text
        assert "no-store" in response.headers["cache-control"]
        assert response.json() == {
            "consent_version": "test-v1",
            "wording_digest": route_client._keeper_consent_digest,
            "wording_text": "Synthetic local borrower consent wording for tests only.",
        }

    def test_active_consent_excludes_future_and_expired_entries(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        now = datetime.now(UTC)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            session.add(
                BorrowerConsentCatalog(
                    consent_version="future-v2",
                    wording_digest="f" * 64,
                    wording_text="Synthetic future borrower consent wording for tests only.",
                    is_active=True,
                    effective_from=now + timedelta(days=1),
                )
            )
            session.commit()

        current = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/consent",
            headers=self._headers(),
        )
        assert current.status_code == 200, current.text
        assert current.json()["consent_version"] == "test-v1"

        with session_factory() as session:
            active = (
                session.query(BorrowerConsentCatalog)
                .filter(BorrowerConsentCatalog.consent_version == "test-v1")
                .one()
            )
            assert active is not None
            active.effective_to = now - timedelta(seconds=1)
            session.commit()
        unavailable = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/consent",
            headers=self._headers(),
        )
        assert unavailable.status_code == 503, unavailable.text
        assert unavailable.json()["detail"] == "consent_unavailable"

    def test_non_local_submission_requires_real_data_release_gate(
        self, route_client: TestClient
    ) -> None:
        started = route_client.post("/api/v1/borrower-applications/start", headers=self._headers())
        assert started.status_code == 201, started.text
        application_id = started.json()["application_id"]
        capability_header = next(
            value
            for value in started.headers.get_list("set-cookie")
            if value.startswith("__Host-keeper-borrower-draft=")
        )
        capability = capability_header.split(";", 1)[0].split("=", 1)[1]
        revision = self._save_full_payload(route_client, application_id)
        route_client._keeper_settings.app_env = "staging"
        route_client._keeper_settings.borrower_real_data_enabled = False
        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers={
                "Host": "apply.keeperfinancial.ca",
                "Origin": "https://apply.keeperfinancial.ca",
                "x-keeper-borrower-csrf": "1",
                "Cookie": f"__Host-keeper-borrower-draft={capability}",
            },
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )
        assert response.status_code == 503, response.text
        assert response.json()["detail"] == "real_data_submission_disabled"
        assert "__Host-keeper-borrower-draft=" not in response.headers.get("set-cookie", "")

    def test_non_local_submission_requires_explicitly_approved_consent(
        self, route_client: TestClient
    ) -> None:
        started = route_client.post("/api/v1/borrower-applications/start", headers=self._headers())
        assert started.status_code == 201, started.text
        application_id = started.json()["application_id"]
        capability_header = next(
            value
            for value in started.headers.get_list("set-cookie")
            if value.startswith("__Host-keeper-borrower-draft=")
        )
        capability = capability_header.split(";", 1)[0].split("=", 1)[1]
        revision = self._save_full_payload(route_client, application_id)
        wording = "Synthetic release wording awaiting owner approval."
        digest = hashlib.sha256(wording.encode()).hexdigest()
        with route_client._keeper_session_factory() as session:
            consent = session.query(BorrowerConsentCatalog).one()
            consent.wording_text = wording
            consent.wording_digest = digest
            session.commit()

        route_client._keeper_settings.app_env = "staging"
        route_client._keeper_settings.borrower_real_data_enabled = True
        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers={
                "Host": "apply.keeperfinancial.ca",
                "Origin": "https://apply.keeperfinancial.ca",
                "x-keeper-borrower-csrf": "1",
                "Cookie": f"__Host-keeper-borrower-draft={capability}",
            },
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )

        assert response.status_code == 503, response.text
        assert response.json()["detail"] == "real_data_submission_disabled"

        with route_client._keeper_session_factory() as session:
            consent = session.query(BorrowerConsentCatalog).one()
            consent.real_data_approved = True
            session.commit()
        route_client._keeper_settings.app_env = "local"
        approved = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )
        assert approved.status_code == 200, approved.text

    def test_submission_rejects_stale_consent_during_overlap(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        displayed = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/consent",
            headers=self._headers(),
        )
        assert displayed.status_code == 200, displayed.text
        old_consent = displayed.json()
        newer_wording = "Synthetic newer local borrower consent wording for tests only."
        newer_digest = hashlib.sha256(newer_wording.encode()).hexdigest()
        with route_client._keeper_session_factory() as session:
            session.add(
                BorrowerConsentCatalog(
                    consent_version="test-v2",
                    wording_digest=newer_digest,
                    wording_text=newer_wording,
                    is_active=True,
                    effective_from=datetime.now(UTC),
                )
            )
            session.commit()

        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": old_consent["consent_version"],
                "consent_wording_digest": old_consent["wording_digest"],
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )

        assert response.status_code == 422, response.text
        assert response.json()["detail"] == "invalid_consent"

    def test_upload_eicar_rejected(self, route_client: TestClient) -> None:
        from document_samples import eicar_bytes, valid_pdf

        application_id = self._start(route_client)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={
                "file": (
                    "notice.pdf",
                    valid_pdf(comment=eicar_bytes()),
                    "application/pdf",
                )
            },
        )
        assert resp.status_code == 422, resp.text
        assert resp.json()["detail"] == "malware_detected"

    def test_upload_metadata_failure_rolls_back_and_removes_encrypted_object(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        monkeypatch.setattr(
            "keeper_api.services.borrower_documents.AuditService.record",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                RuntimeError("synthetic metadata failure")
            ),
        )

        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )

        assert response.status_code == 503, response.text
        assert response.json()["detail"] == "storage_unavailable"
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            assert session.query(BorrowerDocument).count() == 0
        assert not any(
            path.is_file() for path in route_client._keeper_settings.local_storage_path.rglob("*")
        )

    @pytest.mark.parametrize(
        ("failure", "expected_detail"),
        [
            ("scanner", "scanner_unavailable"),
            ("storage", "storage_unavailable"),
        ],
    )
    def test_upload_scanner_and_storage_failures_leave_no_document_or_object(
        self,
        route_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        failure: str,
        expected_detail: str,
    ) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        if failure == "scanner":
            monkeypatch.setattr(
                "keeper_api.services.borrower_documents.build_malware_scanner",
                lambda _settings: (_ for _ in ()).throw(MalwareScannerUnavailable()),
            )
        else:
            monkeypatch.setattr(
                "keeper_api.services.borrower_documents._put_borrower_object",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    BorrowerDocumentStorageError("storage_unavailable")
                ),
            )

        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", valid_pdf(), "application/pdf")},
        )

        assert response.status_code == 503, response.text
        assert response.json()["detail"] == expected_detail
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            assert session.query(BorrowerDocument).count() == 0
            failure_event = (
                session.query(AuditEvent)
                .filter(
                    AuditEvent.event_type == "borrower_document_upload_result",
                    AuditEvent.target_id == uuid.UUID(application_id),
                )
                .one()
            )
            assert failure_event.safe_metadata == {
                "result": "failure",
                "reason": expected_detail,
            }
        assert not any(
            path.is_file() for path in route_client._keeper_settings.local_storage_path.rglob("*")
        )

    def test_upload_oversize_rejected_with_413(self, route_client: TestClient) -> None:
        application_id = self._start(route_client)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("large.pdf", b"x" * (25 * 1024 * 1024 + 1), "application/pdf")},
        )
        assert resp.status_code == 413, resp.text

    def test_exact_25_mib_is_accepted(self, route_client: TestClient) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        payload = valid_pdf(minimum_size=25 * 1024 * 1024)
        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("exact.pdf", payload, "application/pdf")},
        )
        assert response.status_code == 201, response.text
        assert response.json()["size_bytes"] == 25 * 1024 * 1024

    def test_document_count_and_narrowed_aggregate_limits(self, route_client: TestClient) -> None:
        from document_samples import valid_pdf

        settings = route_client._keeper_settings
        settings.borrower_max_document_count = 2
        settings.borrower_max_total_document_bytes = 1200
        application_id = self._start(route_client)
        payload = valid_pdf(minimum_size=700)
        first = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("first.pdf", payload, "application/pdf")},
        )
        assert first.status_code == 201, first.text
        aggregate = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "tax"},
            files={"file": ("second.pdf", payload, "application/pdf")},
        )
        assert aggregate.status_code == 413
        assert aggregate.json()["detail"] == "aggregate_size_limit"
        settings.borrower_max_total_document_bytes = 250 * 1024 * 1024
        second = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "tax"},
            files={"file": ("second.pdf", payload, "application/pdf")},
        )
        assert second.status_code == 201, second.text
        count = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "identification"},
            files={"file": ("third.pdf", payload, "application/pdf")},
        )
        assert count.status_code == 413
        assert count.json()["detail"] == "document_count_limit"

    def test_upload_wrong_mime_or_magic_rejected(self, route_client: TestClient) -> None:
        from document_samples import valid_pdf

        application_id = self._start(route_client)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.png", valid_pdf(), "image/png")},
        )
        assert resp.status_code == 422, resp.text

    def test_upload_capability_mismatch_hidden(self, route_client: TestClient) -> None:
        first_id = self._start(route_client)
        self._start(route_client)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{first_id}/documents",
            headers=self._headers(),
            data={"category": "property"},
            files={"file": ("notice.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
        )
        assert resp.status_code == 404, resp.text

    def test_submit_valid_consent_creates_snapshot_and_revokes_capability(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["lifecycle_status"] == "submitted"
        assert body["snapshot_id"]
        assert body["consent_record_id"]

        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application.lifecycle_status == "submitted"

    def test_review_queue_admin_only_and_omits_drafts(self, route_client: TestClient) -> None:
        submitted_id = self._submit_full_application(route_client)
        self._start(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-queue", role_code="brokerage_admin")
            _create_review_user(
                session,
                subject="agent-queue",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )

        admin = route_client.get(
            "/api/v1/borrower-applications/review-queue",
            headers=self._auth_headers("admin-queue"),
        )
        assert admin.status_code == 200, admin.text
        assert admin.json()["total"] == 1
        assert admin.json()["items"][0]["application_id"] == submitted_id
        assert admin.json()["items"][0]["lifecycle_status"] == "submitted"

        no_mfa = route_client.get(
            "/api/v1/borrower-applications/review-queue",
            headers=self._auth_headers("admin-queue", aal="aal1"),
        )
        assert no_mfa.status_code == 403

        agent = route_client.get(
            "/api/v1/borrower-applications/review-queue",
            headers=self._auth_headers("agent-queue"),
        )
        assert agent.status_code == 403

    def test_assignment_validates_agent_and_records_safe_evidence(
        self, route_client: TestClient
    ) -> None:
        application_id = self._submit_full_application(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            admin = _create_review_user(
                session,
                subject="admin-assign",
                role_code="brokerage_admin",
            )
            agent = _create_review_user(
                session,
                subject="agent-assign",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            inactive_agent = _create_review_user(
                session,
                subject="agent-inactive",
                role_code="agent",
                candidate_status=CandidateStatus.SUSPENDED.value,
            )
            agent_id = agent.id
            inactive_id = inactive_agent.id
            admin_id = admin.id

        invalid = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/assignment",
            headers=self._auth_headers("admin-assign"),
            json={"agent_user_id": str(inactive_id), "reason_category": "initial_assignment"},
        )
        assert invalid.status_code == 422

        missing_reason = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/assignment",
            headers=self._auth_headers("admin-assign"),
            json={"agent_user_id": str(agent_id), "reason_category": ""},
        )
        assert missing_reason.status_code == 422

        assigned = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/assignment",
            headers=self._auth_headers("admin-assign"),
            json={
                "agent_user_id": str(agent_id),
                "reason_category": "initial_assignment",
                "reason_detail": "Synthetic bounded assignment reason",
            },
        )
        assert assigned.status_code == 200, assigned.text
        assert assigned.json()["lifecycle_status"] == "under_review"
        assert assigned.json()["assigned_agent_id"] == str(agent_id)

        repeated = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/assignment",
            headers=self._auth_headers("admin-assign"),
            json={"agent_user_id": str(agent_id), "reason_category": "initial_assignment"},
        )
        assert repeated.status_code == 200

        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application.assigned_agent_id == agent_id
            history = (
                session.query(BorrowerAssignmentHistory)
                .filter(BorrowerAssignmentHistory.application_id == uuid.UUID(application_id))
                .all()
            )
            assert len(history) == 1
            assert history[0].actor_user_id == admin_id
            audit = (
                session.query(AuditEvent)
                .filter(AuditEvent.event_type == "borrower_application_assigned")
                .one()
            )
            assert audit.safe_metadata["assigned_agent_id"] == str(agent_id)
            assert "Synthetic bounded assignment reason" not in str(audit.safe_metadata)

    def test_internal_projection_admin_and_exact_agent_only(self, route_client: TestClient) -> None:
        application_id = self._submit_full_application(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-detail", role_code="brokerage_admin")
            assigned_agent = _create_review_user(
                session,
                subject="agent-detail",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            _create_review_user(
                session,
                subject="agent-wrong",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            application.assigned_agent_id = assigned_agent.id
            session.commit()

        admin = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/internal",
            headers=self._auth_headers("admin-detail"),
        )
        assert admin.status_code == 200, admin.text
        body = admin.json()
        assert body["primary_borrower"]["sin"]["display"] == "*** *** 286"
        assert "046454286" not in json.dumps(body)

        agent = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/internal",
            headers=self._auth_headers("agent-detail"),
        )
        assert agent.status_code == 200, agent.text

        wrong = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/internal",
            headers=self._auth_headers("agent-wrong"),
        )
        assert wrong.status_code == 404

        no_mfa = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/internal",
            headers=self._auth_headers("agent-detail", aal="aal1"),
        )
        assert no_mfa.status_code == 403

    def test_document_metadata_and_download_are_authorized_and_decrypted(
        self, route_client: TestClient
    ) -> None:
        from document_samples import valid_pdf

        application_id = self._submit_full_application(route_client, with_document=True)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-docs", role_code="brokerage_admin")
            assigned_agent = _create_review_user(
                session,
                subject="agent-docs",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            _create_review_user(
                session,
                subject="agent-docs-wrong",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            application.assigned_agent_id = assigned_agent.id
            session.commit()

        metadata = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/documents",
            headers=self._auth_headers("agent-docs"),
        )
        assert metadata.status_code == 200, metadata.text
        item = metadata.json()["items"][0]
        assert item["filename"] == "notice.pdf"
        assert "object_key" not in item
        assert "minio" not in json.dumps(item).lower()

        downloaded = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/documents/{item['document_id']}/download",
            headers=self._auth_headers("agent-docs"),
        )
        assert downloaded.status_code == 200, downloaded.text
        assert downloaded.content == valid_pdf()
        assert downloaded.headers["cache-control"] == "private, no-store"
        assert downloaded.headers["x-content-type-options"] == "nosniff"
        assert downloaded.headers["content-disposition"].startswith("attachment;")

        wrong = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/documents/{item['document_id']}/download",
            headers=self._auth_headers("agent-docs-wrong"),
        )
        assert wrong.status_code == 404

    def test_document_download_denies_tampered_or_missing_object(
        self, route_client: TestClient
    ) -> None:
        application_id = self._submit_full_application(route_client, with_document=True)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-tamper", role_code="brokerage_admin")
            document = session.query(BorrowerDocument).one()
            document.minio_object_key = "borrower/documents/missing"
            document_id = document.id
            session.commit()

        resp = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/documents/{document_id}/download",
            headers=self._auth_headers("admin-tamper"),
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "document not found"

    def test_sin_reveal_allows_exact_agent_and_keeps_audit_safe(
        self, route_client: TestClient
    ) -> None:
        application_id = self._submit_full_application(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            assigned_agent = _create_review_user(
                session,
                subject="agent-reveal",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            _create_review_user(
                session,
                subject="agent-reveal-wrong",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            application.assigned_agent_id = assigned_agent.id
            session.commit()

        revealed = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/sin/reveal",
            headers=self._auth_headers("agent-reveal"),
            json={"reason_category": "credit_review"},
        )
        assert revealed.status_code == 200, revealed.text
        assert revealed.json()["sin"] == "046454286"

        denied = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/sin/reveal",
            headers=self._auth_headers("agent-reveal-wrong"),
            json={"reason_category": "credit_review"},
        )
        assert denied.status_code == 404

        invalid_reason = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/sin/reveal",
            headers=self._auth_headers("agent-reveal"),
            json={"reason_category": "curiosity"},
        )
        assert invalid_reason.status_code == 422

        with session_factory() as session:
            audit_payload = json.dumps(
                [
                    {
                        "role": row.actor_role,
                        "reason": row.reason_category,
                        "result": row.result,
                    }
                    for row in session.query(BorrowerSinRevealAudit).all()
                ],
                sort_keys=True,
            )
            assert "046454286" not in audit_payload
            assert "agent" in audit_payload

    def test_submit_same_request_retry_returns_original_result_once(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        capability = route_client.cookies.get("__Host-keeper-borrower-draft")
        assert capability
        body = {
            "consent_version": "test-v1",
            "consent_wording_digest": route_client._keeper_consent_digest,
            "borrower_coverage": "primary",
            "expected_revision": revision,
        }
        first = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json=body,
        )
        assert first.status_code == 200, first.text
        assert "__Host-keeper-borrower-draft=" in first.headers["set-cookie"]
        assert "Max-Age=0" in first.headers["set-cookie"]
        second = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers={
                **self._headers(),
                "Cookie": f"__Host-keeper-borrower-draft={capability}",
            },
            json=body,
        )
        assert second.status_code == 200, second.text
        assert "Max-Age=0" in second.headers["set-cookie"]
        assert second.json() == first.json()
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            assert session.query(BorrowerApplicationSnapshot).count() == 1
            assert session.query(BorrowerConsentRecord).count() == 1
            assert (
                session.query(BorrowerApplicationStatusHistory)
                .filter(BorrowerApplicationStatusHistory.to_status == "submitted")
                .count()
                == 1
            )
            submission_audits = (
                session.query(AuditEvent)
                .filter(AuditEvent.event_type == "borrower_application_submitted")
                .all()
            )
            assert len(submission_audits) == 1
            assert submission_audits[0].safe_metadata == {
                "result": "success",
                "submission_revision": revision,
            }

    def test_submit_post_lock_same_request_converges_to_original_result(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        body = {
            "consent_version": "test-v1",
            "consent_wording_digest": route_client._keeper_consent_digest,
            "borrower_coverage": "primary",
            "expected_revision": revision,
        }
        first = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json=body,
        )
        assert first.status_code == 200, first.text

        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application is not None
            replay_application, replay_snapshot, replay_consent = submit_borrower_application(
                db=session,
                crypto_state=route_client.app.state.borrower_crypto_state,
                application_id=application.id,
                capability_session_id=application.capability_session_id,
                expected_revision=revision,
                consent_version=body["consent_version"],
                consent_wording_digest=body["consent_wording_digest"],
                borrower_coverage=body["borrower_coverage"],
                settings=route_client._keeper_settings,
            )

        assert str(replay_application.id) == first.json()["application_id"]
        assert str(replay_snapshot.id) == first.json()["snapshot_id"]
        assert str(replay_consent.id) == first.json()["consent_record_id"]

    def test_submit_retry_returns_original_result_after_review_has_started(
        self, route_client: TestClient
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        capability = route_client.cookies.get("__Host-keeper-borrower-draft")
        assert capability
        body = {
            "consent_version": "test-v1",
            "consent_wording_digest": route_client._keeper_consent_digest,
            "borrower_coverage": "primary",
            "expected_revision": revision,
        }
        first = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json=body,
        )
        assert first.status_code == 200, first.text

        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application is not None
            application.lifecycle_status = BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value
            session.commit()

        retry = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers={
                **self._headers(),
                "Cookie": f"__Host-keeper-borrower-draft={capability}",
            },
            json=body,
        )
        assert retry.status_code == 200, retry.text
        assert retry.json() == first.json()

    def test_submit_metadata_failure_rolls_back_and_removes_snapshot_object(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        monkeypatch.setattr(
            "keeper_api.services.borrower_applications.AuditService.record",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                RuntimeError("synthetic submission metadata failure")
            ),
        )

        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )

        assert response.status_code == 503, response.text
        assert response.json()["detail"] == "submission_storage_unavailable"
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application is not None
            assert application.lifecycle_status == "draft"
            assert application.capability_revoked_at is None
            assert session.query(BorrowerApplicationSnapshot).count() == 0
            assert session.query(BorrowerConsentRecord).count() == 0
        assert not any(
            path.is_file() for path in route_client._keeper_settings.local_storage_path.rglob("*")
        )

    def test_submit_snapshot_storage_failure_returns_bounded_error(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        monkeypatch.setattr(
            "keeper_api.services.borrower_documents._put_borrower_object",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                BorrowerDocumentStorageError("storage_unavailable")
            ),
        )

        response = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )

        assert response.status_code == 503, response.text
        assert response.json()["detail"] == "submission_storage_unavailable"
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application is not None
            assert application.lifecycle_status == "draft"
            assert application.capability_revoked_at is None
            assert session.query(BorrowerApplicationSnapshot).count() == 0
            assert session.query(BorrowerConsentRecord).count() == 0

    def test_submit_wrong_revision_returns_409(self, route_client: TestClient) -> None:
        application_id = self._start(route_client)
        self._save_full_payload(route_client, application_id)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": 0,
            },
        )
        assert resp.status_code == 409, resp.text

    def test_submit_co_borrower_requires_both_coverage(self, route_client: TestClient) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id, with_co_borrower=True)
        resp = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )
        assert resp.status_code == 422, resp.text

    def test_patch_after_submit_rejected(self, route_client: TestClient) -> None:
        application_id = self._start(route_client)
        revision = self._save_full_payload(route_client, application_id)
        capability = route_client.cookies.get("__Host-keeper-borrower-draft")
        assert capability
        submit = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": route_client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": revision,
            },
        )
        assert submit.status_code == 200, submit.text
        resp = route_client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers={
                **self._headers(),
                "Cookie": f"__Host-keeper-borrower-draft={capability}",
            },
            json={
                "expected_revision": revision,
                "payload": {"additional_notes": "late change"},
            },
        )
        assert resp.status_code == 409, resp.text
        assert resp.json()["detail"] == "already_submitted"

    def test_web_shaped_subject_property_partial_merges(self, route_client: TestClient) -> None:
        application_id = self._start(route_client)
        headers = self._headers()
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

    def _submit_full_application_with_financials(self, client: TestClient) -> str:
        application_id = self._start(client)
        payload = _valid_submit_payload()
        payload["subject_property"] = {
            "address": "123 Main St",
            "city": "Toronto",
            "province": "ON",
            "postal_code": "M5V 2T6",
            "property_type": "single_family",
            "property_style": "detached",
            "occupancy": "owner_occupied",
        }
        payload["assets"] = [
            {"asset_type": "chequing", "value": "25000.00", "description": "Chequing"}
        ]
        payload["liabilities"] = [
            {
                "liability_type": "credit_card",
                "current_balance": "4000.00",
                "payment_amount": "200.00",
                "payment_frequency": "monthly",
            }
        ]
        payload["other_properties"] = []
        payload["additional_notes"] = "Synthetic full-data note"
        save = client.patch(
            f"/api/v1/borrower-applications/{application_id}",
            headers=self._headers(),
            json={"expected_revision": 0, "payload": payload},
        )
        assert save.status_code == 200, save.text
        resp = client.post(
            f"/api/v1/borrower-applications/{application_id}/submit",
            headers=self._headers(),
            json={
                "consent_version": "test-v1",
                "consent_wording_digest": client._keeper_consent_digest,
                "borrower_coverage": "primary",
                "expected_revision": save.json()["revision"],
            },
        )
        assert resp.status_code == 200, resp.text
        return application_id

    def test_agent_full_projection_returns_unmasked_sin_and_financials(
        self, route_client: TestClient
    ) -> None:
        application_id = self._submit_full_application_with_financials(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            agent = _create_review_user(
                session,
                subject="agent-full",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            agent_id = agent.id
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            application.assigned_agent_id = agent_id
            session.commit()

        response = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/agent",
            headers=self._auth_headers("agent-full"),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["primary_borrower"]["sin"] == "046454286"
        assert body["subject_property"]["city"] == "Toronto"
        assert body["assets"][0]["value"] == "25000.00"
        assert body["liabilities"][0]["current_balance"] == "4000.00"
        assert body["additional_notes"] == "Synthetic full-data note"

        with session_factory() as session:
            audit = (
                session.query(AuditEvent)
                .filter(AuditEvent.event_type == "borrower_application_agent_viewed")
                .one()
            )
            assert audit.safe_metadata["reviewer_role"] == "agent"

    def test_agent_full_projection_denied_for_wrong_agent(self, route_client: TestClient) -> None:
        application_id = self._submit_full_application_with_financials(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(
                session,
                subject="agent-owner",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            wrong = _create_review_user(
                session,
                subject="agent-intruder",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            application.assigned_agent_id = wrong.id
            session.commit()

        response = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/agent",
            headers=self._auth_headers("agent-owner"),
        )
        assert response.status_code == 404

    def test_admin_internal_projection_remains_masked_with_full_data(
        self, route_client: TestClient
    ) -> None:
        application_id = self._submit_full_application_with_financials(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-masked", role_code="brokerage_admin")
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            application.assigned_agent_id = _create_review_user(
                session,
                subject="agent-masked",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            ).id
            session.commit()

        response = route_client.get(
            f"/api/v1/borrower-applications/{application_id}/internal",
            headers=self._auth_headers("admin-masked"),
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["primary_borrower"]["sin"]["display"] == "*** *** 286"
        assert "046454286" not in json.dumps(body)
        assert body.get("assets") is None
        assert body.get("liabilities") is None
        assert body.get("subject_property") is None

    def test_agent_assigned_list_and_email_notification(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from keeper_api.services import borrower_notifications

        sent: list[dict[str, str]] = []

        def fake_send(*, settings, agent_name, agent_email, application_id):
            sent.append(
                {
                    "email": agent_email,
                    "name": agent_name,
                    "application_id": application_id,
                }
            )
            return True

        monkeypatch.setattr(borrower_notifications, "send_assignment_email", fake_send)

        application_id = self._submit_full_application(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-notify", role_code="brokerage_admin")
            agent = _create_review_user(
                session,
                subject="agent-notify",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            agent_id = agent.id

        assign = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/assignment",
            headers=self._auth_headers("admin-notify"),
            json={
                "agent_user_id": str(agent_id),
                "reason_category": "initial_assignment",
            },
        )
        assert assign.status_code == 200, assign.text
        assert len(sent) == 1
        assert sent[0]["email"] == "agent-notify@example.test"
        assert sent[0]["application_id"] == application_id

        list_resp = route_client.get(
            "/api/v1/borrower-applications/agent/assigned",
            headers=self._auth_headers("agent-notify"),
        )
        assert list_resp.status_code == 200, list_resp.text
        items = list_resp.json()["items"]
        assert len(items) == 1
        assert items[0]["application_id"] == application_id

    def test_assignment_email_failure_is_non_fatal(
        self, route_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from keeper_api.services import borrower_notifications

        def fake_send(*, settings, agent_name, agent_email, application_id):
            raise RuntimeError("smtp down")

        monkeypatch.setattr(borrower_notifications, "send_assignment_email", fake_send)

        application_id = self._submit_full_application(route_client)
        session_factory = route_client._keeper_session_factory
        with session_factory() as session:
            _create_review_user(session, subject="admin-emailfail", role_code="brokerage_admin")
            agent = _create_review_user(
                session,
                subject="agent-emailfail",
                role_code="agent",
                candidate_status=CandidateStatus.ACTIVE.value,
            )
            agent_id = agent.id

        assign = route_client.post(
            f"/api/v1/borrower-applications/{application_id}/assignment",
            headers=self._auth_headers("admin-emailfail"),
            json={
                "agent_user_id": str(agent_id),
                "reason_category": "initial_assignment",
            },
        )
        assert assign.status_code == 200, assign.text
        with session_factory() as session:
            application = session.get(BorrowerApplication, uuid.UUID(application_id))
            assert application.assigned_agent_id == agent_id
