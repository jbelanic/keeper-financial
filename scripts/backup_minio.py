#!/usr/bin/env python3
"""Mirror the private Keeper MinIO bucket to a local directory (decision 49 P0).

Uses the application's own boto3/S3 stack (like ``scripts/init_minio_bucket.py``)
rather than the ``minio/mc`` image, which is glibc-based and cannot run on the
below-baseline target host (SIGILL / exit 132, decision 47). Objects are
application-level ciphertext already, so this mirrors bytes without re-encrypting
and never logs object keys or signed URLs.

Usage:
  .venv/bin/python scripts/backup_minio.py [DEST_DIR]

Environment (from .env): MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD,
MINIO_BUCKET (default ``keeper-private``).
"""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import boto3
from botocore.config import Config

RETENTION_DAYS = 30


def main(argv: list[str]) -> int:
    missing = [
        name
        for name in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD")
        if not os.environ.get(name)
    ]
    if missing:
        print(f"backup-minio: missing settings: {', '.join(missing)}", file=sys.stderr)
        return 2

    dest_dir = Path(
        argv[0] if argv else os.environ.get("BACKUP_DIR", "/var/backups/keeper-minio")
    )
    bucket = os.environ.get("MINIO_BUCKET", "keeper-private")
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    out = dest_dir / f"{bucket}-{ts}"
    out.mkdir(parents=True, exist_ok=True)

    client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://127.0.0.1:9000"),
        aws_access_key_id=os.environ.get("MINIO_ROOT_USER"),
        aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD"),
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    count = 0
    total_bytes = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            target = out / key
            target.parent.mkdir(parents=True, exist_ok=True)
            client.download_file(bucket, key, str(target))
            count += 1
            total_bytes += int(obj["Size"])

    print(f"MANIFEST ts={ts} bucket={bucket} objects={count} bytes={total_bytes} dest={out}")

    # Rolling retention: keep the newest N daily mirrors.
    backups = sorted(
        (
            p
            for p in dest_dir.iterdir()
            if p.is_dir() and p.name.startswith(f"{bucket}-")
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for stale in backups[RETENTION_DAYS:]:
        shutil.rmtree(stale)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
