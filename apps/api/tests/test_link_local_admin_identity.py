from __future__ import annotations

import importlib.util
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from keeper_api.db.base import Base
from keeper_api.models.domain import Role, User, UserIdentity, UserRole

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "link_local_admin_identity.py"
REAL_SUBJECT = "11111111-2222-4333-8444-555555555555"


def script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("link_local_admin_identity", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


linker = script_module()


def make_admin(
    db: Session,
    *,
    email: str = "admin@example.test",
    subject: str = linker.SEEDED_ADMIN_SUBJECT,
    active: bool = True,
    admin_role: bool = True,
) -> tuple[User, UserIdentity]:
    user = User(email=email, display_name="Synthetic Administrator", is_active=active)
    db.add(user)
    db.flush()
    identity = UserIdentity(
        user_id=user.id,
        provider="supabase",
        provider_subject=subject,
        verified_at=datetime.now(UTC),
    )
    db.add(identity)
    if admin_role:
        role = db.scalar(select(Role).where(Role.code == "brokerage_admin"))
        if role is None:
            role = Role(code="brokerage_admin", description="Synthetic admin role")
            db.add(role)
            db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return user, identity


def link(db: Session, **overrides: object):  # type: ignore[no-untyped-def]
    arguments = {
        "app_env": "local",
        "email": " ADMIN@example.test ",
        "subject": REAL_SUBJECT.upper(),
    }
    arguments.update(overrides)
    return linker.link_local_admin_identity(db, **arguments)


def test_replaces_only_known_placeholder_and_is_idempotent(db: Session) -> None:
    _user, identity = make_admin(db)
    first = link(db)
    db.commit()
    first_verified_at = identity.verified_at
    second = link(db)
    db.commit()
    assert first.changed is True
    assert second.changed is False
    assert identity.provider_subject == REAL_SUBJECT
    assert identity.verified_at == first_verified_at


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"active": False}, "inactive"),
        ({"admin_role": False}, "brokerage_admin"),
        ({"subject": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"}, "seeded placeholder"),
    ],
)
def test_rejects_ineligible_local_account(
    db: Session, overrides: dict[str, object], message: str
) -> None:
    make_admin(db, **overrides)
    with pytest.raises(linker.LocalAdminIdentityLinkError, match=message):
        link(db)


def test_rejects_subject_linked_to_another_user(db: Session) -> None:
    make_admin(db)
    make_admin(db, email="other-admin@example.test", subject=REAL_SUBJECT)
    with pytest.raises(linker.LocalAdminIdentityLinkError, match="another local account"):
        link(db)


def test_rejects_missing_existing_supabase_identity(db: Session) -> None:
    user = User(
        email="admin@example.test",
        display_name="Synthetic Administrator",
        is_active=True,
    )
    role = Role(code="brokerage_admin", description="Synthetic admin role")
    db.add_all([user, role])
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()

    with pytest.raises(linker.LocalAdminIdentityLinkError, match="one existing Supabase"):
        link(db)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"email": "not-an-email"}, "valid administrator email"),
        ({"subject": "not-a-uuid"}, "valid Supabase user UUID"),
        ({"app_env": "production"}, "APP_ENV=local"),
    ],
)
def test_rejects_invalid_operator_input(
    db: Session, overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(linker.LocalAdminIdentityLinkError, match=message):
        link(db, **overrides)


def test_transaction_rolls_back_when_persistence_fails() -> None:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with sessions() as setup:
        _user, identity = make_admin(setup)
        identity_id = identity.id

    def fail_update(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("synthetic persistence failure")

    event.listen(UserIdentity, "before_update", fail_update)
    try:
        with (
            pytest.raises(RuntimeError, match="synthetic persistence failure"),
            sessions.begin() as transaction,
        ):
            link(transaction)
    finally:
        event.remove(UserIdentity, "before_update", fail_update)

    with sessions() as verification:
        identity = verification.get(UserIdentity, identity_id)
        assert identity is not None
        assert identity.provider_subject == linker.SEEDED_ADMIN_SUBJECT
    Base.metadata.drop_all(engine)


def test_explicit_non_local_environment_fails_before_database_initialization(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    result = linker.main(["--email", "admin@example.test", "--subject", str(uuid.uuid4())])
    assert result == 2
    assert "APP_ENV=local" in capsys.readouterr().err
