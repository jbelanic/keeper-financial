from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from keeper_api.core.config import Settings
from keeper_api.services.malware_scanner import ClamAVScanner, MalwareScannerUnavailable


def build_eicar_bytes() -> bytes:
    fragments = (
        b"X5O!P%@AP[4",
        bytes((92,)),
        b"PZX54(P^)7CC)7}$EI",
        b"CAR-STANDARD-ANTIVIRUS-",
        b"TEST-FILE!$H+H*",
    )
    return b"".join(fragments)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a local clamd INSTREAM endpoint safely")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3310)
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    options = _parser().parse_args(arguments)
    settings = Settings(
        _env_file=None,
        app_env="local",
        database_url="sqlite+pysqlite:///:memory:",
        storage_backend="local",
        malware_scanner_backend="clamav",
        clamav_host=options.host,
        clamav_port=options.port,
    )
    scanner = ClamAVScanner(settings)
    try:
        clean = scanner.scan(b"Keeper local ClamAV verification sample.")
        marker = scanner.scan(build_eicar_bytes())
    except MalwareScannerUnavailable:
        print("verification: scanner unavailable", file=sys.stderr)
        return 1
    if clean.status != "clean":
        print("clean: MISMATCH")
        return 1
    print("clean: OK")
    if marker.status != "rejected":
        print("EICAR: MISMATCH")
        return 1
    print("EICAR: FOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
