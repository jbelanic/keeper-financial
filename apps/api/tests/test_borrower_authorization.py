from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from keeper_api.db.base import Base
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerApplicationSnapshot,
)
from keeper_api.models.domain import Candidate, Role, User, UserRole
from keeper_api.models.statuses import CandidateStatus
from keeper_api.services.auth import Principal
from keeper_api.services.borrower_applications import (
    create_consent_record,
    start_borrower_application,
)
from keeper_api.services.borrower_authorization import (
    extract_capability_from_cookie,
    require_admin_borrower_access,
    require_borrower_feature_enabled,
    require_internal_agent_access,
    resolve_agent_from_slug,
    validate_assignment_target,
    validate_borrower_origin,
    verify_borrower_capability,
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


def add_submission_evidence(db: Session, application_id: uuid.UUID) -> None:
    snapshot = BorrowerApplicationSnapshot(
        application_id=application_id,
        submission_revision=1,
        key_id="v1",
        nonce=os.urandom(12),
        ciphertext_hash="abc123",
        plaintext_hash="def456",
        object_key="snapshots/test.key",
        size_bytes=1024,
    )
    db.add(snapshot)
    db.flush()

    application = db.get(BorrowerApplication, application_id)
    assert application is not None
    create_consent_record(
        db=db,
        application_id=application_id,
        submission_revision=1,
        consent_version="v1.0",
        wording_digest="abc123",
        borrower_coverage="primary_only",
        borrower_count=1,
        capture_source="borrower_draft",
        capability_session_id=application.capability_session_id,
        acknowledged_at=datetime.now(UTC),
    )


@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self, method="GET", headers=None, cookies=None):
            self.method = method
            self.headers = headers or {}
            self.cookies = cookies or {}

    return MockRequest


class TestValidateBorrowerOrigin:
    def test_valid_origin_get(self, mock_request) -> None:
        request = mock_request(
            method="GET",
            headers={"host": "apply.keeperfinancial.ca"},
        )

        class MockSettings:
            app_env = "production"

        validate_borrower_origin(request, MockSettings())

    def test_valid_origin_post(self, mock_request) -> None:
        request = mock_request(
            method="POST",
            headers={
                "host": "apply.keeperfinancial.ca",
                "origin": "https://apply.keeperfinancial.ca",
                "x-keeper-borrower-csrf": "1",
            },
        )

        class MockSettings:
            app_env = "production"

        validate_borrower_origin(request, MockSettings())

    def test_invalid_host(self, mock_request) -> None:
        request = mock_request(
            method="GET",
            headers={"host": "evil.com"},
        )

        class MockSettings:
            app_env = "production"

        with pytest.raises(HTTPException) as exc_info:
            validate_borrower_origin(request, MockSettings())
        assert exc_info.value.status_code == 403

    def test_invalid_origin_post(self, mock_request) -> None:
        request = mock_request(
            method="POST",
            headers={
                "host": "apply.keeperfinancial.ca",
                "origin": "https://evil.com",
                "x-keeper-borrower-csrf": "1",
            },
        )

        class MockSettings:
            app_env = "production"

        with pytest.raises(HTTPException) as exc_info:
            validate_borrower_origin(request, MockSettings())
        assert exc_info.value.status_code == 403

    def test_missing_csrf_header(self, mock_request) -> None:
        request = mock_request(
            method="POST",
            headers={
                "host": "apply.keeperfinancial.ca",
                "origin": "https://apply.keeperfinancial.ca",
            },
        )

        class MockSettings:
            app_env = "production"

        with pytest.raises(HTTPException) as exc_info:
            validate_borrower_origin(request, MockSettings())
        assert exc_info.value.status_code == 403


class TestRequireBorrowerFeatureEnabled:
    def test_feature_enabled(self) -> None:
        class MockSettings:
            borrower_application_enabled = True

        require_borrower_feature_enabled(MockSettings())

    def test_feature_disabled(self) -> None:
        class MockSettings:
            borrower_application_enabled = False

        with pytest.raises(HTTPException) as exc_info:
            require_borrower_feature_enabled(MockSettings())
        assert exc_info.value.status_code == 503


class TestExtractCapabilityFromCookie:
    def test_extract_capability(self, mock_request) -> None:
        request = mock_request(
            headers={"cookie": "__Host-keeper-borrower-draft=test-capability-value"},
        )

        capability = extract_capability_from_cookie(request)
        assert capability == "test-capability-value"

    def test_extract_capability_missing(self, mock_request) -> None:
        request = mock_request(cookies={})

        capability = extract_capability_from_cookie(request)
        assert capability is None


class TestVerifyBorrowerCapability:
    def test_valid_capability(self, db_session: Session, crypto_state: BorrowerCryptoState) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        ctx = verify_borrower_capability(
            db_session,
            crypto_state,
            application.id,
            capability,
        )

        assert ctx.application_id == application.id
        assert ctx.capability_session_id == application.capability_session_id
        assert ctx.revision == 0
        assert ctx.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT

    def test_invalid_capability(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_borrower_capability(
                db_session,
                crypto_state,
                application.id,
                "invalid-capability",
            )
        assert exc_info.value.status_code == 404

    def test_nonexistent_application(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            verify_borrower_capability(
                db_session,
                crypto_state,
                uuid.uuid4(),
                "test-capability",
            )
        assert exc_info.value.status_code == 404

    def test_revoked_capability(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        from keeper_api.services.borrower_applications import transition_lifecycle

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

        with pytest.raises(HTTPException) as exc_info:
            verify_borrower_capability(
                db_session,
                crypto_state,
                application.id,
                capability,
            )
        assert exc_info.value.status_code == 404


class TestRequireInternalAgentAccess:
    def test_valid_agent_access(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.ACTIVE.value,
        )
        db_session.add(candidate)
        db_session.flush()

        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        from keeper_api.services.borrower_applications import transition_lifecycle

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

        add_submission_evidence(db_session, application.id)
        application.assigned_agent_id = user.id
        db_session.commit()

        principal = Principal(
            user_id=user.id,
            identity_subject=str(uuid.uuid4()),
            verified_at=datetime.now(UTC),
            roles=frozenset(["agent"]),
            is_active=True,
            aal="aal2",
            candidate_id=candidate.id,
            candidate_status=CandidateStatus.ACTIVE,
        )

        class MockSettings:
            require_admin_mfa = False

        result = require_internal_agent_access(
            principal,
            application.id,
            db_session,
            MockSettings(),
        )

        assert result.user_id == user.id

    def test_unassigned_agent_access_denied(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.ACTIVE.value,
        )
        db_session.add(candidate)
        db_session.flush()

        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        from keeper_api.services.borrower_applications import transition_lifecycle

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

        add_submission_evidence(db_session, application.id)
        principal = Principal(
            user_id=user.id,
            identity_subject=str(uuid.uuid4()),
            verified_at=datetime.now(UTC),
            roles=frozenset(["agent"]),
            is_active=True,
            aal="aal2",
            candidate_id=candidate.id,
            candidate_status=CandidateStatus.ACTIVE,
        )

        class MockSettings:
            require_admin_mfa = False

        with pytest.raises(HTTPException) as exc_info:
            require_internal_agent_access(
                principal,
                application.id,
                db_session,
                MockSettings(),
            )
        assert exc_info.value.status_code == 404

    def test_inactive_agent_access_denied(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.SUSPENDED.value,
        )
        db_session.add(candidate)
        db_session.flush()

        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        from keeper_api.services.borrower_applications import transition_lifecycle

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

        add_submission_evidence(db_session, application.id)
        application.assigned_agent_id = user.id
        db_session.commit()

        principal = Principal(
            user_id=user.id,
            identity_subject=str(uuid.uuid4()),
            verified_at=datetime.now(UTC),
            roles=frozenset(["agent"]),
            is_active=True,
            aal="aal2",
            candidate_id=candidate.id,
            candidate_status=CandidateStatus.SUSPENDED,
        )

        class MockSettings:
            require_admin_mfa = False

        with pytest.raises(HTTPException) as exc_info:
            require_internal_agent_access(
                principal,
                application.id,
                db_session,
                MockSettings(),
            )
        assert exc_info.value.status_code == 403


class TestRequireAdminBorrowerAccess:
    def test_valid_admin_access(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        user = User(
            id=uuid.uuid4(),
            email="admin@test.com",
            display_name="Test Admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="brokerage_admin",
            description="Admin role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)
        db_session.flush()

        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        from keeper_api.services.borrower_applications import transition_lifecycle

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

        add_submission_evidence(db_session, application.id)
        principal = Principal(
            user_id=user.id,
            identity_subject=str(uuid.uuid4()),
            verified_at=datetime.now(UTC),
            roles=frozenset(["brokerage_admin"]),
            is_active=True,
            aal="aal2",
            candidate_id=None,
            candidate_status=None,
        )

        class MockSettings:
            require_admin_mfa = False

        result = require_admin_borrower_access(
            principal,
            application.id,
            db_session,
            MockSettings(),
        )

        assert result.user_id == user.id

    def test_admin_without_aal2_denied(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        user = User(
            id=uuid.uuid4(),
            email="admin@test.com",
            display_name="Test Admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="brokerage_admin",
            description="Admin role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)
        db_session.flush()

        application, capability = start_borrower_application(
            db=db_session,
            crypto_state=crypto_state,
            settings=None,
        )

        from keeper_api.services.borrower_applications import transition_lifecycle

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

        principal = Principal(
            user_id=user.id,
            identity_subject=str(uuid.uuid4()),
            verified_at=datetime.now(UTC),
            roles=frozenset(["brokerage_admin"]),
            is_active=True,
            aal="aal1",
            candidate_id=None,
            candidate_status=None,
        )

        class MockSettings:
            require_admin_mfa = False

        with pytest.raises(HTTPException) as exc_info:
            require_admin_borrower_access(
                principal,
                application.id,
                db_session,
                MockSettings(),
            )
        assert exc_info.value.status_code == 403


class TestValidateAssignmentTarget:
    def test_valid_assignment_target(self, db_session: Session) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.ACTIVE.value,
        )
        db_session.add(candidate)
        db_session.flush()

        validate_assignment_target(db_session, user.id)

    def test_invalid_assignment_target_inactive_user(self, db_session: Session) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=False,
        )
        db_session.add(user)
        db_session.flush()

        with pytest.raises(HTTPException) as exc_info:
            validate_assignment_target(db_session, user.id)
        assert exc_info.value.status_code == 422

    def test_invalid_assignment_target_no_agent_role(self, db_session: Session) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        with pytest.raises(HTTPException) as exc_info:
            validate_assignment_target(db_session, user.id)
        assert exc_info.value.status_code == 422

    def test_invalid_assignment_target_suspended_candidate(self, db_session: Session) -> None:
        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.SUSPENDED.value,
        )
        db_session.add(candidate)
        db_session.flush()

        with pytest.raises(HTTPException) as exc_info:
            validate_assignment_target(db_session, user.id)
        assert exc_info.value.status_code == 422


class TestResolveAgentFromSlug:
    def test_resolve_agent_from_slug(self, db_session: Session) -> None:
        from keeper_api.models.domain import AgentProfile

        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.ACTIVE.value,
        )
        db_session.add(candidate)
        db_session.flush()

        profile = AgentProfile(
            user_id=user.id,
            slug="test-agent",
            licensed_name="Test Agent",
            approved_title="Agent",
            licence_number="L12345",
            status="published",
        )
        db_session.add(profile)
        db_session.flush()

        agent_id = resolve_agent_from_slug(db_session, "test-agent")
        assert agent_id == user.id

    def test_resolve_agent_from_slug_not_found(self, db_session: Session) -> None:
        agent_id = resolve_agent_from_slug(db_session, "nonexistent-slug")
        assert agent_id is None

    def test_resolve_agent_from_slug_inactive_user(self, db_session: Session) -> None:
        from keeper_api.models.domain import AgentProfile

        user = User(
            id=uuid.uuid4(),
            email="agent@test.com",
            display_name="Test Agent",
            is_active=False,
        )
        db_session.add(user)
        db_session.flush()

        role = Role(
            id=uuid.uuid4(),
            code="agent",
            description="Agent role",
        )
        db_session.add(role)
        db_session.flush()

        user_role = UserRole(
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(user_role)

        candidate = Candidate(
            user_id=user.id,
            status=CandidateStatus.ACTIVE.value,
        )
        db_session.add(candidate)
        db_session.flush()

        profile = AgentProfile(
            user_id=user.id,
            slug="test-agent",
            licensed_name="Test Agent",
            approved_title="Agent",
            licence_number="L12345",
            status="published",
        )
        db_session.add(profile)
        db_session.flush()

        agent_id = resolve_agent_from_slug(db_session, "test-agent")
        assert agent_id is None
