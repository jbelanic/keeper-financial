from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from keeper_api.models.borrower import BorrowerConsentCatalog
from keeper_api.services.consent_approval import (
    ConsentApprovalError,
    approve_consent_real_data,
)

VERSION = "borrower-privacy-credit-disclosure-2026-07-27-v1"
DIGEST = "sha256:approved-digest"


def _seed_catalog(
    db: Session, *, approved: bool = False, version: str = VERSION, digest: str = DIGEST
) -> BorrowerConsentCatalog:
    entry = BorrowerConsentCatalog(
        consent_version=version,
        wording_digest=digest,
        wording_text="Approved synthetic wording.",
        is_active=True,
        real_data_approved=approved,
        effective_from=datetime.now(UTC) - timedelta(days=1),
    )
    db.add(entry)
    db.flush()
    return entry


def test_approve_sets_real_data_approved(db: Session) -> None:
    entry = _seed_catalog(db)
    result = approve_consent_real_data(db, consent_version=VERSION, wording_digest=DIGEST)

    assert result.changed is True
    assert result.entry_id == entry.id
    assert entry.real_data_approved is True


def test_approve_is_idempotent(db: Session) -> None:
    _seed_catalog(db, approved=True)
    result = approve_consent_real_data(db, consent_version=VERSION, wording_digest=DIGEST)

    assert result.changed is False


def test_wrong_version_or_digest_is_refused(db: Session) -> None:
    _seed_catalog(db)
    with pytest.raises(ConsentApprovalError, match="not the active"):
        approve_consent_real_data(db, consent_version="other-version", wording_digest=DIGEST)
    with pytest.raises(ConsentApprovalError, match="not the active"):
        approve_consent_real_data(db, consent_version=VERSION, wording_digest="other-digest")


def test_no_active_entry_is_refused(db: Session) -> None:
    with pytest.raises(ConsentApprovalError, match="No active"):
        approve_consent_real_data(db, consent_version=VERSION, wording_digest=DIGEST)


def test_empty_version_or_digest_is_refused(db: Session) -> None:
    _seed_catalog(db)
    with pytest.raises(ConsentApprovalError, match="required"):
        approve_consent_real_data(db, consent_version="", wording_digest=DIGEST)
