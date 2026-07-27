from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
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
)
from keeper_api.models.domain import User
from keeper_api.services.audit import AuditService
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoState,
    BorrowerDecryptionError,
    EncryptedEnvelope,
    compute_capability_digest,
    decrypt_payload,
    decrypt_sin,
    encrypt_payload,
    encrypt_sin,
    generate_capability,
)


class BorrowerSubmissionError(ValueError):
    def __init__(self, code: str, *, status_code: int = 422) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code


def _decrypt_payload_sin(
    db: Session,
    crypto_state: BorrowerCryptoState,
    payload: BorrowerApplicationPayload,
) -> str | None:
    if payload.encrypted_sin_ciphertext is None or payload.encrypted_sin_nonce is None:
        return None

    candidates = [payload]
    candidates.extend(
        db.scalars(
            select(BorrowerApplicationPayload)
            .where(
                BorrowerApplicationPayload.application_id == payload.application_id,
                BorrowerApplicationPayload.revision < payload.revision,
                BorrowerApplicationPayload.encrypted_sin_ciphertext
                == payload.encrypted_sin_ciphertext,
                BorrowerApplicationPayload.encrypted_sin_nonce == payload.encrypted_sin_nonce,
            )
            .order_by(BorrowerApplicationPayload.revision.desc())
        ).all()
    )
    for candidate in candidates:
        try:
            return decrypt_sin(
                state=crypto_state,
                ciphertext=payload.encrypted_sin_ciphertext,
                nonce=payload.encrypted_sin_nonce,
                application_id=str(payload.application_id),
                payload_revision=candidate.revision,
                key_id=candidate.key_id,
            )
        except BorrowerDecryptionError:
            continue
    raise BorrowerDecryptionError()


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def borrower_draft_expired(
    application: BorrowerApplication, *, now: datetime | None = None
) -> bool:
    if application.draft_expires_at is None:
        return True
    checked_at = now or datetime.now(UTC)
    return _as_aware_utc(application.draft_expires_at) <= checked_at


def record_borrower_draft_activity(
    application: BorrowerApplication, *, now: datetime | None = None
) -> None:
    activity_at = now or datetime.now(UTC)
    application.last_activity_at = activity_at
    application.draft_expires_at = activity_at + timedelta(days=30)


def get_current_borrower_consent(
    db: Session, *, now: datetime | None = None
) -> BorrowerConsentCatalog | None:
    checked_at = now or datetime.now(UTC)
    return db.scalar(
        select(BorrowerConsentCatalog)
        .where(
            BorrowerConsentCatalog.is_active.is_(True),
            BorrowerConsentCatalog.effective_from <= checked_at,
            or_(
                BorrowerConsentCatalog.effective_to.is_(None),
                BorrowerConsentCatalog.effective_to > checked_at,
            ),
        )
        .order_by(
            BorrowerConsentCatalog.effective_from.desc(),
            BorrowerConsentCatalog.created_at.desc(),
            BorrowerConsentCatalog.id.desc(),
        )
    )


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge `incoming` onto `base`. Dicts recurse; lists and scalars from
    `incoming` override `base`. Used so an incremental section PATCH accumulates
    into the prior saved draft instead of replacing it."""
    result = dict(base)
    for key, value in incoming.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class _SafeEncoder(json.JSONEncoder):
    def default(self, o: object) -> Any:
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, date | datetime):
            return o.isoformat()
        return super().default(o)


def start_borrower_application(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    settings: Settings | None = None,
) -> tuple[BorrowerApplication, str]:
    if crypto_state is None:
        raise ValueError("borrower cryptography is unavailable")

    capability = generate_capability()
    capability_digest = compute_capability_digest(capability, crypto_state.hmac_key)

    application = BorrowerApplication(
        capability_digest=capability_digest,
        capability_session_id=uuid.uuid4(),
        lifecycle_status=BorrowerApplicationLifecycleStatus.DRAFT.value,
        revision=0,
        payload_revision=0,
        last_activity_at=datetime.now(UTC),
        draft_expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.add(application)
    db.flush()

    history = BorrowerApplicationStatusHistory(
        application_id=application.id,
        from_status=None,
        to_status=BorrowerApplicationLifecycleStatus.DRAFT.value,
        actor_user_id=None,
        actor_source="public",
        reason_category="start",
        reason_detail=None,
        revision=0,
        capability_session_id=application.capability_session_id,
    )
    db.add(history)
    db.commit()

    return application, capability


def save_draft_payload(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    capability_session_id: uuid.UUID,
    expected_revision: int,
    payload_data: dict[str, Any],
    settings: Settings,
) -> BorrowerApplication:
    application = db.scalar(
        select(BorrowerApplication)
        .where(BorrowerApplication.id == application_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if application is None:
        raise ValueError("application not found")

    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise ValueError("application is not in draft status")

    if borrower_draft_expired(application):
        raise ValueError("application not found")

    if application.capability_session_id != capability_session_id:
        raise ValueError("capability mismatch")

    if application.revision != expected_revision:
        raise ValueError("stale revision")

    if crypto_state is None:
        raise ValueError("borrower cryptography is unavailable")

    # Load the prior saved revision (if any) so an incremental section PATCH
    # merges into it instead of replacing it. Decryption failures propagate.
    prior_plaintext: dict[str, Any] = {}
    prior_payload_row = None
    if application.payload_revision > 0:
        prior_payload_row = db.scalar(
            select(BorrowerApplicationPayload).where(
                BorrowerApplicationPayload.application_id == application_id,
                BorrowerApplicationPayload.revision == application.payload_revision,
            )
        )
        if prior_payload_row is not None:
            try:
                envelope = EncryptedEnvelope(
                    format_version=1,
                    key_id=prior_payload_row.key_id,
                    nonce=prior_payload_row.nonce,
                    ciphertext=prior_payload_row.ciphertext,
                )
                decrypted = decrypt_payload(
                    state=crypto_state,
                    envelope=envelope,
                    application_id=str(application_id),
                    purpose="borrower_application",
                    schema_version=prior_payload_row.schema_version,
                    payload_revision=prior_payload_row.revision,
                )
                prior_plaintext = json.loads(decrypted.decode("utf-8"))
            except BorrowerDecryptionError:
                raise ValueError("borrower cryptography is unavailable") from None

    merged_payload = _deep_merge(prior_plaintext, payload_data)

    has_co_borrower = bool(merged_payload.get("co_borrower"))

    incoming_sin = payload_data.get("primary_borrower", {}).get("sin")
    preserved_sin = None
    if prior_payload_row is not None:
        try:
            preserved_sin = _decrypt_payload_sin(db, crypto_state, prior_payload_row)
        except BorrowerDecryptionError:
            raise ValueError("borrower cryptography is unavailable") from None
    sin_changed = incoming_sin is not None and incoming_sin != preserved_sin

    payload_for_encryption = {k: v for k, v in merged_payload.items() if k != "primary_borrower"}
    if "primary_borrower" in merged_payload:
        borrower_data = dict(merged_payload["primary_borrower"])
        borrower_data.pop("sin", None)
        payload_for_encryption["primary_borrower"] = borrower_data

    plaintext = json.dumps(payload_for_encryption, sort_keys=True, cls=_SafeEncoder).encode("utf-8")

    # No-op guard: if the merged result serializes identically to the prior
    # revision, do not mint a new revision. Compare the canonical serialized
    # form (not the decoded dict) so Decimal/date round-tripping is stable.
    if prior_payload_row is not None and prior_plaintext and not sin_changed:
        prior_serialized = json.dumps(prior_plaintext, sort_keys=True, cls=_SafeEncoder).encode(
            "utf-8"
        )
        if prior_serialized == plaintext:
            return application

    new_revision = expected_revision + 1
    encrypted_sin_ciphertext = None
    encrypted_sin_nonce = None
    sin_to_store = incoming_sin if incoming_sin is not None else preserved_sin
    if sin_to_store:
        encrypted_sin_ciphertext, encrypted_sin_nonce = encrypt_sin(
            crypto_state, sin_to_store, str(application_id), new_revision
        )
    has_sin = bool(encrypted_sin_ciphertext)

    envelope = encrypt_payload(
        state=crypto_state,
        plaintext=plaintext,
        application_id=str(application_id),
        purpose="borrower_application",
        schema_version="1.0",
        payload_revision=new_revision,
    )

    payload = BorrowerApplicationPayload(
        application_id=application_id,
        revision=new_revision,
        schema_version="1.0",
        key_id=envelope.key_id,
        nonce=envelope.nonce,
        ciphertext=envelope.ciphertext,
        has_sin=has_sin,
        has_co_borrower=has_co_borrower,
        encrypted_sin_ciphertext=encrypted_sin_ciphertext,
        encrypted_sin_nonce=encrypted_sin_nonce,
    )
    db.add(payload)

    application.revision = new_revision
    application.payload_revision = new_revision
    record_borrower_draft_activity(application)

    history = BorrowerApplicationStatusHistory(
        application_id=application_id,
        from_status=BorrowerApplicationLifecycleStatus.DRAFT.value,
        to_status=BorrowerApplicationLifecycleStatus.DRAFT.value,
        actor_user_id=None,
        actor_source="public",
        reason_category="save",
        reason_detail=None,
        revision=new_revision,
        capability_session_id=capability_session_id,
    )
    db.add(history)

    db.commit()
    return application


def get_latest_payload(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    payload_revision: int,
) -> dict[str, Any] | None:
    payload = db.scalar(
        select(BorrowerApplicationPayload).where(
            BorrowerApplicationPayload.application_id == application_id,
            BorrowerApplicationPayload.revision == payload_revision,
        )
    )
    if payload is None:
        return None

    if crypto_state is None:
        raise ValueError("borrower cryptography is unavailable")

    try:
        from keeper_api.services.borrower_crypto import EncryptedEnvelope

        envelope = EncryptedEnvelope(
            format_version=1,
            key_id=payload.key_id,
            nonce=payload.nonce,
            ciphertext=payload.ciphertext,
        )

        plaintext = decrypt_payload(
            state=crypto_state,
            envelope=envelope,
            application_id=str(application_id),
            purpose="borrower_application",
            schema_version=payload.schema_version,
            payload_revision=payload.revision,
        )
        result: dict[str, Any] = json.loads(plaintext)

        try:
            sin = _decrypt_payload_sin(db, crypto_state, payload)
            primary = result.get("primary_borrower")
            if sin is not None and isinstance(primary, dict):
                primary["sin"] = sin
        except BorrowerDecryptionError:
            pass

        return result
    except BorrowerDecryptionError:
        raise ValueError("failed to decrypt payload") from None


def _seven_year_retention(now: datetime) -> datetime:
    try:
        return now.replace(year=now.year + 7)
    except ValueError:
        return now.replace(month=2, day=28, year=now.year + 7)


def submit_borrower_application(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    capability_session_id: uuid.UUID,
    expected_revision: int,
    consent_version: str,
    consent_wording_digest: str,
    borrower_coverage: str,
    settings: Settings,
) -> tuple[BorrowerApplication, BorrowerApplicationSnapshot, BorrowerConsentRecord]:
    if crypto_state is None:
        raise BorrowerSubmissionError("borrower_cryptography_unavailable", status_code=503)

    application = db.scalar(
        select(BorrowerApplication)
        .where(BorrowerApplication.id == application_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if application is None:
        raise BorrowerSubmissionError("application_not_found", status_code=404)
    if application.capability_session_id != capability_session_id:
        raise BorrowerSubmissionError("application_not_found", status_code=404)
    if (
        application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value
        and borrower_draft_expired(application)
    ):
        raise BorrowerSubmissionError("application_not_found", status_code=404)
    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        consent = db.scalar(
            select(BorrowerConsentRecord).where(
                BorrowerConsentRecord.application_id == application_id
            )
        )
        snapshot = db.scalar(
            select(BorrowerApplicationSnapshot).where(
                BorrowerApplicationSnapshot.application_id == application_id
            )
        )
        if (
            consent is not None
            and snapshot is not None
            and consent.capability_session_id == capability_session_id
            and consent.submission_revision == expected_revision
            and consent.consent_version == consent_version
            and consent.wording_digest == consent_wording_digest
            and consent.borrower_coverage == borrower_coverage
        ):
            return application, snapshot, consent
        raise BorrowerSubmissionError("already_submitted", status_code=409)
    if application.revision != expected_revision:
        raise BorrowerSubmissionError("stale_revision", status_code=409)
    if application.payload_revision != expected_revision or application.payload_revision <= 0:
        raise BorrowerSubmissionError("missing_payload", status_code=422)
    if db.scalar(
        select(BorrowerDocument.id)
        .where(
            BorrowerDocument.application_id == application_id,
            BorrowerDocument.deletion_pending_at.is_not(None),
        )
        .limit(1)
    ):
        raise BorrowerSubmissionError("document_operation_pending", status_code=409)

    payload_row = db.scalar(
        select(BorrowerApplicationPayload).where(
            BorrowerApplicationPayload.application_id == application_id,
            BorrowerApplicationPayload.revision == application.payload_revision,
        )
    )
    if payload_row is None:
        raise BorrowerSubmissionError("missing_payload", status_code=422)

    payload_data = get_latest_payload(
        db, crypto_state, application_id, application.payload_revision
    )
    if payload_data is None:
        raise BorrowerSubmissionError("missing_payload", status_code=422)

    from keeper_api.schemas.borrower_payload import validate_borrower_payload

    try:
        validated_payload = validate_borrower_payload(payload_data)
    except Exception as exc:
        raise BorrowerSubmissionError("payload_incomplete", status_code=422) from exc

    now = datetime.now(UTC)
    catalog_entry = get_current_borrower_consent(db, now=now)
    if (
        catalog_entry is None
        or catalog_entry.consent_version != consent_version
        or catalog_entry.wording_digest != consent_wording_digest
    ):
        raise BorrowerSubmissionError("invalid_consent", status_code=422)
    if (settings.app_env != "local" and not settings.borrower_real_data_enabled) or (
        settings.borrower_real_data_enabled and not catalog_entry.real_data_approved
    ):
        raise BorrowerSubmissionError("real_data_submission_disabled", status_code=503)

    effective_from = _as_aware_utc(catalog_entry.effective_from)
    effective_to = (
        _as_aware_utc(catalog_entry.effective_to)
        if catalog_entry.effective_to is not None
        else None
    )
    if effective_from > now or (effective_to is not None and effective_to <= now):
        raise BorrowerSubmissionError("invalid_consent", status_code=422)

    has_co_borrower = validated_payload.co_borrower is not None
    borrower_count = 2 if has_co_borrower else 1
    if has_co_borrower and borrower_coverage != "both":
        raise BorrowerSubmissionError("invalid_borrower_coverage", status_code=422)
    if not has_co_borrower and borrower_coverage != "primary":
        raise BorrowerSubmissionError("invalid_borrower_coverage", status_code=422)

    payload_for_snapshot = validated_payload.model_dump(mode="json", exclude_none=True)
    snapshot_plaintext = json.dumps(
        payload_for_snapshot,
        sort_keys=True,
        separators=(",", ":"),
        cls=_SafeEncoder,
    ).encode("utf-8")
    envelope = encrypt_payload(
        state=crypto_state,
        plaintext=snapshot_plaintext,
        application_id=str(application_id),
        purpose="borrower_submission_snapshot",
        schema_version=payload_row.schema_version,
        payload_revision=payload_row.revision,
    )

    from keeper_api.services.borrower_documents import (
        BorrowerDocumentStorageError,
        delete_borrower_object,
        put_encrypted_borrower_object,
    )

    try:
        stored = put_encrypted_borrower_object(
            settings,
            prefix="snapshots",
            content=envelope.ciphertext,
            content_type="application/octet-stream",
        )
    except BorrowerDocumentStorageError as exc:
        raise BorrowerSubmissionError("submission_storage_unavailable", status_code=503) from exc
    try:
        consent = BorrowerConsentRecord(
            application_id=application_id,
            submission_revision=application.revision,
            consent_version=consent_version,
            wording_digest=consent_wording_digest,
            borrower_coverage=borrower_coverage,
            borrower_count=borrower_count,
            capture_source="borrower_web",
            capability_session_id=capability_session_id,
            acknowledged_at=now,
        )
        db.add(consent)
        db.flush()

        snapshot = BorrowerApplicationSnapshot(
            application_id=application_id,
            submission_revision=application.revision,
            payload_revision=payload_row.revision,
            schema_version=payload_row.schema_version,
            key_id=envelope.key_id,
            nonce=envelope.nonce,
            ciphertext=envelope.ciphertext,
            consent_record_id=consent.id,
            ciphertext_hash=hashlib.sha256(envelope.ciphertext).hexdigest(),
            plaintext_hash=hashlib.sha256(snapshot_plaintext).hexdigest(),
            object_key=stored.object_key,
            size_bytes=len(snapshot_plaintext),
        )
        db.add(snapshot)

        application.lifecycle_status = BorrowerApplicationLifecycleStatus.SUBMITTED.value
        application.submitted_at = now
        application.retention_due_at = _seven_year_retention(now)
        application.capability_revoked_at = now

        db.add(
            BorrowerApplicationStatusHistory(
                application_id=application_id,
                from_status=BorrowerApplicationLifecycleStatus.DRAFT.value,
                to_status=BorrowerApplicationLifecycleStatus.SUBMITTED.value,
                actor_user_id=None,
                actor_source="public",
                reason_category="submission",
                reason_detail=None,
                revision=application.revision,
                capability_session_id=capability_session_id,
            )
        )
        AuditService(db).record(
            "borrower_application_submitted",
            "borrower_application",
            application.id,
            safe_metadata={
                "result": "success",
                "submission_revision": application.revision,
            },
        )
        db.flush()
        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            delete_borrower_object(settings, stored.object_key)
        except BorrowerDocumentStorageError as cleanup_exc:
            raise BorrowerSubmissionError(
                "submission_cleanup_unavailable", status_code=503
            ) from cleanup_exc
        raise BorrowerSubmissionError("submission_storage_unavailable", status_code=503) from exc

    return application, snapshot, consent


def get_application_summary(
    db: Session,
    application: BorrowerApplication,
) -> dict[str, Any]:
    payload = db.scalar(
        select(BorrowerApplicationPayload).where(
            BorrowerApplicationPayload.application_id == application.id,
            BorrowerApplicationPayload.revision == application.payload_revision,
        )
    )

    return {
        "id": str(application.id),
        "lifecycle_status": application.lifecycle_status,
        "revision": application.revision,
        "payload_revision": application.payload_revision,
        "has_sin": payload.has_sin if payload else False,
        "has_co_borrower": payload.has_co_borrower if payload else False,
        "last_activity_at": application.last_activity_at.isoformat(),
        "draft_expires_at": application.draft_expires_at.isoformat()
        if application.draft_expires_at
        else None,
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
        "retention_due_at": application.retention_due_at.isoformat()
        if application.retention_due_at
        else None,
        "assigned_agent_id": str(application.assigned_agent_id)
        if application.assigned_agent_id
        else None,
        "capability_session_id": str(application.capability_session_id),
    }


def transition_lifecycle(
    db: Session,
    application_id: uuid.UUID,
    from_status: BorrowerApplicationLifecycleStatus,
    to_status: BorrowerApplicationLifecycleStatus,
    actor_user_id: uuid.UUID | None,
    actor_source: str,
    reason_category: str | None = None,
    reason_detail: str | None = None,
    capability_session_id: uuid.UUID | None = None,
) -> BorrowerApplication:
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise ValueError("application not found")

    current_status = BorrowerApplicationLifecycleStatus(application.lifecycle_status)
    if current_status != from_status:
        raise ValueError(f"cannot transition from {current_status.value} to {to_status.value}")

    application.lifecycle_status = to_status.value

    if to_status == BorrowerApplicationLifecycleStatus.SUBMITTED:
        application.submitted_at = datetime.now(UTC)
        application.retention_due_at = datetime.now(UTC) + timedelta(days=365 * 7)
        application.capability_revoked_at = datetime.now(UTC)

    if to_status in (
        BorrowerApplicationLifecycleStatus.WITHDRAWN,
        BorrowerApplicationLifecycleStatus.EXPIRED,
    ):
        application.capability_revoked_at = datetime.now(UTC)

    history = BorrowerApplicationStatusHistory(
        application_id=application_id,
        from_status=from_status.value,
        to_status=to_status.value,
        actor_user_id=actor_user_id,
        actor_source=actor_source,
        reason_category=reason_category,
        reason_detail=reason_detail,
        revision=application.revision,
        capability_session_id=capability_session_id,
    )
    db.add(history)

    db.commit()
    return application


def assign_application(
    db: Session,
    application_id: uuid.UUID,
    agent_user_id: uuid.UUID | None,
    actor_user_id: uuid.UUID,
    reason_category: str,
    reason_detail: str | None = None,
) -> BorrowerApplication:
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise ValueError("application not found")

    application.assigned_agent_id = agent_user_id
    application.assigned_at = datetime.now(UTC)

    if agent_user_id is None and reason_category != "unassignment":
        raise ValueError("unassignment requires reason_category='unassignment'")

    history = BorrowerAssignmentHistory(
        application_id=application_id,
        agent_user_id=agent_user_id,
        actor_user_id=actor_user_id,
        actor_source="administrator",
        reason_category=reason_category,
        reason_detail=reason_detail,
        assigned_at=datetime.now(UTC),
    )
    db.add(history)

    db.commit()
    return application


def revoke_capability(
    db: Session,
    application_id: uuid.UUID,
) -> None:
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        return

    application.capability_revoked_at = datetime.now(UTC)
    db.commit()


def create_consent_record(
    db: Session,
    application_id: uuid.UUID,
    submission_revision: int,
    consent_version: str,
    wording_digest: str,
    borrower_coverage: str,
    borrower_count: int,
    capture_source: str,
    capability_session_id: uuid.UUID,
    acknowledged_at: datetime,
) -> BorrowerConsentRecord:
    consent = BorrowerConsentRecord(
        application_id=application_id,
        submission_revision=submission_revision,
        consent_version=consent_version,
        wording_digest=wording_digest,
        borrower_coverage=borrower_coverage,
        borrower_count=borrower_count,
        capture_source=capture_source,
        capability_session_id=capability_session_id,
        acknowledged_at=acknowledged_at,
    )
    db.add(consent)
    db.commit()
    return consent


def has_submission_evidence(db: Session, application_id: uuid.UUID) -> bool:
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        return False

    if application.lifecycle_status not in (
        BorrowerApplicationLifecycleStatus.SUBMITTED.value,
        BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value,
        BorrowerApplicationLifecycleStatus.COMPLETED.value,
        BorrowerApplicationLifecycleStatus.WITHDRAWN.value,
        BorrowerApplicationLifecycleStatus.EXPIRED.value,
    ):
        return False

    if application.submitted_at is None:
        return False

    if application.retention_due_at is None:
        return False

    from keeper_api.models.borrower import BorrowerApplicationSnapshot, BorrowerConsentRecord

    snapshot = db.scalar(
        select(BorrowerApplicationSnapshot).where(
            BorrowerApplicationSnapshot.application_id == application_id
        )
    )
    if snapshot is None:
        return False

    consent = db.scalar(
        select(BorrowerConsentRecord).where(
            BorrowerConsentRecord.application_id == application_id,
            BorrowerConsentRecord.submission_revision == snapshot.submission_revision,
        )
    )
    return consent is not None


def list_admin_review_queue(db: Session) -> list[dict[str, Any]]:
    statuses = (
        BorrowerApplicationLifecycleStatus.SUBMITTED.value,
        BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value,
    )
    applications = db.scalars(
        select(BorrowerApplication)
        .where(BorrowerApplication.lifecycle_status.in_(statuses))
        .order_by(BorrowerApplication.submitted_at.asc(), BorrowerApplication.id.asc())
    ).all()
    rows: list[dict[str, Any]] = []
    for application in applications:
        if not has_submission_evidence(db, application.id):
            continue
        agent = (
            db.get(User, application.assigned_agent_id) if application.assigned_agent_id else None
        )
        rows.append(
            {
                "application_id": str(application.id),
                "lifecycle_status": application.lifecycle_status,
                "submitted_at": application.submitted_at.isoformat()
                if application.submitted_at
                else None,
                "assigned_agent_id": str(application.assigned_agent_id)
                if application.assigned_agent_id
                else None,
                "assigned_agent_name": agent.display_name if agent else None,
                "assigned_agent_email": agent.email if agent else None,
            }
        )
    return rows


def assign_submitted_application(
    db: Session,
    application_id: uuid.UUID,
    agent_user_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    reason_category: str,
    reason_detail: str | None = None,
    request_id: str | None = None,
) -> BorrowerApplication:
    from keeper_api.services.borrower_authorization import validate_assignment_target

    allowed_reasons = {
        "initial_assignment",
        "reassignment",
        "workload",
        "coverage",
        "conflict",
        "correction",
    }
    if reason_category not in allowed_reasons:
        raise ValueError("invalid assignment reason")

    validate_assignment_target(db, agent_user_id)

    application = db.scalar(
        select(BorrowerApplication)
        .where(BorrowerApplication.id == application_id)
        .execution_options(populate_existing=True)
        .with_for_update()
    )
    if application is None:
        raise ValueError("application not found")

    if application.lifecycle_status not in (
        BorrowerApplicationLifecycleStatus.SUBMITTED.value,
        BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value,
    ):
        raise ValueError("application is not assignable")

    if not has_submission_evidence(db, application_id):
        raise ValueError("application not found")

    if application.assigned_agent_id == agent_user_id:
        if application.lifecycle_status == BorrowerApplicationLifecycleStatus.SUBMITTED.value:
            application.lifecycle_status = BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value
            db.add(
                BorrowerApplicationStatusHistory(
                    application_id=application_id,
                    from_status=BorrowerApplicationLifecycleStatus.SUBMITTED.value,
                    to_status=BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value,
                    actor_user_id=actor_user_id,
                    actor_source="administrator",
                    reason_category="assignment_review_start",
                    reason_detail=None,
                    revision=application.revision,
                    capability_session_id=None,
                )
            )
            AuditService(db).record(
                "borrower_application_assignment_idempotent_review_start",
                "borrower_application",
                application_id,
                actor_user_id=actor_user_id,
                request_id=request_id,
                safe_metadata={"result": "under_review"},
            )
            db.commit()
        return application

    now = datetime.now(UTC)
    previous_agent_id = application.assigned_agent_id
    from_status = application.lifecycle_status
    application.assigned_agent_id = agent_user_id
    application.assigned_at = now
    if application.lifecycle_status == BorrowerApplicationLifecycleStatus.SUBMITTED.value:
        application.lifecycle_status = BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value
        db.add(
            BorrowerApplicationStatusHistory(
                application_id=application_id,
                from_status=from_status,
                to_status=BorrowerApplicationLifecycleStatus.UNDER_REVIEW.value,
                actor_user_id=actor_user_id,
                actor_source="administrator",
                reason_category="assignment_review_start",
                reason_detail=None,
                revision=application.revision,
                capability_session_id=None,
            )
        )

    db.add(
        BorrowerAssignmentHistory(
            application_id=application_id,
            agent_user_id=agent_user_id,
            actor_user_id=actor_user_id,
            actor_source="administrator",
            reason_category=reason_category,
            reason_detail=reason_detail,
            assigned_at=now,
        )
    )
    AuditService(db).record(
        "borrower_application_assigned",
        "borrower_application",
        application_id,
        actor_user_id=actor_user_id,
        request_id=request_id,
        safe_metadata={
            "reason_category": reason_category,
            "previous_agent_id": str(previous_agent_id) if previous_agent_id else None,
            "assigned_agent_id": str(agent_user_id),
            "result": "success",
        },
    )
    db.commit()
    db.refresh(application)
    return application


def get_internal_projection(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
) -> dict[str, Any]:
    from keeper_api.schemas.borrower_internal import mask_sin

    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise ValueError("application not found")

    if application.lifecycle_status == BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise ValueError("application not found")

    if not has_submission_evidence(db, application_id):
        raise ValueError("application not found")

    result: dict[str, Any] = {
        "application_id": str(application.id),
        "lifecycle_status": application.lifecycle_status,
        "revision": application.revision,
        "has_sin": False,
        "has_co_borrower": False,
        "primary_borrower": None,
        "co_borrower": None,
        "mortgage_request": None,
        "last_activity_at": application.last_activity_at.isoformat(),
        "submitted_at": application.submitted_at.isoformat() if application.submitted_at else None,
    }

    if application.payload_revision == 0 or crypto_state is None:
        return result

    payload = get_latest_payload(db, crypto_state, application.id, application.payload_revision)
    if payload is None:
        return result

    result["has_sin"] = bool(payload.get("primary_borrower", {}).get("sin"))
    result["has_co_borrower"] = bool(payload.get("co_borrower"))
    result["mortgage_request"] = payload.get("mortgage_request")

    primary = payload.get("primary_borrower")
    if primary is not None:
        sin_val = primary.get("sin", "")
        masked = mask_sin(sin_val) if sin_val else None
        result["primary_borrower"] = {
            "first_name": primary.get("first_name", ""),
            "last_name": primary.get("last_name", ""),
            "email": primary.get("email", ""),
            "phone": primary.get("phone", ""),
            "date_of_birth": str(primary.get("date_of_birth", "")),
            "sin": {"last_three": masked.last_three, "display": masked.display} if masked else None,
            "marital_status": primary.get("marital_status", ""),
            "number_of_dependants": primary.get("number_of_dependants", 0),
            "current_address": primary.get("current_address", {}),
            "employment": primary.get("employment", []),
            "has_sin": bool(sin_val),
        }

    co = payload.get("co_borrower")
    if co is not None:
        co_sin_val = co.get("sin", "")
        co_masked = mask_sin(co_sin_val) if co_sin_val else None
        result["co_borrower"] = {
            "first_name": co.get("first_name", ""),
            "last_name": co.get("last_name", ""),
            "email": co.get("email", ""),
            "phone": co.get("phone", ""),
            "date_of_birth": str(co.get("date_of_birth", "")),
            "sin": {"last_three": co_masked.last_three, "display": co_masked.display}
            if co_masked
            else None,
            "marital_status": co.get("marital_status", ""),
            "number_of_dependants": co.get("number_of_dependants", 0),
            "current_address": co.get("current_address", {}),
            "employment": co.get("employment", []),
            "has_sin": bool(co_sin_val),
            "relationship_to_primary": co.get("relationship_to_primary", ""),
        }

    return result


def reveal_sin(
    db: Session,
    crypto_state: BorrowerCryptoState | None,
    application_id: uuid.UUID,
    selector: str,
    reason_category: str,
    actor_user_id: uuid.UUID,
    actor_role: str,
    assurance_level: str,
) -> str:
    allowed_reasons = {
        "credit_review",
        "borrower_identity_review",
        "document_reconciliation",
        "supervisory_review",
    }
    if reason_category not in allowed_reasons:
        raise ValueError("invalid reveal reason")

    if crypto_state is None:
        raise ValueError("borrower cryptography is unavailable")

    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise ValueError("application not found")

    if not has_submission_evidence(db, application_id):
        raise ValueError("application not found")

    if application.payload_revision == 0:
        raise ValueError("no payload to reveal")

    payload = db.scalar(
        select(BorrowerApplicationPayload).where(
            BorrowerApplicationPayload.application_id == application_id,
            BorrowerApplicationPayload.revision == application.payload_revision,
        )
    )
    if payload is None:
        raise ValueError("payload not found")

    if selector == "primary":
        if not payload.encrypted_sin_ciphertext or not payload.encrypted_sin_nonce:
            raise ValueError("SIN not available for primary borrower")
        from keeper_api.services.borrower_crypto import decrypt_sin

        try:
            sin = decrypt_sin(
                crypto_state,
                payload.encrypted_sin_ciphertext,
                payload.encrypted_sin_nonce,
                str(application_id),
                payload.revision,
                payload.key_id,
            )
        except BorrowerDecryptionError:
            raise ValueError("failed to decrypt SIN") from None

        from keeper_api.models.borrower import BorrowerSinRevealAudit

        audit = BorrowerSinRevealAudit(
            application_id=application_id,
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            assurance_level=assurance_level,
            selector=selector,
            reason_category=reason_category,
            result="success",
            safe_reason_code="revealed",
        )
        db.add(audit)
        db.commit()
        return sin
    else:
        raise ValueError("unsupported SIN selector")
