from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from keeper_api.services.backup_reconciliation import (
    Deletion,
    ReconcileError,
    deleted_after,
    load_deletion_ledger,
    reconcile_restore,
    resurrection_conflicts,
)


def _ledger(tmp_path, lines: list[str]) -> str:
    path = tmp_path / "deletions.jsonl"
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def _deletions(*entries: tuple[str, datetime]) -> list[Deletion]:
    return [Deletion(record_id=r, deleted_at=t) for r, t in entries]


BACKUP = datetime(2026, 10, 14, 12, 0, 0, tzinfo=UTC)


def test_missing_ledger_fails_closed(tmp_path) -> None:
    missing = tmp_path / "nope.jsonl"
    with pytest.raises(ReconcileError, match="unavailable"):
        reconcile_restore(missing, BACKUP)


def test_missing_ledger_with_allow_is_empty_not_a_clean_pass(tmp_path) -> None:
    missing = tmp_path / "nope.jsonl"
    assert reconcile_restore(missing, BACKUP, allow_missing_ledger=True) == set()


def test_malformed_ledger_fails_closed(tmp_path) -> None:
    ledger = _ledger(tmp_path, ['{"record_id": "a", "deleted_at": "not-a-date"}'])
    with pytest.raises(ReconcileError, match="malformed"):
        reconcile_restore(ledger, BACKUP)


def test_deleted_after_returns_only_records_after_backup() -> None:
    deletions = _deletions(
        ("before", BACKUP - timedelta(days=1)),
        ("after", BACKUP + timedelta(days=1)),
        ("exactly", BACKUP),
    )
    assert deleted_after(deletions, BACKUP) == {"after"}


def test_reconcile_restore_returns_deleted_after_set(tmp_path) -> None:
    ledger = _ledger(
        tmp_path,
        [
            '{"record_id": "before", "deleted_at": "2026-10-13T12:00:00+00:00"}',
            '{"record_id": "after", "deleted_at": "2026-10-15T12:00:00+00:00"}',
        ],
    )
    assert reconcile_restore(ledger, BACKUP) == {"after"}


def test_mixed_timezone_awareness_fails_closed(tmp_path) -> None:
    ledger = _ledger(
        tmp_path,
        ['{"record_id": "a", "deleted_at": "2026-10-15T12:00:00+00:00"}'],
    )
    naive_backup = datetime(2026, 10, 14, 12, 0, 0)
    with pytest.raises(ReconcileError, match="timezone awareness"):
        reconcile_restore(ledger, naive_backup)


def test_resurrection_conflicts_are_detected() -> None:
    must_not_restore = {"a", "b"}
    present = {"b", "c"}
    assert resurrection_conflicts(must_not_restore, present) == {"b"}


def test_ledger_loader_returns_ordered_deletions(tmp_path) -> None:
    ledger = _ledger(
        tmp_path,
        [
            '{"record_id": "first", "deleted_at": "2026-10-15T12:00:00+00:00"}',
            '{"record_id": "second", "deleted_at": "2026-10-16T12:00:00+00:00"}',
        ],
    )
    deletions = load_deletion_ledger(ledger)
    assert [d.record_id for d in deletions] == ["first", "second"]
