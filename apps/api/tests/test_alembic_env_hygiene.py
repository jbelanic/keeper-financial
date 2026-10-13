"""Regression guard: Alembic migrations perform schema work only.

An unapproved, never-committed change once added a MinIO bucket-creation side
effect (``ensure_minio_bucket``) to ``apps/api/alembic/env.py``. Migrations must
not touch object storage or the network: private-bucket provisioning belongs to
the Compose ``minio-init`` step or a documented operator action (see decisions
46/47 and ``docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md``). This guard
fails if that side effect is reintroduced.
"""

from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_ENV = API_ROOT / "alembic" / "env.py"

# Tokens that must never appear in the migration entrypoint: an object-store or
# network side effect inside a migration bootstrap is a defect, not a shortcut.
FORBIDDEN_TOKENS = (
    "minio",
    "boto3",
    "botocore",
    "urllib",
    "requests",
    "bucket",
    "s3_",
    "aws4",
    "sigv4",
)


def test_alembic_env_exists() -> None:
    assert ALEMBIC_ENV.is_file(), f"missing migration entrypoint: {ALEMBIC_ENV}"


def test_alembic_env_has_no_object_storage_or_network_side_effects() -> None:
    source = ALEMBIC_ENV.read_text(encoding="utf-8").lower()
    offenders = sorted({token for token in FORBIDDEN_TOKENS if token in source})
    assert not offenders, (
        "apps/api/alembic/env.py must perform schema migrations only; found "
        f"object-storage/network side-effect tokens: {offenders}"
    )


def test_alembic_env_does_not_import_application_services() -> None:
    source = ALEMBIC_ENV.read_text(encoding="utf-8")
    assert "keeper_api.services" not in source, (
        "apps/api/alembic/env.py must not import application services "
        "(storage/scanner/etc.) into the migration bootstrap"
    )
