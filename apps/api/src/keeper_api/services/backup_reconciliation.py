"""Restore-time deletion reconciliation (decision 49 P0 safety gate).

Before a restored environment returns to service, verify that no record deleted
after the backup was created is silently resurrected. This is a *safety gate*,
not a purge engine: retention/deletion is deferred under decision 49, so today
the deletion ledger may be absent or empty. The gate fails closed when the
ledger is unavailable unless the caller explicitly opts into
``allow_missing_ledger`` (which still returns a result, never a "clean pass").

Ledger format (JSON Lines), one deletion per line::

    {"record_id": "<opaque id>", "deleted_at": "2026-10-14T12:00:00+00:00"}

``deleted_at`` must be an ISO-8601 datetime. Comparison is safe only when both
``deleted_at`` and the supplied ``backup_time`` carry the same awareness; the
caller (CLI) treats a mixed naive/aware comparison as a fail-closed error.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class ReconcileError(ValueError):
    """Raised when the safety gate cannot be satisfied (fail closed)."""


@dataclass(frozen=True)
class Deletion:
    record_id: str
    deleted_at: datetime


def load_deletion_ledger(path: str | Path) -> list[Deletion]:
    ledger = Path(path)
    if not ledger.is_file():
        raise ReconcileError(f"deletion ledger is unavailable: {path}")

    deletions: list[Deletion] = []
    for line_no, raw in enumerate(ledger.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            record_id = entry["record_id"]
            deleted_at = datetime.fromisoformat(entry["deleted_at"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ReconcileError(f"deletion ledger line {line_no} is malformed") from exc
        deletions.append(Deletion(record_id=str(record_id), deleted_at=deleted_at))
    return deletions


def deleted_after(deletions: list[Deletion], backup_time: datetime) -> set[str]:
    """Record ids deleted after the backup was created (must not resurrect)."""
    must_not_restore: set[str] = set()
    for deletion in deletions:
        try:
            is_after = deletion.deleted_at > backup_time
        except TypeError as exc:  # naive vs aware
            raise ReconcileError(
                "deleted_at and backup_time must use consistent timezone awareness"
            ) from exc
        if is_after:
            must_not_restore.add(deletion.record_id)
    return must_not_restore


def reconcile_restore(
    ledger_path: str | Path,
    backup_time: datetime,
    *,
    allow_missing_ledger: bool = False,
) -> set[str]:
    """Return the records deleted after ``backup_time`` (must not resurrect).

    Raises ``ReconcileError`` when the ledger is unavailable or malformed, or
    when timestamps mix naive/aware — unless ``allow_missing_ledger`` is set, in
    which case a missing ledger is treated as empty (still not a clean pass).
    """
    try:
        deletions = load_deletion_ledger(ledger_path)
    except ReconcileError:
        if allow_missing_ledger:
            deletions = []
        else:
            raise
    return deleted_after(deletions, backup_time)


def resurrection_conflicts(must_not_restore: set[str], present_ids: set[str]) -> set[str]:
    """Record ids a restore would resurrect (deleted after backup, now present)."""
    return must_not_restore & present_ids
