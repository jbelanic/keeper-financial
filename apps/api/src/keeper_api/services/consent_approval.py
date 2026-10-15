"""Borrower consent-catalog real-data approval (decision 40 + 49 follow-up).

Sets ``real_data_approved=true`` on the currently active consent-catalog entry,
but only when the caller names the exact approved version and digest. This is the
audited operator step that pairs with ``BORROWER_REAL_DATA_ENABLED=true``; the
submission path fails closed unless both are in place.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from keeper_api.services.audit import AuditService
from keeper_api.services.borrower_applications import get_current_borrower_consent


class ConsentApprovalError(ValueError):
    """Raised when a real-data consent approval is refused (fail closed)."""


@dataclass(frozen=True)
class ConsentApprovalResult:
    entry_id: uuid.UUID
    changed: bool


def approve_consent_real_data(
    db: Session,
    *,
    consent_version: str,
    wording_digest: str,
    actor_user_id: uuid.UUID | None = None,
) -> ConsentApprovalResult:
    version = consent_version.strip()
    digest = wording_digest.strip()
    if not version or not digest:
        raise ConsentApprovalError("An exact consent version and wording digest are required.")

    current = get_current_borrower_consent(db)
    if current is None:
        raise ConsentApprovalError("No active consent-catalog entry exists.")
    if current.consent_version != version or current.wording_digest != digest:
        raise ConsentApprovalError(
            "The provided version/digest is not the active consent-catalog entry."
        )

    if current.real_data_approved:
        return ConsentApprovalResult(entry_id=current.id, changed=False)

    current.real_data_approved = True
    db.flush()
    AuditService(db).record(
        "consent.real_data_approved",
        "borrower_consent_catalog",
        current.id,
        actor_user_id=actor_user_id,
        safe_metadata={"consent_version": version, "wording_digest": digest},
    )
    return ConsentApprovalResult(entry_id=current.id, changed=True)
