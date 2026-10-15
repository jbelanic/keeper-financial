"""Production administrator identity bootstrap (decision 49 follow-up).

Links one explicit hosted-Supabase identity to a ``brokerage_admin`` account.
This is the operator-only counterpart to the local-only
``link_local_admin_identity`` command: it never runs in ``APP_ENV=local``, never
links by matching email alone, never uses service-role credentials, and never
overwrites a genuine non-placeholder provider subject. The caller supplies the
exact Supabase subject UUID and verified email from the hosted project dashboard.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.orm import Session

from keeper_api.models.domain import Role, User, UserIdentity, UserRole
from keeper_api.services.audit import AuditService


class AdminBootstrapError(ValueError):
    """Raised when an administrator identity bootstrap is refused (fail closed)."""


@dataclass(frozen=True)
class AdminBootstrapResult:
    user_id: uuid.UUID
    created_user: bool
    created_identity: bool
    granted_role: bool


def _normalize_email(value: str) -> str:
    try:
        normalized = validate_email(
            value.strip(), check_deliverability=False, test_environment=True
        ).normalized.lower()
    except EmailNotValidError as exc:
        raise AdminBootstrapError("A valid administrator email is required.") from exc
    if len(normalized) > 320:
        raise AdminBootstrapError("A valid administrator email is required.")
    return normalized


def _normalize_subject(value: str) -> str:
    try:
        return str(uuid.UUID(value.strip()))
    except (AttributeError, ValueError) as exc:
        raise AdminBootstrapError("A valid Supabase user UUID is required.") from exc


def bootstrap_admin_identity(
    db: Session,
    *,
    email: str,
    subject: str,
    display_name: str,
    actor_user_id: uuid.UUID | None = None,
) -> AdminBootstrapResult:
    normalized_email = _normalize_email(email)
    normalized_subject = _normalize_subject(subject)
    name = display_name.strip()
    if not name:
        raise AdminBootstrapError("A display name is required.")

    audit = AuditService(db)

    subject_identity = db.scalar(
        select(UserIdentity)
        .where(
            UserIdentity.provider == "supabase",
            UserIdentity.provider_subject == normalized_subject,
        )
        .with_for_update()
    )
    user = db.scalar(select(User).where(User.email == normalized_email).with_for_update())

    # The exact Supabase subject must not already be linked to a different account.
    if subject_identity is not None and (user is None or subject_identity.user_id != user.id):
        raise AdminBootstrapError("The Supabase subject is already linked to a different account.")

    created_user = False
    if user is None:
        user = User(email=normalized_email, display_name=name, is_active=True)
        db.add(user)
        db.flush()
        created_user = True
    elif not user.is_active:
        raise AdminBootstrapError("The administrator account is inactive.")

    # Never overwrite a genuine existing Supabase identity on this account.
    created_identity = False
    if subject_identity is None:
        other_identity = db.scalar(
            select(UserIdentity).where(
                UserIdentity.user_id == user.id,
                UserIdentity.provider == "supabase",
            )
        )
        if other_identity is not None:
            raise AdminBootstrapError("The account already has a different Supabase identity.")
        subject_identity = UserIdentity(
            user_id=user.id,
            provider="supabase",
            provider_subject=normalized_subject,
            verified_at=datetime.now(UTC),
        )
        db.add(subject_identity)
        db.flush()
        created_identity = True
        audit.record(
            "user_identity.linked",
            "user_identity",
            subject_identity.id,
            actor_user_id=actor_user_id,
            safe_metadata={"provider": "supabase", "source": "admin_bootstrap"},
        )
    elif subject_identity.verified_at is None:
        subject_identity.verified_at = datetime.now(UTC)
        db.flush()

    admin_role = db.scalar(select(Role).where(Role.code == "brokerage_admin"))
    if admin_role is None:
        admin_role = Role(code="brokerage_admin", description="Brokerage administration access")
        db.add(admin_role)
        db.flush()

    granted_role = False
    existing_grant = db.scalar(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role_id == admin_role.id,
        )
    )
    if existing_grant is None:
        grant = UserRole(user_id=user.id, role_id=admin_role.id, granted_by_user_id=None)
        db.add(grant)
        db.flush()
        granted_role = True
        audit.record(
            "role.granted",
            "user_role",
            grant.id,
            actor_user_id=actor_user_id,
            safe_metadata={"role": "brokerage_admin", "source": "admin_bootstrap"},
        )

    audit.record(
        "admin_identity.bootstrapped",
        "user",
        user.id,
        actor_user_id=actor_user_id,
        safe_metadata={
            "created_user": created_user,
            "created_identity": created_identity,
            "granted_role": granted_role,
        },
    )

    return AdminBootstrapResult(
        user_id=user.id,
        created_user=created_user,
        created_identity=created_identity,
        granted_role=granted_role,
    )
