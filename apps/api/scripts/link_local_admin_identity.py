from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from keeper_api.models.domain import Role, User, UserIdentity, UserRole

SEEDED_ADMIN_SUBJECT = "00000000-0000-4000-8000-000000000002"


class LocalAdminIdentityLinkError(ValueError):
    """Bounded operator error for a refused local identity link."""


@dataclass(frozen=True)
class LinkResult:
    changed: bool


def normalize_email(value: str) -> str:
    try:
        normalized = validate_email(
            value.strip(), check_deliverability=False, test_environment=True
        ).normalized.lower()
    except EmailNotValidError as exc:
        raise LocalAdminIdentityLinkError("A valid administrator email is required.") from exc
    if len(normalized) > 320:
        raise LocalAdminIdentityLinkError("A valid administrator email is required.")
    return normalized


def normalize_subject(value: str) -> str:
    try:
        return str(uuid.UUID(value.strip()))
    except (AttributeError, ValueError) as exc:
        raise LocalAdminIdentityLinkError("A valid Supabase user UUID is required.") from exc


def link_local_admin_identity(
    db: Session,
    *,
    app_env: str,
    email: str,
    subject: str,
) -> LinkResult:
    if app_env != "local":
        raise LocalAdminIdentityLinkError("Local administrator linking requires APP_ENV=local.")

    normalized_email = normalize_email(email)
    normalized_subject = normalize_subject(subject)
    user = db.scalar(select(User).where(User.email == normalized_email).with_for_update())
    if user is None:
        raise LocalAdminIdentityLinkError("The local administrator account was not found.")
    if not user.is_active:
        raise LocalAdminIdentityLinkError("The local administrator account is inactive.")

    roles = set(
        db.scalars(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        ).all()
    )
    if "brokerage_admin" not in roles:
        raise LocalAdminIdentityLinkError(
            "The local account does not have the brokerage_admin role."
        )

    identities = list(
        db.scalars(
            select(UserIdentity)
            .where(
                UserIdentity.user_id == user.id,
                UserIdentity.provider == "supabase",
            )
            .with_for_update()
        ).all()
    )
    if len(identities) != 1:
        raise LocalAdminIdentityLinkError(
            "Exactly one existing Supabase identity is required for the local administrator."
        )
    identity = identities[0]

    duplicate = db.scalar(
        select(UserIdentity).where(
            UserIdentity.provider == "supabase",
            UserIdentity.provider_subject == normalized_subject,
            UserIdentity.user_id != user.id,
        )
    )
    if duplicate is not None:
        raise LocalAdminIdentityLinkError(
            "The Supabase subject is already linked to another local account."
        )

    if identity.provider_subject == normalized_subject:
        if identity.verified_at is None:
            identity.verified_at = datetime.now(UTC)
            db.flush()
            return LinkResult(changed=True)
        return LinkResult(changed=False)
    if identity.provider_subject != SEEDED_ADMIN_SUBJECT:
        raise LocalAdminIdentityLinkError(
            "The existing Supabase identity is not the approved seeded placeholder."
        )

    identity.provider_subject = normalized_subject
    identity.verified_at = datetime.now(UTC)
    db.flush()
    return LinkResult(changed=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Link a real local Supabase subject to a seeded local brokerage admin."
    )
    parser.add_argument("--email", required=True, help="Existing local administrator email")
    parser.add_argument("--subject", required=True, help="Local Supabase Auth user UUID")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.environ.get("APP_ENV") != "local":
        print("Local administrator linking requires explicit APP_ENV=local.", file=sys.stderr)
        return 2

    # Import only after the explicit environment guard so a non-local command
    # cannot initialize an application database connection.
    from keeper_api.core.config import get_settings
    from keeper_api.db.session import SessionLocal

    settings = get_settings()
    if settings.app_env != "local":
        print("Local administrator linking is unavailable outside local mode.", file=sys.stderr)
        return 2
    try:
        with SessionLocal.begin() as db:
            result = link_local_admin_identity(
                db,
                app_env=settings.app_env,
                email=args.email,
                subject=args.subject,
            )
    except LocalAdminIdentityLinkError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("The local administrator identity update could not be completed.", file=sys.stderr)
        return 1

    if result.changed:
        print("The local administrator identity was linked successfully.")
    else:
        print("The local administrator identity is already linked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
