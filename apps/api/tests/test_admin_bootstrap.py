from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.models.domain import Role, User, UserIdentity, UserRole
from keeper_api.services.admin_bootstrap import (
    AdminBootstrapError,
    bootstrap_admin_identity,
)

EMAIL = "admin@keeperfinancial.test"
SUBJECT = "00000000-0000-4000-8000-0000000000aa"


def _role_codes(db: Session, user_id: uuid.UUID) -> set[str]:
    return set(
        db.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        ).all()
    )


def test_bootstrap_creates_admin_identity_and_role(db: Session) -> None:
    result = bootstrap_admin_identity(db, email=EMAIL, subject=SUBJECT, display_name="Admin")

    assert result.created_user is True
    assert result.created_identity is True
    assert result.granted_role is True

    user = db.scalar(select(User).where(User.email == EMAIL))
    assert user is not None
    assert user.is_active is True
    identity = db.scalar(
        select(UserIdentity).where(
            UserIdentity.user_id == user.id,
            UserIdentity.provider == "supabase",
        )
    )
    assert identity is not None
    assert identity.provider_subject == SUBJECT
    assert identity.verified_at is not None
    assert "brokerage_admin" in _role_codes(db, user.id)


def test_bootstrap_is_idempotent(db: Session) -> None:
    first = bootstrap_admin_identity(db, email=EMAIL, subject=SUBJECT, display_name="Admin")
    second = bootstrap_admin_identity(db, email=EMAIL, subject=SUBJECT, display_name="Admin")

    assert first.granted_role is True
    assert second.created_user is False
    assert second.created_identity is False
    assert second.granted_role is False


def test_subject_already_linked_to_another_account_is_refused(db: Session) -> None:
    other = User(email="other@keeperfinancial.test", display_name="Other")
    db.add(other)
    db.flush()
    db.add(UserIdentity(user_id=other.id, provider="supabase", provider_subject=SUBJECT))
    db.flush()

    with pytest.raises(AdminBootstrapError, match="different account"):
        bootstrap_admin_identity(db, email=EMAIL, subject=SUBJECT, display_name="Admin")


def test_account_with_different_identity_is_refused(db: Session) -> None:
    user = User(email=EMAIL, display_name="Admin")
    db.add(user)
    db.flush()
    db.add(
        UserIdentity(
            user_id=user.id,
            provider="supabase",
            provider_subject=str(uuid.uuid4()),
        )
    )
    db.flush()

    with pytest.raises(AdminBootstrapError, match="different Supabase identity"):
        bootstrap_admin_identity(db, email=EMAIL, subject=SUBJECT, display_name="Admin")


def test_inactive_account_is_refused(db: Session) -> None:
    user = User(email=EMAIL, display_name="Admin", is_active=False)
    db.add(user)
    db.flush()

    with pytest.raises(AdminBootstrapError, match="inactive"):
        bootstrap_admin_identity(db, email=EMAIL, subject=SUBJECT, display_name="Admin")


def test_invalid_email_and_subject_are_refused(db: Session) -> None:
    with pytest.raises(AdminBootstrapError, match="email"):
        bootstrap_admin_identity(db, email="not-an-email", subject=SUBJECT, display_name="Admin")
    with pytest.raises(AdminBootstrapError, match="UUID"):
        bootstrap_admin_identity(db, email=EMAIL, subject="not-a-uuid", display_name="Admin")
