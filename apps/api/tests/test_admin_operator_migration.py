from __future__ import annotations

import os
import uuid
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from keeper_api.core.config import get_settings

API_ROOT = Path(__file__).resolve().parents[1]
RUN_POSTGRES = os.getenv("KEEPER_RUN_SCHEMA_MIGRATION_E2E") == "1"


@pytest.fixture
def temporary_postgres_url() -> Generator[str, None, None]:
    if not RUN_POSTGRES:
        pytest.skip("set KEEPER_RUN_SCHEMA_MIGRATION_E2E=1 to run PostgreSQL migration tests")

    base_url = make_url(get_settings().database_url)
    if not base_url.drivername.startswith("postgresql"):
        pytest.skip("PostgreSQL migration tests require a PostgreSQL DATABASE_URL")

    database_name = f"keeper_admin_migration_test_{uuid.uuid4().hex}"
    admin_engine = create_engine(
        base_url.set(database="postgres"), isolation_level="AUTOCOMMIT", pool_pre_ping=True
    )
    quoted_database = admin_engine.dialect.identifier_preparer.quote_identifier(database_name)
    created = False
    try:
        with admin_engine.connect() as connection:
            connection.exec_driver_sql(f"CREATE DATABASE {quoted_database}")
            created = True
        yield base_url.set(database=database_name).render_as_string(hide_password=False)
    finally:
        if created:
            with admin_engine.connect() as connection:
                connection.execute(
                    text(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                    ),
                    {"database_name": database_name},
                )
                connection.exec_driver_sql(f"DROP DATABASE {quoted_database}")
        admin_engine.dispose()


@contextmanager
def _alembic_config(database_url: str) -> Iterator[Config]:
    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    try:
        yield config
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url
        get_settings.cache_clear()


def _upgrade(database_url: str, revision: str) -> None:
    with _alembic_config(database_url) as config:
        command.upgrade(config, revision)


def _seed_candidate(connection) -> dict[str, uuid.UUID]:  # type: ignore[no-untyped-def]
    identifiers = {
        name: uuid.uuid4() for name in ("user", "candidate", "first_envelope", "second_envelope")
    }
    connection.execute(
        text(
            "INSERT INTO users (id, email, display_name, is_active) "
            "VALUES (:user, 'admin-migration-candidate@example.test', 'Migration Candidate', true)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidates (id, user_id, status) "
            "VALUES (:candidate, :user, 'onboarding_in_progress')"
        ),
        identifiers,
    )
    return identifiers


def test_upgrade_refuses_duplicate_legacy_provider_ids_before_schema_change(
    temporary_postgres_url: str,
) -> None:
    _upgrade(temporary_postgres_url, "20260718_0007")
    engine = create_engine(temporary_postgres_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            identifiers = _seed_candidate(connection)
            connection.execute(
                text(
                    "INSERT INTO candidate_esign_envelopes "
                    "(id, candidate_id, status, envelope_id) VALUES "
                    "(:first_envelope, :candidate, 'sent', 'duplicate-provider-id'), "
                    "(:second_envelope, :candidate, 'voided', 'duplicate-provider-id')"
                ),
                identifiers,
            )

        with (
            _alembic_config(temporary_postgres_url) as config,
            pytest.raises(RuntimeError, match="duplicate legacy e-sign envelope identifiers"),
        ):
            command.upgrade(config, "20260719_0008")

        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "20260718_0007"
            )
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.columns "
                        "WHERE table_name = 'candidate_esign_envelopes' AND column_name = 'provider'"
                    )
                )
                == 0
            )
    finally:
        engine.dispose()


def test_upgrade_locks_slug_from_publication_audit_history(
    temporary_postgres_url: str,
) -> None:
    _upgrade(temporary_postgres_url, "20260718_0007")
    engine = create_engine(temporary_postgres_url, pool_pre_ping=True)
    profile_id = uuid.uuid4()
    user_id = uuid.uuid4()
    audit_id = uuid.uuid4()
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO users (id, email, display_name, is_active) "
                    "VALUES (:user_id, 'admin-migration-agent@example.test', 'Migration Agent', true)"
                ),
                {"user_id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO agent_profiles "
                    "(id, user_id, slug, licensed_name, approved_title, licence_number, biography, "
                    " status, languages, service_areas, specialties, social_links, version, "
                    " approved_at, published_at) VALUES "
                    "(:profile_id, :user_id, 'historically-published', 'Migration Agent', "
                    " 'Mortgage Agent', 'MIGRATION-1', 'Synthetic profile', 'pending_approval', "
                    " '[]', '[]', '[]', '[]', 2, NULL, NULL)"
                ),
                {"profile_id": profile_id, "user_id": user_id},
            )
            connection.execute(
                text(
                    "INSERT INTO audit_events "
                    "(id, event_type, actor_user_id, target_type, target_id, safe_metadata) "
                    "VALUES (:audit_id, 'agent_profile.published', :user_id, "
                    " 'agent_profile', :profile_id, '{}')"
                ),
                {"audit_id": audit_id, "profile_id": profile_id, "user_id": user_id},
            )

        _upgrade(temporary_postgres_url, "20260719_0008")

        with engine.connect() as connection:
            assert (
                connection.scalar(
                    text("SELECT slug_locked_at FROM agent_profiles WHERE id = :profile_id"),
                    {"profile_id": profile_id},
                )
                is not None
            )
    finally:
        engine.dispose()


def test_downgrade_refuses_unrepresentable_rejected_envelope_before_schema_change(
    temporary_postgres_url: str,
) -> None:
    _upgrade(temporary_postgres_url, "20260719_0008")
    engine = create_engine(temporary_postgres_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            identifiers = _seed_candidate(connection)
            connection.execute(
                text(
                    "INSERT INTO candidate_esign_envelopes "
                    "(id, candidate_id, status, envelope_id, provider) "
                    "VALUES (:first_envelope, :candidate, 'rejected', "
                    " 'rejected-provider-id', 'documenso')"
                ),
                identifiers,
            )

        with (
            _alembic_config(temporary_postgres_url) as config,
            pytest.raises(RuntimeError, match="rejected e-sign envelope evidence"),
        ):
            command.downgrade(config, "20260718_0007")

        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "20260719_0008"
            )
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.columns "
                        "WHERE table_name = 'agent_profiles' AND column_name = 'slug_locked_at'"
                    )
                )
                == 1
            )
    finally:
        engine.dispose()
