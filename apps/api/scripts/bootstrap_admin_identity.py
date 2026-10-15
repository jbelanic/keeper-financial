from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError

from keeper_api.services.admin_bootstrap import (
    AdminBootstrapError,
    bootstrap_admin_identity,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap the first production brokerage administrator from a hosted Supabase identity."
    )
    parser.add_argument("--email", required=True, help="Administrator verified email address")
    parser.add_argument("--subject", required=True, help="Hosted Supabase Auth user UUID")
    parser.add_argument("--name", required=True, help="Administrator display name")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.environ.get("APP_ENV") != "production":
        print(
            "Administrator bootstrap requires explicit APP_ENV=production.",
            file=sys.stderr,
        )
        return 2

    # Import only after the explicit environment guard so a non-production command
    # cannot initialize an application database connection.
    from keeper_api.core.config import get_settings
    from keeper_api.db.session import SessionLocal

    settings = get_settings()
    if settings.app_env != "production":
        print(
            "Administrator bootstrap is unavailable outside production.",
            file=sys.stderr,
        )
        return 2

    try:
        with SessionLocal.begin() as db:
            result = bootstrap_admin_identity(
                db,
                email=args.email,
                subject=args.subject,
                display_name=args.name,
            )
    except AdminBootstrapError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("The administrator identity bootstrap could not be completed.", file=sys.stderr)
        return 1

    print(
        f"Administrator identity bootstrapped: user_id={result.user_id} "
        f"created_user={result.created_user} created_identity={result.created_identity} "
        f"granted_role={result.granted_role}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
