from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from keeper_api.core.config import get_settings
from keeper_api.db.session import SessionLocal
from keeper_api.models.domain import (
    Candidate,
    CandidateApplication,
    OnboardingPlan,
    OnboardingTask,
    RecruitmentPosting,
    Role,
    User,
    UserIdentity,
    UserRole,
)

settings = get_settings()
if settings.app_env != "local":
    raise SystemExit("Synthetic seed data is permitted only when APP_ENV=local")


def role(db, code: str, description: str) -> Role:  # type: ignore[no-untyped-def]
    existing = db.scalar(select(Role).where(Role.code == code))
    if existing:
        return existing
    value = Role(code=code, description=description)
    db.add(value)
    db.flush()
    return value


with SessionLocal.begin() as db:
    candidate_role = role(db, "candidate", "Candidate portal access")
    admin_role = role(db, "brokerage_admin", "Brokerage administration access")
    role(db, "agent", "Agent portal access")

    candidate_user = db.scalar(select(User).where(User.email == "candidate@example.test"))
    if candidate_user is None:
        candidate_user = User(email="candidate@example.test", display_name="Synthetic Candidate")
        db.add(candidate_user)
        db.flush()
        db.add_all(
            [
                UserIdentity(
                    user_id=candidate_user.id,
                    provider="supabase",
                    provider_subject="00000000-0000-4000-8000-000000000001",
                    verified_at=datetime.now(UTC),
                ),
                UserRole(user_id=candidate_user.id, role_id=candidate_role.id),
                Candidate(user_id=candidate_user.id, status="application_started"),
            ]
        )

    admin_user = db.scalar(select(User).where(User.email == "admin@example.test"))
    if admin_user is None:
        admin_user = User(email="admin@example.test", display_name="Synthetic Administrator")
        db.add(admin_user)
        db.flush()
        db.add_all(
            [
                UserIdentity(
                    user_id=admin_user.id,
                    provider="supabase",
                    provider_subject="00000000-0000-4000-8000-000000000002",
                    verified_at=datetime.now(UTC),
                ),
                UserRole(user_id=admin_user.id, role_id=admin_role.id),
            ]
        )

    posting_fixtures = [
        (
            "synthetic-published-opportunity",
            "SYNTHETIC published local-development opportunity",
            "published",
        ),
        ("synthetic-draft-opportunity", "SYNTHETIC draft local-development opportunity", "draft"),
        (
            "synthetic-closed-opportunity",
            "SYNTHETIC closed local-development opportunity",
            "closed",
        ),
        (
            "synthetic-archived-opportunity",
            "SYNTHETIC archived local-development opportunity",
            "archived",
        ),
    ]
    seeded_postings: dict[str, RecruitmentPosting] = {}
    for slug, title, posting_status in posting_fixtures:
        posting = db.scalar(select(RecruitmentPosting).where(RecruitmentPosting.slug == slug))
        if posting is None:
            posting = RecruitmentPosting(
                slug=slug,
                title=title,
                summary="Explicitly synthetic fixture data; this is not a real job or hiring claim.",
                body="This plain-text local-development fixture is never seeded outside APP_ENV=local.",
                status=posting_status,
                version=1,
                created_by_user_id=admin_user.id,
                updated_by_user_id=admin_user.id,
                published_by_user_id=(
                    admin_user.id if posting_status in {"published", "closed"} else None
                ),
                published_at=(
                    datetime.now(UTC) if posting_status in {"published", "closed"} else None
                ),
                closed_by_user_id=(admin_user.id if posting_status == "closed" else None),
                closed_at=(datetime.now(UTC) if posting_status == "closed" else None),
                archived_by_user_id=(admin_user.id if posting_status == "archived" else None),
                archived_at=(datetime.now(UTC) if posting_status == "archived" else None),
            )
            db.add(posting)
            db.flush()
        seeded_postings[slug] = posting

    candidate = db.scalar(select(Candidate).where(Candidate.user_id == candidate_user.id))
    published = seeded_postings["synthetic-published-opportunity"]
    if (
        candidate is not None
        and db.scalar(
            select(CandidateApplication).where(
                CandidateApplication.candidate_id == candidate.id,
                CandidateApplication.recruitment_posting_id == published.id,
            )
        )
        is None
    ):
        db.add(
            CandidateApplication(
                candidate_id=candidate.id,
                recruitment_posting_id=published.id,
                attempt_number=1,
                source_posting_slug=published.slug,
                source_posting_title=published.title,
                source_posting_version=published.version,
                schema_version="candidate-application-2026-07-15-v1",
                revision=1,
                state="draft",
                status="application_started",
                email=candidate_user.email,
            )
        )

    if (
        db.scalar(select(OnboardingPlan).where(OnboardingPlan.name == "Synthetic local plan"))
        is None
    ):
        plan = OnboardingPlan(
            name="Synthetic local plan",
            description="Local-development plan; not approved brokerage policy.",
        )
        db.add(plan)
        db.flush()
        db.add(
            OnboardingTask(
                plan_id=plan.id,
                title="Review synthetic placeholder",
                instructions="This task has no compliance meaning.",
                sequence=1,
            )
        )

print("Synthetic local seed data is ready.")
