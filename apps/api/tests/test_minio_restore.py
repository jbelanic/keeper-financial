from __future__ import annotations

from pathlib import Path

import pytest

from keeper_api.services.minio_restore import (
    LIVE_BUCKET,
    MinIORestoreError,
    MinIORestoreResult,
    mirror_object_keys,
    restore_mirror,
)


def test_mirror_object_keys_returns_sorted_relative_paths(tmp_path: Path) -> None:
    (tmp_path / "snapshots").mkdir()
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "snapshots" / "b.bin").write_bytes(b"b")

    assert mirror_object_keys(tmp_path) == [Path("a.txt"), Path("snapshots") / "b.bin"]


def test_mirror_object_keys_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(MinIORestoreError, match="not found"):
        mirror_object_keys(tmp_path / "nope")


def test_mirror_object_keys_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(MinIORestoreError, match="empty"):
        mirror_object_keys(tmp_path)


def test_restore_mirror_refuses_live_bucket_without_override(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    with pytest.raises(MinIORestoreError, match="live bucket"):
        restore_mirror(
            tmp_path,
            LIVE_BUCKET,
            endpoint_url="http://127.0.0.1:9000",
            access_key="k",
            secret_key="s",
        )


def test_restore_mirror_requires_bucket(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    with pytest.raises(MinIORestoreError, match="required"):
        restore_mirror(
            tmp_path,
            "",
            endpoint_url="http://127.0.0.1:9000",
            access_key="k",
            secret_key="s",
        )


class _FakeClient:
    def __init__(self) -> None:
        self.uploads: list[tuple[str, str, str]] = []

    def upload_file(self, src: str, bucket: str, key: str) -> None:
        self.uploads.append((src, bucket, key))


def test_restore_mirror_uploads_every_object_key(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "a.txt").write_text("aaa")
    (tmp_path / "snapshots").mkdir()
    (tmp_path / "snapshots" / "b.bin").write_bytes(b"bb")
    fake = _FakeClient()
    monkeypatch.setattr(
        "keeper_api.services.minio_restore.boto3.client",
        lambda *args, **kwargs: fake,
    )

    result = restore_mirror(
        tmp_path,
        "keeper-restore-test",
        endpoint_url="http://127.0.0.1:9000",
        access_key="k",
        secret_key="s",
    )

    assert result == MinIORestoreResult(bucket="keeper-restore-test", objects=2, total_bytes=5)
    assert sorted(key for _, _, key in fake.uploads) == ["a.txt", "snapshots/b.bin"]
