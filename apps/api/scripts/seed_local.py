from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from keeper_api.core.config import get_settings
from keeper_api.db.session import SessionLocal
from keeper_api.models.domain import (
    Candidate,
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

    if db.scalar(select(User).where(User.email == "candidate@example.test")) is None:
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

    if db.scalar(select(User).where(User.email == "admin@example.test")) is None:
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

    if (
        db.scalar(
            select(RecruitmentPosting).where(RecruitmentPosting.slug == "synthetic-opportunity")
        )
        is None
    ):
        db.add(
            RecruitmentPosting(
                slug="synthetic-opportunity",
                title="Synthetic local-development opportunity",
                summary="Clearly synthetic draft data for local development only.",
                body="This is not a real job posting and is never seeded outside local development.",
                status="draft",
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
