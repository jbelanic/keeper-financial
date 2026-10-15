from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError

from keeper_api.services.consent_approval import (
    ConsentApprovalError,
    approve_consent_real_data,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Approve the active borrower consent-catalog entry for real-data submission."
    )
    parser.add_argument("--version", required=True, help="Exact consent version")
    parser.add_argument("--digest", required=True, help="Exact wording digest")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.environ.get("APP_ENV") != "production":
        print(
            "Consent real-data approval requires explicit APP_ENV=production.",
            file=sys.stderr,
        )
        return 2

    from keeper_api.core.config import get_settings
    from keeper_api.db.session import SessionLocal

    settings = get_settings()
    if settings.app_env != "production":
        print(
            "Consent real-data approval is unavailable outside production.",
            file=sys.stderr,
        )
        return 2

    try:
        with SessionLocal.begin() as db:
            result = approve_consent_real_data(
                db,
                consent_version=args.version,
                wording_digest=args.digest,
            )
    except ConsentApprovalError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("The consent real-data approval could not be completed.", file=sys.stderr)
        return 1

    print(f"Consent real-data approval: entry_id={result.entry_id} changed={result.changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
