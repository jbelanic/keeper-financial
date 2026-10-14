#!/usr/bin/env python3
"""Restore-time deletion reconciliation CLI (decision 49 P0 safety gate).

Usage:
  reconcile_restore_deletions.py --ledger <file> --backup-time <ISO8601> \
      [--present <file-of-ids>] [--allow-missing-ledger]

``--present`` is an optional file of record ids (one per line) present in the
restored environment. When supplied, any id that was deleted after the backup
time and is also present is a resurrection conflict and the gate exits 1.

Exit codes:
  0 = no conflict (or only the must-not-restore set was requested);
  1 = resurrection conflict detected;
  2 = fail closed (ledger unavailable or malformed; mixed tz awareness).

Run inside the project venv: .venv/bin/python scripts/reconcile_restore_deletions.py …
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from keeper_api.services.backup_reconciliation import (
    ReconcileError,
    reconcile_restore,
    resurrection_conflicts,
)


def _read_present_ids(path: str | None) -> set[str] | None:
    if path is None:
        return None
    present = Path(path)
    if not present.is_file():
        raise ReconcileError(f"present-ids file is unavailable: {path}")
    return {line.strip() for line in present.read_text().splitlines() if line.strip()}


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, help="JSON-lines deletion ledger")
    parser.add_argument("--backup-time", required=True, help="backup ISO-8601 timestamp")
    parser.add_argument("--present", help="optional file of restored record ids")
    parser.add_argument(
        "--allow-missing-ledger",
        action="store_true",
        help="treat a missing ledger as empty (still not a clean pass)",
    )
    args = parser.parse_args(argv)

    try:
        backup_time = datetime.fromisoformat(args.backup_time)
    except ValueError:
        print(f"fail-closed: invalid backup-time: {args.backup_time}", file=sys.stderr)
        return 2

    try:
        present_ids = _read_present_ids(args.present)
        must_not_restore = reconcile_restore(
            args.ledger,
            backup_time,
            allow_missing_ledger=args.allow_missing_ledger,
        )
    except ReconcileError as exc:
        print(f"fail-closed: {exc}", file=sys.stderr)
        return 2

    if present_ids is not None:
        conflicts = resurrection_conflicts(must_not_restore, present_ids)
        if conflicts:
            print(
                "resurrection conflict: " + ", ".join(sorted(conflicts)),
                file=sys.stderr,
            )
            return 1

    print(
        f"RECONCILE_OK backup_time={args.backup_time} "
        f"must_not_restore={len(must_not_restore)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
