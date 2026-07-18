from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"{name} is required for the local API")
    return value


def main() -> None:
    env_file = Path(".env")
    if env_file.is_file():
        load_dotenv(env_file)

    # Host-run services use the loopback bindings published by Compose. The
    # API container keeps its explicit internal clamav/minio service settings.
    os.environ["CLAMAV_HOST"] = "127.0.0.1"
    os.environ["S3_ENDPOINT_URL"] = "http://127.0.0.1:9000"
    os.environ["S3_ACCESS_KEY_ID"] = _required("MINIO_ROOT_USER")
    os.environ["S3_SECRET_ACCESS_KEY"] = _required("MINIO_ROOT_PASSWORD")
    if os.environ.get("MINIO_BUCKET", "").strip():
        os.environ["S3_BUCKET"] = os.environ["MINIO_BUCKET"]

    uvicorn.run(
        "keeper_api.main:app",
        app_dir="apps/api/src",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
