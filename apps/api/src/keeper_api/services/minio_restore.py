"""Restore a Keeper MinIO mirror into a bucket (decision 49 P0 follow-up).

``scripts/backup_minio.py`` mirrors the live bucket to a local directory named
``<bucket>-<ts>``. This module restores that mirror back into a bucket, preserving
object keys, for the isolated restore drill. Backup and restore are opposite
directions: the backup scripts copy *live → local* only; there is no automated
``restore_all`` counterpart. This module is the restore leg for MinIO.

Fail closed: it refuses the live ``keeper-private`` bucket unless the caller opts
in, and refuses a missing or empty mirror.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.config import Config

LIVE_BUCKET = "keeper-private"


class MinIORestoreError(ValueError):
    """Raised when a MinIO restore is refused (fail closed)."""


@dataclass(frozen=True)
class MinIORestoreResult:
    bucket: str
    objects: int
    total_bytes: int


def mirror_object_keys(mirror_dir: str | Path) -> list[Path]:
    """Return the relative file paths in a mirror directory (the object keys)."""
    root = Path(mirror_dir)
    if not root.is_dir():
        raise MinIORestoreError(f"mirror directory not found: {root}")
    keys = sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())
    if not keys:
        raise MinIORestoreError(f"mirror directory is empty: {root}")
    return keys


def restore_mirror(
    mirror_dir: str | Path,
    bucket: str,
    *,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    region: str = "us-east-1",
    allow_live_bucket: bool = False,
) -> MinIORestoreResult:
    """Upload every object in ``mirror_dir`` into an existing ``bucket``.

    The destination bucket must already exist; the isolated-drill operator creates
    it first. ``allow_live_bucket`` is required to write into ``keeper-private``.
    """
    bucket = (bucket or "").strip()
    if not bucket:
        raise MinIORestoreError("a destination bucket is required")
    if bucket == LIVE_BUCKET and not allow_live_bucket:
        raise MinIORestoreError(
            f"refusing to restore into the live bucket {LIVE_BUCKET!r}; "
            "pass --allow-live-bucket to override (isolated restore only)"
        )

    keys = mirror_object_keys(mirror_dir)
    root = Path(mirror_dir)

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    total_bytes = 0
    for rel in keys:
        client.upload_file(str(root / rel), bucket, str(rel))
        total_bytes += (root / rel).stat().st_size
    return MinIORestoreResult(bucket=bucket, objects=len(keys), total_bytes=total_bytes)
