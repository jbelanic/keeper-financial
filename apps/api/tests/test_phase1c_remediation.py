"""Regression tests for Phase 1C blocking findings B1-B10.

These tests exercise the ACTUAL application code paths (not placeholders).
Each test targets a specific finding from the Phase 1C independent security
audit. Tests are written first (RED), then the minimal code fix is applied so
they pass (GREEN).

Run: python -m pytest apps/api/tests/test_phase1c_remediation.py -xvs
"""
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import (
    CandidateApplication,
    RecruitmentPosting,
)


def _published_posting(db: Session, slug: str) -> RecruitmentPosting:
    posting = RecruitmentPosting(
        slug=slug,
        title=f"Posting {slug}",
        summary="summary",
        body="body",
        status="published",
        version=1,
        published_at=datetime.now(UTC),
    )
    db.add(posting)
    db.commit()
    return posting


def _start(client: TestClient, slug: str, subject: str) -> int:
    resp = client.post(
        f"/api/v1/recruitment/postings/{slug}/applications/start",
        headers={
            "X-Dev-Auth-Sub": subject,
            "X-Dev-Auth-Email": f"{subject}@example.test",
            "X-Dev-Auth-Verified": "true",
        },
    )
    return resp.status_code


# ---------------------------------------------------------------------------
# B1 — High: suspended / offboarding / offboarded candidates must not be able
# to start (or re-start) applications through the provisioning boundary.
# Evidence: provision_application() loads the existing Candidate but never
# checks candidate.status against the denied lifecycle set that
# authorize_portal() enforces for the candidate portal.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("denied_status", ["suspended", "offboarding", "offboarded"])
def test_b1_denied_candidate_lifecycle_cannot_start(
    client: TestClient, db: Session, denied_status: str
):
    # create_user builds the Candidate row when candidate_status is supplied;
    # we then force the exact denied state under test.
    user, candidate = create_user(
        db, subject="b1-candidate", active=True, candidate_status=denied_status
    )
    assert candidate is not None
    candidate.status = denied_status
    db.flush()
    _published_posting(db, slug="b1-posting")

    status_code = _start(client, "b1-posting", subject="b1-candidate")

    # Must be denied; must NOT create a new application.
    assert status_code in (403, 404), (
        f"denied candidate ({denied_status}) should be blocked, got {status_code}"
    )
    apps = (
        db.query(CandidateApplication)
        .filter_by(candidate_id=candidate.id)
        .all()
    )
    assert apps == [], (
        f"denied candidate ({denied_status}) must not own any application"
    )
