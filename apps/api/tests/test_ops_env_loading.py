"""The host ops scripts must read the deployment environment file the same way.

Background: `compose.yaml` reads `env_file: ${KEEPER_ENV_FILE:-.env}`, but the
host-level scripts (backup, restore, alert, monitor) run *outside* Compose and
used to read only `os.environ`. A cron run therefore reported
`backup-minio: missing settings: MINIO_ROOT_USER, MINIO_ROOT_PASSWORD` no matter
what the deployment `.env` contained, and `BACKUP_ENCRYPTION_KEY_FILE` was never
picked up, so the PostgreSQL dump was written unencrypted without any warning.

These tests pin the single resolution order and the parsing rules, and assert
that the bash loader and the Python loader agree — a divergence between the two
is exactly how the original bug hid.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from keeper_api.services.ops_env import (
    DEFAULT_ENV_FILENAME,
    load_env_file,
    parse_env_text,
    repo_root,
    resolve_env_file,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "scripts"
BASH: str = shutil.which("bash") or ""
requires_bash = pytest.mark.skipif(not BASH, reason="bash is required for the shell loader")

FIXTURE = """\
# a comment line

MINIO_ROOT_USER=quiet-otter
MINIO_ROOT_PASSWORD="quoted secret value"
MINIO_BUCKET=keeper-private
KEEPER_ISOLATED_VALUE='single quoted'
WITH_HASH=abc#def
export EXPORTED_STYLE=yes
INVALID-KEY=ignored
9LEADING_DIGIT=ignored
"""

EXPECTED = {
    "MINIO_ROOT_USER": "quiet-otter",
    "MINIO_ROOT_PASSWORD": "quoted secret value",
    "MINIO_BUCKET": "keeper-private",
    "KEEPER_ISOLATED_VALUE": "single quoted",
    "WITH_HASH": "abc#def",
    "EXPORTED_STYLE": "yes",
}


def test_parse_env_text_handles_comments_quotes_and_invalid_keys() -> None:
    assert parse_env_text(FIXTURE) == EXPECTED


def test_resolve_env_file_defaults_to_repo_root_dot_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KEEPER_ENV_FILE", raising=False)
    assert resolve_env_file(root=REPO_ROOT) == REPO_ROOT / DEFAULT_ENV_FILENAME


def test_resolve_env_file_honours_keeper_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KEEPER_ENV_FILE", ".env.production")
    assert resolve_env_file(root=REPO_ROOT) == REPO_ROOT / ".env.production"
    monkeypatch.setenv("KEEPER_ENV_FILE", "/etc/keeper/deploy.env")
    assert resolve_env_file(root=REPO_ROOT) == Path("/etc/keeper/deploy.env")


def test_load_env_file_does_not_clobber_real_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "deploy.env"
    env_file.write_text(FIXTURE, encoding="utf-8")
    monkeypatch.setenv("MINIO_ROOT_USER", "explicit-wins")
    for key in EXPECTED:
        if key != "MINIO_ROOT_USER":
            monkeypatch.delenv(key, raising=False)

    loaded = load_env_file(env_file, root=tmp_path)

    assert loaded == env_file
    assert os.environ["MINIO_ROOT_USER"] == "explicit-wins"
    assert os.environ["MINIO_ROOT_PASSWORD"] == "quoted secret value"


def test_load_env_file_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_env_file(tmp_path / "absent.env", root=tmp_path) is None


@requires_bash
def test_bash_and_python_loaders_agree(tmp_path: Path) -> None:
    """A value must never load differently depending on which script read it."""
    env_file = tmp_path / "deploy.env"
    env_file.write_text(FIXTURE, encoding="utf-8")

    script = (
        f'. "{SCRIPTS / "lib" / "load_env.sh"}"\n'
        "keeper_load_env\n"
        "for key in MINIO_ROOT_USER MINIO_ROOT_PASSWORD MINIO_BUCKET "
        "KEEPER_ISOLATED_VALUE WITH_HASH EXPORTED_STYLE; do\n"
        '  printf "%s=%s\\n" "$key" "${!key-}"\n'
        "done\n"
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in EXPECTED and key != "KEEPER_ENV_FILE"
    }
    environment["KEEPER_ENV_FILE"] = str(env_file)

    completed = subprocess.run(  # noqa: S603 - fixed argv, absolute interpreter
        [BASH, "-c", script],
        capture_output=True,
        text=True,
        env=environment,
        cwd=tmp_path,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"bash loader exited {completed.returncode}\n"
            f"stdout={completed.stdout!r}\nstderr={completed.stderr!r}"
        )
    exported = dict(line.split("=", 1) for line in completed.stdout.splitlines() if "=" in line)

    assert exported == EXPECTED


@requires_bash
def test_bash_loader_ignores_missing_file(tmp_path: Path) -> None:
    script = f'. "{SCRIPTS / "lib" / "load_env.sh"}"\nkeeper_load_env\necho loaded\n'
    environment = {**os.environ, "KEEPER_ENV_FILE": str(tmp_path / "absent.env")}
    completed = subprocess.run(  # noqa: S603 - fixed argv, absolute interpreter
        [BASH, "-c", script],
        capture_output=True,
        text=True,
        env=environment,
        cwd=tmp_path,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"bash loader exited {completed.returncode}\n"
            f"stdout={completed.stdout!r}\nstderr={completed.stderr!r}"
        )
    assert completed.stdout.strip() == "loaded"


def test_ops_scripts_source_the_shared_loader() -> None:
    """Guard the class of bug: every host script that reads settings must load them."""
    for name in ("backup_all.sh", "backup_postgres.sh", "monitor_health.sh"):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "lib/load_env.sh" in text, f"{name} does not source the shared loader"
        assert "keeper_load_env" in text, f"{name} never calls keeper_load_env"

    for name in ("backup_minio.py", "restore_minio.py", "send_alert.py"):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "load_env_file" in text, f"{name} does not load the deployment env file"


def test_backup_minio_reads_credentials_from_env_file(tmp_path: Path) -> None:
    """The reported failure: creds in .env, script still reported them missing."""
    env_file = tmp_path / "deploy.env"
    env_file.write_text(
        "MINIO_ROOT_USER=quiet-otter\n"
        "MINIO_ROOT_PASSWORD=quiet-otter-secret\n"
        "MINIO_ENDPOINT=http://127.0.0.1:1\n",
        encoding="utf-8",
    )
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("MINIO_") and key != "KEEPER_ENV_FILE"
    }
    environment["KEEPER_ENV_FILE"] = str(env_file)

    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [
            sys.executable,
            str(SCRIPTS / "backup_minio.py"),
            str(tmp_path / "mirror"),
        ],
        capture_output=True,
        text=True,
        env=environment,
        cwd=tmp_path,
    )

    assert "missing settings" not in completed.stderr
    # It now gets as far as talking to (an absent) MinIO, which fails closed.
    assert completed.returncode != 0


def test_backup_minio_still_fails_closed_without_credentials(tmp_path: Path) -> None:
    env_file = tmp_path / "empty.env"
    env_file.write_text("# no credentials here\n", encoding="utf-8")
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("MINIO_") and key != "KEEPER_ENV_FILE"
    }
    environment["KEEPER_ENV_FILE"] = str(env_file)

    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [
            sys.executable,
            str(SCRIPTS / "backup_minio.py"),
            str(tmp_path / "mirror"),
        ],
        capture_output=True,
        text=True,
        env=environment,
        cwd=tmp_path,
    )

    assert completed.returncode == 2
    assert "missing settings: MINIO_ROOT_USER, MINIO_ROOT_PASSWORD" in completed.stderr


def test_repo_root_derivation_matches_this_test_file() -> None:
    assert repo_root() == REPO_ROOT
