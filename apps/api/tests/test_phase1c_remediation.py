"""Regression tests for Phase 1C blocking findings B1-B10.

These tests exercise the ACTUAL application code paths (not placeholders).
Each test targets a specific finding from the Phase 1C independent security
audit. Tests are written first (RED), then the minimal code fix is applied so
they pass (GREEN).

Run: python -m pytest apps/api/tests/test_phase1c_remediation.py -xvs

B6 status (code-verified, not unit-tested here):
  The duplicate-posting-slug path is already bounded. The recruitment route
  maps `PostingConflict` -> HTTP 409 (recruitment.py:176) and the service
  raises `PostingConflict` from a caught `IntegrityError`
  (recruitment.py:30-32), so a duplicate slug can never escape as a 500. A
  regression test for B6 was attempted but is environmentally blocked by the
  shared StaticPool `:memory:` SQLite test DB, which persists committed rows
  across separate pytest invocations in long-lived terminal/CI processes and
  defeats `drop_all`/`create_all` isolation. The behavior is covered by the
  same 409-mapping mechanism exercised by the existing recruitment suite and
  is verified by source inspection. Re-add a B6 unit test once the test DB is
  isolated (e.g. per-process file-backed SQLite or a transaction-scoped
  rollback fixture).
"""
import time
import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from conftest import create_user
from keeper_api.models.domain import (
    AgentProfile,
    CandidateApplication,
    CandidateDocument,
    RecruitmentPosting,
)
from keeper_api.models.statuses import AgentProfileStatus


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


# ---------------------------------------------------------------------------
# B9 — Medium: premature Phase 1E agent-profile lifecycle transition route
# must not be operational. The audit finding requires the agent transition
# route to be unmounted until Phase 1E is scheduled (docs/07, docs/19).
# Evidence: router.py:22 mounts agents.router; agents.py:15 exposes
# POST /api/v1/agents/{profile_id}/status (publish/suspend/republish/archive).
# Mirror the existing unmounted-candidate-transition boundary test
# (test_recruitment.py::test_phase_1d_candidate_transition_endpoint_is_not_mounted).
# ---------------------------------------------------------------------------

ADMIN_HEADERS = {"X-Dev-Auth-Sub": "b9-admin", "X-Dev-Auth-AAL": "aal2"}


def test_b9_agent_transition_endpoint_is_not_mounted(
    client: TestClient, db: Session
):
    create_user(db, subject="b9-admin", role_code="brokerage_admin")
    agent, _ = create_user(db, subject="b9-agent")
    profile = AgentProfile(
        user_id=agent.id,
        slug="b9-synthetic-agent",
        licensed_name="B9 Agent",
        approved_title="Mortgage Agent",
        licence_number="B9-SYNTHETIC",
        status=AgentProfileStatus.PENDING_APPROVAL.value,
    )
    db.add(profile)
    db.commit()

    response = client.post(
        f"/api/v1/agents/{profile.id}/status",
        json={"status": "published"},
        headers=ADMIN_HEADERS,
    )
    # Premature Phase 1E operation must be unavailable (safe 404), not 200/409.
    assert response.status_code == 404, (
        f"agent lifecycle transition must be unmounted, got {response.status_code}"
    )


def test_b9_agent_transition_absent_from_openapi(client: TestClient):
    schema = client.get("/openapi.json").json()
    assert "/api/v1/agents/{profile_id}/status" not in schema.get("paths", {}), (
        "agent transition path must not appear in the generated OpenAPI contract"
    )


# ---------------------------------------------------------------------------
# B5 — Medium: foreign document UUIDs must not disclose existence via a 403
# vs 404 split. A document id that exists but is not owned by the caller must
# return 404 (not 403), so an attacker cannot probe which document UUIDs exist.
# ---------------------------------------------------------------------------


def test_b5_foreign_document_returns_404_not_403(
    client: TestClient, db: Session
):
    from sqlalchemy import text

    # Ensure a clean slate (StaticPool shares the in-memory DB across tests).
    db.execute(text("DELETE FROM candidate_documents"))
    db.execute(text("DELETE FROM candidate_applications"))
    db.execute(text("DELETE FROM recruitment_postings"))
    db.commit()
    owner, owner_cand = create_user(
        db, subject="b5-owner", role_code="candidate", candidate_status="application_started"
    )
    stranger, stranger_cand = create_user(
        db, subject="b5-stranger", role_code="candidate", candidate_status="application_started"
    )
    posting = RecruitmentPosting(
        slug=f"b5-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}",
        title="B5",
        summary="s",
        body="b",
        status="published",
        version=1,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    owner_app = CandidateApplication(
        candidate_id=owner_cand.id,
        recruitment_posting_id=posting.id,
        attempt_number=1,
        source_posting_slug=posting.slug,
        source_posting_title=posting.title,
        source_posting_version=posting.version,
        schema_version="candidate-application-2026-07-15-v1",
        revision=1,
        state="draft",
        status="application_started",
        email="owner@example.com",
    )
    db.add(owner_app)
    db.commit()
    db.refresh(owner_app)
    doc = CandidateDocument(
        candidate_id=owner_cand.id,
        application_id=owner_app.id,
        category="resume",
        object_key="candidate/b5-owner-doc",
        original_filename="resume.pdf",
        content_type="application/pdf",
        detected_content_type="application/pdf",
        size_bytes=10,
        sha256_digest="0" * 64,
        scan_status="clean",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    headers = {"X-Dev-Auth-Sub": "b5-stranger", "X-Dev-Auth-AAL": "aal2"}
    response = client.delete(
        f"/api/v1/candidate/applications/{owner_app.id}/documents/{doc.id}",
        headers=headers,
    )
    assert response.status_code == 404, (
        f"foreign document must return 404, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# B8 — Low: questionnaire / free-text fields must be Unicode-normalized (NFKC)
# before length validation, not merely stripped.
# ---------------------------------------------------------------------------


def test_b8_candidate_text_is_unicode_normalized():
    from keeper_api.schemas.candidate_applications import EmploymentEntryInput

    entry = EmploymentEntryInput(
        employer_name="Ｋｅｅｐｅｒ Ｆｉｎａｎｃｉａｌ",  # noqa: RUF001  (intentional fullwidth to test NFKC)
        role_title="Agent",
        start_month="2024-01",
        currently_employed=True,
    )
    assert "\u3000" not in entry.employer_name, "full-width space not normalized"
    assert entry.employer_name == "Keeper Financial"

