from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from keeper_api.core.config import Settings, get_settings
from keeper_api.db.base import Base
from keeper_api.db.session import get_db
from keeper_api.main import app
from keeper_api.models.domain import Candidate, Role, User, UserIdentity, UserRole
from keeper_api.services.submission_guard import LeadSubmissionGuard

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def settings(tmp_path) -> Settings:  # type: ignore[no-untyped-def]
    return Settings(
        _env_file=None,
        app_env="local",
        database_url="sqlite+pysqlite:///:memory:",
        dev_auth_enabled=True,
        require_admin_mfa=False,
        lead_rate_limit_requests=100,
        storage_backend="local",
        local_storage_path=tmp_path / "objects",
    )


@pytest.fixture
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(engine)
    with TestSession() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db: Session, settings: Settings) -> Generator[TestClient, None, None]:
    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    if app.openapi_url is None:
        app.openapi_url = "/openapi.json"
        if not any(getattr(route, "path", None) == "/openapi.json" for route in app.routes):
            app.add_route(
                "/openapi.json",
                lambda _request: JSONResponse(app.openapi()),
                include_in_schema=False,
            )
    previous_guard = app.state.lead_submission_guard
    app.state.lead_submission_guard = LeadSubmissionGuard(
        request_limit=settings.lead_rate_limit_requests,
        window_seconds=settings.lead_rate_limit_window_seconds,
        tracked_clients=settings.lead_rate_limit_tracked_clients,
    )
    # Python 3.14's selector loop can miss the AnyIO cross-thread wake-up in this WSL
    # environment; uvloop is already supplied by the uvicorn[standard] dependency.
    try:
        with TestClient(app, backend_options={"use_uvloop": True}) as test_client:
            yield test_client
    finally:
        app.state.lead_submission_guard = previous_guard
        app.dependency_overrides.clear()


def create_user(
    db: Session,
    *,
    subject: str,
    role_code: str | None = None,
    candidate_status: str | None = None,
    active: bool = True,
) -> tuple[User, Candidate | None]:
    user = User(
        email=f"{subject}@example.test", display_name=f"Synthetic {subject}", is_active=active
    )
    db.add(user)
    db.flush()
    db.add(
        UserIdentity(
            user_id=user.id,
            provider="supabase",
            provider_subject=subject,
            verified_at=datetime.now(UTC),
        )
    )
    if role_code:
        role = db.query(Role).filter(Role.code == role_code).one_or_none()
        if role is None:
            role = Role(code=role_code, description=f"Synthetic {role_code}")
            db.add(role)
            db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
    candidate = None
    if candidate_status:
        candidate = Candidate(user_id=user.id, status=candidate_status)
        db.add(candidate)
    db.commit()
    return user, candidate


@pytest.fixture
def synthetic_user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-4000-8000-000000000099")
