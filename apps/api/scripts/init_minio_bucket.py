"""Idempotently create the private Keeper object bucket.

Runs as the one-shot ``minio-init`` Compose service. It uses the application's
own boto3/S3 stack rather than a second registry image: the official
``quay.io/minio/mc`` image is glibc-based and cannot execute on the
below-baseline target host (SIGILL / exit 132, decision 47), whereas the API
image already runs there and keeps the local and target stacks aligned.

Bucket provisioning must never live inside Alembic migrations (decision 47; see
``apps/api/tests/test_alembic_env_hygiene.py``). This script is the supported,
idempotent one-shot path; the private bucket is created without any anonymous
policy, so objects stay private by default.
"""

from __future__ import annotations

import os
import sys

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

REQUIRED_SETTINGS = (
    "S3_ENDPOINT_URL",
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "S3_BUCKET",
)
MISSING_BUCKET_CODES = {"404", "NoSuchBucket", "NotFound"}
ALREADY_EXISTS_CODES = {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}


def main() -> int:
    missing = [name for name in REQUIRED_SETTINGS if not os.environ.get(name)]
    if missing:
        print(f"minio-init: missing required settings: {', '.join(missing)}", file=sys.stderr)
        return 2

    bucket = os.environ["S3_BUCKET"]
    client = boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("S3_REGION", "us-east-1"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in MISSING_BUCKET_CODES:
            print(f"minio-init: bucket check failed: {code or exc}", file=sys.stderr)
            return 1
    else:
        print(f"minio-init: private bucket '{bucket}' already exists")
        return 0

    try:
        client.create_bucket(Bucket=bucket)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in ALREADY_EXISTS_CODES:
            print(f"minio-init: bucket creation failed: {code or exc}", file=sys.stderr)
            return 1
    print(f"minio-init: created private bucket '{bucket}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
