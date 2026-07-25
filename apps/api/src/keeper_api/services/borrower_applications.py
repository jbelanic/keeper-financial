from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.core.config import Settings
from keeper_api.models.borrower import (
    BorrowerApplication,
    BorrowerApplicationLifecycleStatus,
    BorrowerApplicationPayload,
    BorrowerApplicationStatusHistory,
    BorrowerAssignmentHistory,
    BorrowerConsentRecord,
)
from keeper_api.services.borrower_crypto import (
    BorrowerCryptoState,
    BorrowerDecryptionError,
    EncryptedEnvelope,
    compute_capability_digest,
    decrypt_payload,
    encrypt_payload,
    encrypt_sin,
    generate_capability,
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
    application = db.get(BorrowerApplication, application_id)
    if application is None:
        raise ValueError("application not found")

    if application.lifecycle_status != BorrowerApplicationLifecycleStatus.DRAFT.value:
        raise ValueError("application is not in draft status")

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

    # SIN is stored separately from the payload ciphertext. Track prior SIN
    # ciphertext so a partial save that omits `sin` preserves the earlier value.
    prior_encrypted_sin_ciphertext = (
        prior_payload_row.encrypted_sin_ciphertext if prior_payload_row else None
    )
    prior_encrypted_sin_nonce = prior_payload_row.encrypted_sin_nonce if prior_payload_row else None

    merged_payload = _deep_merge(prior_plaintext, payload_data)

    has_co_borrower = bool(merged_payload.get("co_borrower"))

    encrypted_sin_ciphertext = prior_encrypted_sin_ciphertext
    encrypted_sin_nonce = prior_encrypted_sin_nonce
    incoming_sin = payload_data.get("primary_borrower", {}).get("sin")
    if incoming_sin:
        encrypted_sin_ciphertext, encrypted_sin_nonce = encrypt_sin(
            crypto_state, incoming_sin, str(application_id), expected_revision + 1
        )
    # The SIN is stored in a dedicated ciphertext (stripped from the payload
    # dict before encryption), so has_sin tracks the ciphertext, not the merged
    # payload. A partial save that omits sin preserves the prior ciphertext.
    has_sin = bool(encrypted_sin_ciphertext)

    payload_for_encryption = {k: v for k, v in merged_payload.items() if k != "primary_borrower"}
    if "primary_borrower" in merged_payload:
        borrower_data = dict(merged_payload["primary_borrower"])
        borrower_data.pop("sin", None)
        payload_for_encryption["primary_borrower"] = borrower_data

    plaintext = json.dumps(payload_for_encryption, sort_keys=True, cls=_SafeEncoder).encode("utf-8")

    # No-op guard: if the merged result serializes identically to the prior
    # revision, do not mint a new revision. Compare the canonical serialized
    # form (not the decoded dict) so Decimal/date round-tripping is stable.
    if prior_payload_row is not None and prior_plaintext:
        prior_serialized = json.dumps(prior_plaintext, sort_keys=True, cls=_SafeEncoder).encode(
            "utf-8"
        )
        if prior_serialized == plaintext:
            return application

    envelope = encrypt_payload(
        state=crypto_state,
        plaintext=plaintext,
        application_id=str(application_id),
        purpose="borrower_application",
        schema_version="1.0",
        payload_revision=expected_revision + 1,
    )

    new_revision = expected_revision + 1

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
    application.last_activity_at = datetime.now(UTC)
    application.draft_expires_at = datetime.now(UTC) + timedelta(days=30)

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

        if payload.encrypted_sin_ciphertext is not None and payload.encrypted_sin_nonce is not None:
            from keeper_api.services.borrower_crypto import decrypt_sin

            try:
                sin = decrypt_sin(
                    state=crypto_state,
                    ciphertext=payload.encrypted_sin_ciphertext,
                    nonce=payload.encrypted_sin_nonce,
                    application_id=str(application_id),
                    payload_revision=payload.revision,
                    key_id=payload.key_id,
                )
                primary = result.get("primary_borrower")
                if primary is not None:
                    primary["sin"] = sin
            except BorrowerDecryptionError:
                pass

        return result
    except BorrowerDecryptionError:
        raise ValueError("failed to decrypt payload") from None


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
