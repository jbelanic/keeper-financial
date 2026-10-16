#!/usr/bin/env python3
"""Restore a Keeper MinIO mirror into a bucket (isolated restore drill).

The mirror directory is the one written by ``scripts/backup_minio.py`` (a directory
named ``<bucket>-<ts>``). Create the destination bucket first, then run:

    .venv/bin/python scripts/restore_minio.py <mirror-dir> --bucket <name>

Exit codes: 0 = restored; 1 = restore failed (fail closed); 2 = misconfigured.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from keeper_api.services.minio_restore import MinIORestoreError, restore_mirror


def _load_env() -> None:
    """Load the deployment environment file (see ``keeper_api.services.ops_env``).

    Resolution order and parsing rules live in one place so every host script
    reads the same file the same way: ``$KEEPER_ENV_FILE`` then ``<repo>/.env``,
    with real environment variables winning.
    """
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "apps" / "api" / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    from keeper_api.services.ops_env import load_env_file

    load_env_file(root=repo_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Restore a Keeper MinIO mirror into a bucket (isolated drill)."
    )
    parser.add_argument("mirror_dir", help="mirror directory written by backup_minio.py")
    parser.add_argument("--bucket", required=True, help="destination bucket (must exist)")
    parser.add_argument(
        "--allow-live-bucket",
        action="store_true",
        help="override the live-bucket guard (isolated restore only)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _load_env()

    endpoint = os.environ.get("MINIO_ENDPOINT", "http://127.0.0.1:9000")
    access_key = os.environ.get("MINIO_ROOT_USER", "")
    secret_key = os.environ.get("MINIO_ROOT_PASSWORD", "")
    if not access_key or not secret_key:
        print(
            "restore-minio: MINIO_ROOT_USER and MINIO_ROOT_PASSWORD are required",
            file=sys.stderr,
        )
        return 2

    try:
        result = restore_mirror(
            args.mirror_dir,
            args.bucket,
            endpoint_url=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            region=os.environ.get("S3_REGION", "us-east-1"),
            allow_live_bucket=args.allow_live_bucket,
        )
    except MinIORestoreError as exc:
        print(f"restore-minio: {exc}", file=sys.stderr)
        return 1

    print(
        f"RESTORE_OK bucket={result.bucket} objects={result.objects} "
        f"bytes={result.total_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
