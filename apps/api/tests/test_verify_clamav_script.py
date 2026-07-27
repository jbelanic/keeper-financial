from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

from keeper_api.services.malware_scanner import ScanDecision

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = PROJECT_ROOT / "apps" / "api" / "scripts" / "verify_clamav.py"
SPEC = importlib.util.spec_from_file_location("verify_clamav", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
verify_clamav = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_clamav)


def test_eicar_bytes_are_assembled_only_at_runtime_and_match_standard_hashes() -> None:
    marker = verify_clamav.build_eicar_bytes()

    assert len(marker) == 68
    assert (
        hashlib.md5(marker, usedforsecurity=False).hexdigest() == "44d88612fea8a8f36de82e1278abb02f"
    )
    assert hashlib.sha1(marker, usedforsecurity=False).hexdigest() == (
        "3395856ce81f2b7382dee72602f798b642f14140"
    )

    for directory in [
        PROJECT_ROOT / "apps",
        PROJECT_ROOT / "docs",
        PROJECT_ROOT / "infrastructure",
    ]:
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".md", ".toml", ".yaml", ".yml"}:
                assert marker not in path.read_bytes(), path


def test_verifier_requires_clean_ok_and_eicar_found_without_printing_bytes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    decisions = iter(
        [
            ScanDecision(status="clean", source="clamav"),
            ScanDecision(status="rejected", source="clamav"),
        ]
    )

    class StubScanner:
        def __init__(self, _settings: object) -> None:
            pass

        def scan(self, _content: bytes) -> ScanDecision:
            return next(decisions)

    monkeypatch.setattr(verify_clamav, "ClamAVScanner", StubScanner)

    assert verify_clamav.main(["--host", "127.0.0.1", "--port", "3310"]) == 0
    output = capsys.readouterr().out
    assert output.splitlines() == ["clean: OK", "EICAR: FOUND"]
    assert verify_clamav.build_eicar_bytes().decode() not in output


def test_verifier_exits_nonzero_on_any_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    class IncorrectScanner:
        def __init__(self, _settings: object) -> None:
            pass

        def scan(self, _content: bytes) -> ScanDecision:
            return ScanDecision(status="clean", source="clamav")

    monkeypatch.setattr(verify_clamav, "ClamAVScanner", IncorrectScanner)

    assert verify_clamav.main([]) == 1
