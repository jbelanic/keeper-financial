"""Deployment environment-file loading for host-level ops scripts.

The backup, restore, alert and monitor scripts run *outside* Docker, but every
setting they need lives in the deployment environment file that Compose reads
(``env_file: ${KEEPER_ENV_FILE:-.env}`` in ``compose.yaml``). Compose reads that
file for the containers; nothing used to read it for the host scripts, so a
script that only looked at ``os.environ`` saw nothing when run from cron.

This module gives every ops script one resolution order and one default:

1. an explicit ``override`` argument,
2. ``$KEEPER_ENV_FILE`` (the same override Compose and the Makefile use),
3. ``<repo root>/.env``.

Existing process environment variables always win, so an operator can override a
single value for one run (``MINIO_ROOT_USER=... ./scripts/backup_all.sh``).

A missing file is not an error here: callers decide whether *their* required
settings are missing, and fail closed on those. The parser is deliberately
dependency-free and line-based, and ``scripts/lib/load_env.sh`` implements the
same rules for the bash scripts; ``tests/test_ops_env_loading.py`` asserts the
two implementations agree, so a value can never load differently depending on
which script read it.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_ENV_FILENAME = ".env"

#: Depth from this file (apps/api/src/keeper_api/services/) up to the repo root.
_REPO_ROOT_DEPTH = 5


def repo_root() -> Path:
    """Return the repository root derived from this file's location."""
    return Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]


def resolve_env_file(
    override: str | os.PathLike[str] | None = None,
    *,
    root: Path | None = None,
) -> Path:
    """Resolve the deployment environment file path without reading it."""
    base = root if root is not None else repo_root()
    candidate = override or os.environ.get("KEEPER_ENV_FILE") or DEFAULT_ENV_FILENAME
    path = Path(candidate)
    return path if path.is_absolute() else base / path


def _valid_key(key: str) -> bool:
    if not key or key[0].isdigit():
        return False
    return all(character.isalnum() or character == "_" for character in key)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_text(text: str) -> dict[str, str]:
    """Parse ``KEY=value`` lines the same way ``scripts/lib/load_env.sh`` does.

    Blank lines and lines whose first non-space character is ``#`` are ignored.
    A value may be wrapped in one layer of matching single or double quotes.
    Inline ``#`` comments are *not* stripped, so a value that legitimately
    contains ``#`` round-trips unchanged; keep comments on their own lines.
    """
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export ") :].strip()
        if not _valid_key(key):
            continue
        values[key] = _strip_quotes(value.strip())
    return values


def load_env_file(
    override: str | os.PathLike[str] | None = None,
    *,
    root: Path | None = None,
) -> Path | None:
    """Load the deployment environment file into ``os.environ``.

    Returns the path that was read, or ``None`` when no file exists. Values are
    applied with ``setdefault`` so real environment variables are never
    overwritten.
    """
    path = resolve_env_file(override, root=root)
    if not path.is_file():
        return None
    for key, value in parse_env_text(path.read_text(encoding="utf-8")).items():
        os.environ.setdefault(key, value)
    return path
