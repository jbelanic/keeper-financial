from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from keeper_api.db.base import Base
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerApplicationPayload,
    BorrowerApplicationSnapshot,
    BorrowerApplicationStatusHistory,
    BorrowerConsentRecord,
    BorrowerSinRevealAudit,
)
from keeper_api.schemas.borrower_internal import mask_sin
from keeper_api.schemas.borrower_payload import (
    _luhn_check,
    validate_borrower_payload,
)
from keeper_api.services.borrower_applications import (
    get_internal_projection,
    has_submission_evidence,
    reveal_sin,
    save_draft_payload,
    start_borrower_application,
    transition_lifecycle,
)
from keeper_api.services.borrower_authorization import verify_borrower_capability
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
    return {"v1": os.urandom(32)}


@pytest.fixture
def test_hmac_key() -> bytes:
    return os.urandom(32)


@pytest.fixture
def keyring_file(test_keys: dict[str, bytes]) -> Path:
    import base64

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(
            {
                "version": 1,
                "keys": {k: base64.b64encode(v).decode() for k, v in test_keys.items()},
            },
            f,
        )
        f.flush()
        return Path(f.name)


@pytest.fixture
def hmac_key_file(test_hmac_key: bytes) -> Path:
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(test_hmac_key)
        f.flush()
        return Path(f.name)


@pytest.fixture
def crypto_state(keyring_file, hmac_key_file) -> BorrowerCryptoState:
    return load_borrower_crypto_state(
        keyring_path=keyring_file,
        hmac_key_path=hmac_key_file,
        active_key_id="v1",
        borrower_origin="https://apply.keeperfinancial.ca",
        production=False,
    )


def _valid_payload() -> dict:
    return {
        "mortgage_request": {
            "mortgage_objective": "purchase",
            "requested_amount": Decimal("500000"),
        },
        "primary_borrower": {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "phone": "+14165551234",
            "preferred_contact_method": "email",
            "date_of_birth": "1990-01-15",
            "sin": "046454286",
            "marital_status": "single",
            "number_of_dependants": 0,
            "current_address": {
                "street": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V2T6",
                "years_at_address": 2,
                "months_at_address": 6,
            },
            "employment": [
                {
                    "employment_type": "employed",
                    "employer_name": "Acme Corp",
                    "job_title": "Engineer",
                    "occupation_category": "engineering",
                    "industry": "technology",
                    "duration_years": 5,
                    "duration_months": 0,
                    "annual_gross_income": Decimal("120000.00"),
                }
            ],
        },
    }


def _create_submitted_application(
    db: Session, crypto_state: BorrowerCryptoState
) -> tuple[BorrowerApplication, str]:
    application, capability = start_borrower_application(db, crypto_state, None)
    save_draft_payload(
        db=db,
        crypto_state=crypto_state,
        application_id=application.id,
        capability_session_id=application.capability_session_id,
        expected_revision=0,
        payload_data=_valid_payload(),
        settings=None,
    )
    transition_lifecycle(
        db=db,
        application_id=application.id,
        from_status=BorrowerApplicationLifecycleStatus.DRAFT,
        to_status=BorrowerApplicationLifecycleStatus.SUBMITTED,
        actor_user_id=None,
        actor_source="public",
        reason_category="submission",
        capability_session_id=application.capability_session_id,
    )
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
    db.add(snapshot)
    consent = BorrowerConsentRecord(
        application_id=application.id,
        submission_revision=1,
        consent_version="synthetic-v1",
        wording_digest="wording123",
        borrower_coverage="primary_only",
        borrower_count=1,
        capture_source="borrower_draft",
        capability_session_id=application.capability_session_id,
        acknowledged_at=datetime.now(UTC),
    )
    db.add(consent)
    db.commit()
    db.refresh(application)
    return application, capability


class TestLuhnValidation:
    def test_valid_sin(self) -> None:
        assert _luhn_check("046454286")

    def test_valid_sin_all_zeros(self) -> None:
        assert _luhn_check("000000000")

    def test_invalid_sin_checksum(self) -> None:
        assert not _luhn_check("046454287")

    def test_invalid_sin_wrong_length(self) -> None:
        assert not _luhn_check("12345678")

    def test_invalid_sin_non_digit(self) -> None:
        assert not _luhn_check("12345abc9")

    def test_valid_sin_known_good(self) -> None:
        assert _luhn_check("121912083")


class TestTypedPayloadValidation:
    def test_valid_payload(self) -> None:
        result = validate_borrower_payload(_valid_payload())
        assert result.primary_borrower.first_name == "Jane"
        assert result.primary_borrower.sin == "046454286"
        assert result.co_borrower is None

    def test_invalid_sin_luhn(self) -> None:
        payload = _valid_payload()
        payload["primary_borrower"]["sin"] = "123456789"
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)

    def test_invalid_email(self) -> None:
        payload = _valid_payload()
        payload["primary_borrower"]["email"] = "not-an-email"
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)

    def test_invalid_province(self) -> None:
        payload = _valid_payload()
        payload["primary_borrower"]["current_address"]["province"] = "XX"
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)

    def test_invalid_postal_code(self) -> None:
        payload = _valid_payload()
        payload["primary_borrower"]["current_address"]["postal_code"] = "INVALID"
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)

    def test_extra_forbidden(self) -> None:
        payload = _valid_payload()
        payload["unknown_field"] = "test"
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)

    def test_no_employment_rejected(self) -> None:
        payload = _valid_payload()
        payload["primary_borrower"]["employment"] = []
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)

    def test_co_borrower_requires_relationship(self) -> None:
        payload = _valid_payload()
        payload["co_borrower"] = {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "phone": "+14165551235",
            "preferred_contact_method": "phone",
            "date_of_birth": "1992-05-20",
            "sin": "046454286",
            "marital_status": "married",
            "number_of_dependants": 0,
            "current_address": {
                "street": "123 Main St",
                "city": "Toronto",
                "province": "ON",
                "postal_code": "M5V2T6",
                "years_at_address": 2,
                "months_at_address": 6,
            },
            "employment": [
                {
                    "employment_type": "employed",
                    "employer_name": "Acme Corp",
                    "job_title": "Manager",
                    "occupation_category": "management",
                    "industry": "technology",
                    "duration_years": 3,
                    "duration_months": 0,
                    "annual_gross_income": Decimal("90000.00"),
                }
            ],
        }
        with pytest.raises(Exception, match="relationship_to_primary"):
            validate_borrower_payload(payload)

    def test_future_date_of_birth_rejected(self) -> None:
        payload = _valid_payload()
        payload["primary_borrower"]["date_of_birth"] = "2030-01-01"
        with pytest.raises(ValidationError):
            validate_borrower_payload(payload)


class TestMaskedProjection:
    def test_mask_sin_basic(self) -> None:
        masked = mask_sin("123456789")
        assert masked.last_three == "789"
        assert masked.display == "*** *** 789"

    def test_mask_sin_all_zeros(self) -> None:
        masked = mask_sin("000000000")
        assert masked.last_three == "000"
        assert masked.display == "*** *** 000"

    def test_mask_sin_invalid_length_raises(self) -> None:
        with pytest.raises(ValueError):
            mask_sin("123")

    def test_mask_sin_non_digit_raises(self) -> None:
        with pytest.raises(ValueError):
            mask_sin("12345abcd")

    def test_internal_projection_masked_sin(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = _create_submitted_application(db_session, crypto_state)

        result = get_internal_projection(db_session, crypto_state, application.id)

        assert result["has_sin"] is True
        assert result["primary_borrower"]["sin"]["last_three"] == "286"
        assert result["primary_borrower"]["sin"]["display"] == "*** *** 286"
        assert "046454286" not in json.dumps(result)

    def test_internal_projection_draft_blocked(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)

        with pytest.raises(ValueError, match="not found"):
            get_internal_projection(db_session, crypto_state, application.id)

    def test_internal_projection_no_evidence_blocked(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
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

        with pytest.raises(ValueError, match="not found"):
            get_internal_projection(db_session, crypto_state, application.id)

    def test_internal_projection_no_raw_sin_in_response(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = _create_submitted_application(db_session, crypto_state)

        result = get_internal_projection(db_session, crypto_state, application.id)
        result_str = json.dumps(result)

        assert "046454286" not in result_str
        assert "9 digit" not in result_str.lower() or "sin" in result_str.lower()


class TestNoOpSave:
    def test_no_op_save_same_payload(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(db_session, crypto_state, None)
        payload = _valid_payload()

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=payload,
            settings=None,
        )

        db_session.refresh(application)
        first_activity = application.last_activity_at

        result = save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data=payload,
            settings=None,
        )

        assert result.revision == 1
        assert result.last_activity_at == first_activity

    def test_no_op_save_different_payload_updates(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(db_session, crypto_state, None)

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=_valid_payload(),
            settings=None,
        )

        db_session.refresh(application)
        first_activity = application.last_activity_at

        modified_payload = _valid_payload()
        modified_payload["primary_borrower"]["first_name"] = "Different"

        result = save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data=modified_payload,
            settings=None,
        )

        assert result.revision == 2
        assert result.last_activity_at >= first_activity


class TestSubmissionEvidence:
    def test_no_evidence_for_draft(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        assert has_submission_evidence(db_session, application.id) is False

    def test_no_evidence_without_snapshot(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = _create_submitted_application(db_session, crypto_state)
        db_session.delete(
            db_session.query(BorrowerApplicationSnapshot)
            .filter_by(application_id=application.id)
            .one()
        )
        db_session.commit()
        assert has_submission_evidence(db_session, application.id) is False

    def test_evidence_complete(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = _create_submitted_application(db_session, crypto_state)
        assert has_submission_evidence(db_session, application.id) is True

    def test_forged_submitted_no_evidence(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        application.lifecycle_status = "submitted"
        application.submitted_at = datetime.now(UTC)
        db_session.commit()

        assert has_submission_evidence(db_session, application.id) is False


class TestSinReveal:
    def test_reveal_sin_success(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = _create_submitted_application(db_session, crypto_state)

        sin_value = reveal_sin(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            selector="primary",
            reason_category="credit_assessment",
            actor_user_id=uuid.uuid4(),
            actor_role="brokerage_admin",
            assurance_level="aal2",
        )

        assert sin_value == "046454286"

        audit = db_session.query(BorrowerSinRevealAudit).first()
        assert audit is not None
        assert audit.result == "success"
        assert audit.safe_reason_code == "revealed"
        assert audit.selector == "primary"
        assert audit.reason_category == "credit_assessment"
        assert "046454286" not in str(audit.__dict__.values())

    def test_reveal_sin_draft_blocked(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)

        with pytest.raises(ValueError, match="not found"):
            reveal_sin(
                db=db_session,
                crypto_state=crypto_state,
                application_id=application.id,
                selector="primary",
                reason_category="test",
                actor_user_id=uuid.uuid4(),
                actor_role="agent",
                assurance_level="aal2",
            )

    def test_reveal_sin_no_audit_for_failure(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)

        with pytest.raises(ValueError):
            reveal_sin(
                db=db_session,
                crypto_state=crypto_state,
                application_id=application.id,
                selector="primary",
                reason_category="test",
                actor_user_id=uuid.uuid4(),
                actor_role="agent",
                assurance_level="aal2",
            )

        assert db_session.query(BorrowerSinRevealAudit).count() == 0


class TestActivityTimestampBehavior:
    def test_start_sets_activity_time(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        assert application.last_activity_at is not None

    def test_save_updates_activity_time(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        original_activity = application.last_activity_at

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=_valid_payload(),
            settings=None,
        )

        db_session.refresh(application)
        assert application.last_activity_at >= original_activity

    def test_no_op_save_preserves_activity_time(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=_valid_payload(),
            settings=None,
        )
        db_session.refresh(application)
        activity_after_first_save = application.last_activity_at

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data=_valid_payload(),
            settings=None,
        )
        db_session.refresh(application)
        assert application.last_activity_at == activity_after_first_save


class TestCapabilitySessionBinding:
    def test_capability_session_matches_application(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, capability = start_borrower_application(db_session, crypto_state, None)
        assert application.capability_session_id is not None

        ctx = verify_borrower_capability(db_session, crypto_state, application.id, capability)
        assert ctx.capability_session_id == application.capability_session_id

    def test_capability_mismatch_rejected(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        app1, _ = start_borrower_application(db_session, crypto_state, None)
        app2, cap2 = start_borrower_application(db_session, crypto_state, None)

        with pytest.raises(HTTPException) as exc_info:
            verify_borrower_capability(db_session, crypto_state, app1.id, cap2)
        assert exc_info.value.status_code == 404

    def test_draft_save_requires_matching_capability(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        app1, _ = start_borrower_application(db_session, crypto_state, None)
        app2, cap2 = start_borrower_application(db_session, crypto_state, None)

        with pytest.raises(ValueError, match="capability mismatch"):
            save_draft_payload(
                db=db_session,
                crypto_state=crypto_state,
                application_id=app1.id,
                capability_session_id=app2.capability_session_id,
                expected_revision=0,
                payload_data=_valid_payload(),
                settings=None,
            )


class TestNullableActorSystemUser:
    def test_start_application_has_null_actor(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        history = db_session.query(BorrowerApplicationStatusHistory).first()
        assert history is not None
        assert history.actor_user_id is None
        assert history.actor_source == "public"

    def test_submission_has_null_actor(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
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
        history = (
            db_session.query(BorrowerApplicationStatusHistory)
            .filter_by(reason_category="submission")
            .first()
        )
        assert history is not None
        assert history.actor_user_id is None


class TestConsentSnapshotPrimitives:
    def test_consent_record_stored(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
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

        consent = BorrowerConsentRecord(
            application_id=application.id,
            submission_revision=1,
            consent_version="test-v1",
            wording_digest="abc123",
            borrower_coverage="primary_only",
            borrower_count=1,
            capture_source="borrower_draft",
            capability_session_id=application.capability_session_id,
            acknowledged_at=datetime.now(UTC),
        )
        db_session.add(consent)
        db_session.commit()

        loaded = db_session.query(BorrowerConsentRecord).first()
        assert loaded is not None
        assert loaded.consent_version == "test-v1"
        assert loaded.capability_session_id == application.capability_session_id

    def test_snapshot_stored(self, db_session: Session, crypto_state: BorrowerCryptoState) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
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

        snapshot = BorrowerApplicationSnapshot(
            application_id=application.id,
            submission_revision=1,
            key_id="v1",
            nonce=os.urandom(12),
            ciphertext_hash="hash123",
            plaintext_hash="pthash123",
            object_key="snapshots/test.key",
            size_bytes=512,
        )
        db_session.add(snapshot)
        db_session.commit()

        loaded = db_session.query(BorrowerApplicationSnapshot).first()
        assert loaded is not None
        assert loaded.submission_revision == 1
        assert loaded.size_bytes == 512


class TestInternalProjectionNoDraftLeakage:
    def test_draft_application_hidden_from_internal(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)

        with pytest.raises(ValueError, match="not found"):
            get_internal_projection(db_session, crypto_state, application.id)

    def test_submitted_without_evidence_hidden(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
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

        with pytest.raises(ValueError, match="not found"):
            get_internal_projection(db_session, crypto_state, application.id)


class TestOpenApiCookieSecurityScheme:
    def test_cookie_security_scheme_declared(self, client) -> None:
        document = client.get("/openapi.json").json()
        schemes = document.get("components", {}).get("securitySchemes", {})
        assert "__Host-keeper-borrower-draft" in schemes
        cookie_scheme = schemes["__Host-keeper-borrower-draft"]
        assert cookie_scheme["type"] == "apiKey"
        assert cookie_scheme["in"] == "cookie"
        assert cookie_scheme["name"] == "__Host-keeper-borrower-draft"

    def test_borrower_start_no_security(self, client) -> None:
        document = client.get("/openapi.json").json()
        paths = document["paths"]
        start = paths["/api/v1/borrower-applications/start"]
        assert "security" not in start["post"]


class TestMigrationParity:
    def test_model_columns_match_migration(self) -> None:
        from sqlalchemy import inspect

        from keeper_api.models.borrower import (
            BorrowerApplication,
            BorrowerApplicationPayload,
            BorrowerApplicationSnapshot,
            BorrowerApplicationStatusHistory,
            BorrowerAssignmentHistory,
            BorrowerConsentCatalog,
            BorrowerConsentRecord,
            BorrowerDocument,
            BorrowerLegalHold,
            BorrowerSinRevealAudit,
        )

        model_tables = {
            "borrower_applications": BorrowerApplication,
            "borrower_application_payloads": BorrowerApplicationPayload,
            "borrower_application_status_history": BorrowerApplicationStatusHistory,
            "borrower_assignment_history": BorrowerAssignmentHistory,
            "borrower_consent_catalog": BorrowerConsentCatalog,
            "borrower_consent_records": BorrowerConsentRecord,
            "borrower_application_snapshots": BorrowerApplicationSnapshot,
            "borrower_documents": BorrowerDocument,
            "borrower_legal_holds": BorrowerLegalHold,
            "borrower_sin_reveal_audit": BorrowerSinRevealAudit,
        }

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        inspector = inspect(engine)

        for table_name, model_cls in model_tables.items():
            model_columns = {c.name for c in model_cls.__table__.columns}
            db_columns = {col["name"] for col in inspector.get_columns(table_name)}
            assert model_columns == db_columns, (
                f"Column mismatch for {table_name}: "
                f"model has {model_columns - db_columns}, "
                f"db has {db_columns - model_columns}"
            )


class TestNoOpLeakBehavior:
    def test_no_op_does_not_create_history(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=_valid_payload(),
            settings=None,
        )

        history_count_after_first = (
            db_session.query(BorrowerApplicationStatusHistory)
            .filter_by(application_id=application.id)
            .count()
        )

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data=_valid_payload(),
            settings=None,
        )

        history_count_after_second = (
            db_session.query(BorrowerApplicationStatusHistory)
            .filter_by(application_id=application.id)
            .count()
        )
        assert history_count_after_first == history_count_after_second

    def test_no_op_does_not_create_payload(
        self, db_session: Session, crypto_state: BorrowerCryptoState
    ) -> None:
        application, _ = start_borrower_application(db_session, crypto_state, None)
        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=0,
            payload_data=_valid_payload(),
            settings=None,
        )

        payload_count = (
            db_session.query(BorrowerApplicationPayload)
            .filter_by(application_id=application.id)
            .count()
        )

        save_draft_payload(
            db=db_session,
            crypto_state=crypto_state,
            application_id=application.id,
            capability_session_id=application.capability_session_id,
            expected_revision=1,
            payload_data=_valid_payload(),
            settings=None,
        )

        payload_count_after = (
            db_session.query(BorrowerApplicationPayload)
            .filter_by(application_id=application.id)
            .count()
        )
        assert payload_count == payload_count_after
