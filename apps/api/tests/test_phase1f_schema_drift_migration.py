from __future__ import annotations

import hashlib
import importlib.util
import os
import uuid
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.exc import IntegrityError

from keeper_api.core.config import get_settings
from keeper_api.models.domain import Base

API_ROOT = Path(__file__).resolve().parents[1]
VERSIONS_ROOT = API_ROOT / "alembic/versions"
MIGRATION_PATH = VERSIONS_ROOT / "20260718_0007_phase_1f_schema_drift.py"
RUN_POSTGRES = os.getenv("KEEPER_RUN_SCHEMA_MIGRATION_E2E") == "1"

ISSUED_MIGRATION_HASHES = {
    "20260714_0001_phase_0_foundation.py": (
        "4b49b954fe7118f7694044b7545ac5eab432e8d5463952f72bd229fab7a9819c"
    ),
    "20260714_0002_lead_queue_indexes.py": (
        "e9fea3da86bfb0bc00a57634cc2ff4148484e0ae60dc0032c19e9fd048f1a193"
    ),
    "20260715_0003_phase_1c_recruitment.py": (
        "26fbeaa4774ac92a7868f89c50ffa78f4e047aaffcca41fc7a29cabc49174a9d"
    ),
    "20260716_0004_phase_1d_review_onboarding.py": (
        "adf86e3e8aaea7d619859897799c07c4bab88a49ef44989538a13f219f624341"
    ),
    "20260717_0005_phase_1e_agent_profiles.py": (
        "64307f18abee51ef2bccf2e5cef16160dd91f02b9898c519637be3fa38e53492"
    ),
    "20260717_0006_candidate_auth_onboarding_completion.py": (
        "29745ffe2bb9a025ae5c32a4a50af1074fd80d327b73abdcfecce5751ea66c04"
    ),
}

EXPECTED_COUNTS = {
    "candidate_esign_envelopes": 1,
    "candidate_information_requests": 1,
    "candidate_onboarding_assignments": 1,
    "candidate_onboarding_document_versions": 1,
    "candidate_onboarding_tasks": 2,
    "policy_acknowledgements": 1,
    "programmatic_gates": 1,
}


def _migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phase1f_schema_drift_migration", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _index_columns(table_name: str) -> dict[str, tuple[str, ...]]:
    return {
        index.name: tuple(column.name for column in index.columns)
        for index in Base.metadata.tables[table_name].indexes
        if index.name is not None
    }


def _foreign_key(table_name: str, column_name: str):  # type: ignore[no-untyped-def]
    foreign_keys = Base.metadata.tables[table_name].columns[column_name].foreign_keys
    assert len(foreign_keys) == 1
    return next(iter(foreign_keys))


def test_phase1f_schema_drift_is_one_forward_revision_and_preserves_issued_history() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["20260722_0010"]

    migration = _migration_module()
    assert migration.revision == "20260718_0007"  # type: ignore[attr-defined]
    assert migration.down_revision == "20260717_0006"  # type: ignore[attr-defined]

    for filename, expected_hash in ISSUED_MIGRATION_HASHES.items():
        assert hashlib.sha256((VERSIONS_ROOT / filename).read_bytes()).hexdigest() == expected_hash


def test_authoritative_index_and_foreign_key_metadata() -> None:
    esign_indexes = _index_columns("candidate_esign_envelopes")
    assert esign_indexes["ix_candidate_esign_envelopes_candidate"] == (
        "candidate_id",
        "created_at",
        "id",
    )
    assert "ix_candidate_esign_envelopes_candidate_id" not in esign_indexes

    request_indexes = _index_columns("candidate_information_requests")
    assert request_indexes["ix_candidate_information_requests_candidate_open"] == (
        "candidate_id",
        "created_at",
        "id",
    )
    assert "ix_candidate_information_requests_candidate_id" not in request_indexes

    assignment_indexes = _index_columns("candidate_onboarding_assignments")
    assert "ix_candidate_onboarding_assignments_candidate_plan" not in assignment_indexes
    assignment_uniques = {
        tuple(column.name for column in constraint.columns)
        for constraint in Base.metadata.tables["candidate_onboarding_assignments"].constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    assert ("candidate_id", "onboarding_plan_id", "generation") in assignment_uniques

    gate_indexes = _index_columns("programmatic_gates")
    assert gate_indexes["ix_programmatic_gates_candidate"] == (
        "candidate_id",
        "created_at",
        "id",
    )
    assert "ix_programmatic_gates_candidate_id" not in gate_indexes

    task_template_fk = _foreign_key("candidate_onboarding_tasks", "onboarding_task_id")
    assert task_template_fk.name == "candidate_onboarding_tasks_onboarding_task_id_fkey"
    assert task_template_fk.ondelete == "RESTRICT"

    reviewer_fk = _foreign_key("candidate_onboarding_tasks", "reviewed_by_user_id")
    assert reviewer_fk.name == "candidate_onboarding_tasks_reviewed_by_user_id_fkey"
    assert reviewer_fk.ondelete == "RESTRICT"
    assert Base.metadata.tables["candidate_onboarding_tasks"].c.reviewed_by_user_id.nullable

    version_fk = _foreign_key("policy_acknowledgements", "document_version_id")
    assert version_fk.name == "policy_acknowledgements_document_version_id_fkey"
    assert version_fk.ondelete == "RESTRICT"


@pytest.fixture
def temporary_postgres_url() -> Generator[str, None, None]:
    if not RUN_POSTGRES:
        pytest.skip("set KEEPER_RUN_SCHEMA_MIGRATION_E2E=1 to run PostgreSQL migration tests")

    base_url = make_url(get_settings().database_url)
    if not base_url.drivername.startswith("postgresql"):
        pytest.skip("PostgreSQL migration tests require a PostgreSQL DATABASE_URL")

    database_name = f"keeper_schema_test_{uuid.uuid4().hex}"
    assert database_name.startswith("keeper_schema_test_") and len(database_name) < 64
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


def _seed_representative_evidence(connection: Connection) -> dict[str, uuid.UUID]:
    identifiers = {
        name: uuid.uuid5(uuid.NAMESPACE_URL, f"keeper-schema-test:{name}")
        for name in (
            "candidate_user",
            "reviewer_user",
            "candidate",
            "plan",
            "task_reviewed",
            "task_unreviewed",
            "assignment",
            "candidate_task_reviewed",
            "candidate_task_unreviewed",
            "controlled_document",
            "document_version",
            "assigned_version",
            "acknowledgement",
            "information_request",
            "esign_envelope",
            "gate",
        )
    }
    connection.execute(
        text(
            "INSERT INTO users (id, email, display_name, is_active) VALUES "
            "(:candidate_user, 'schema-candidate@example.test', 'Schema Candidate', true), "
            "(:reviewer_user, 'schema-reviewer@example.test', 'Schema Reviewer', true)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidates (id, user_id, status) "
            "VALUES (:candidate, :candidate_user, 'onboarding_in_progress')"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO onboarding_plans (id, name, description, is_active) "
            "VALUES (:plan, 'Schema test plan', 'Synthetic migration evidence', true)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO onboarding_tasks "
            "(id, plan_id, title, instructions, sequence, is_required) VALUES "
            "(:task_reviewed, :plan, 'Reviewed task', 'Synthetic', 1, true), "
            "(:task_unreviewed, :plan, 'Unreviewed task', 'Synthetic', 2, true)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidate_onboarding_assignments "
            "(id, candidate_id, onboarding_plan_id, generation, status, assigned_by_user_id) "
            "VALUES (:assignment, :candidate, :plan, 1, 'completed', :reviewer_user)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidate_onboarding_tasks "
            "(id, candidate_id, assignment_id, onboarding_task_id, status, "
            " reviewed_by_user_id, reviewed_at) VALUES "
            "(:candidate_task_reviewed, :candidate, :assignment, :task_reviewed, "
            " 'completed', :reviewer_user, now()), "
            "(:candidate_task_unreviewed, :candidate, :assignment, :task_unreviewed, "
            " 'required', NULL, NULL)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO controlled_documents "
            "(id, key, title, description, requires_acknowledgement) "
            "VALUES (:controlled_document, 'schema-test-policy', 'Schema test policy', "
            " 'Synthetic', true)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO document_versions "
            "(id, controlled_document_id, version_label, object_key, sha256_digest, "
            " content_type, size_bytes, issued_at) VALUES "
            "(:document_version, :controlled_document, '1.0', "
            " 'schema-test/document-version', "
            " '0000000000000000000000000000000000000000000000000000000000000000', "
            " 'application/pdf', 1, now())"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidate_onboarding_document_versions "
            "(id, assignment_id, document_version_id, assigned_by_user_id) "
            "VALUES (:assigned_version, :assignment, :document_version, :reviewer_user)"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO policy_acknowledgements "
            "(id, candidate_id, assignment_id, user_id, document_version_id, wording) "
            "VALUES (:acknowledgement, :candidate, :assignment, :candidate_user, "
            " :document_version, 'Synthetic acknowledgement wording')"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidate_information_requests "
            "(id, candidate_id, requested_by_user_id, status, message) "
            "VALUES (:information_request, :candidate, :reviewer_user, 'open', "
            " 'Synthetic information request')"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO candidate_esign_envelopes "
            "(id, candidate_id, created_by_user_id, document_version_id, status, envelope_id) "
            "VALUES (:esign_envelope, :candidate, :reviewer_user, :document_version, "
            " 'sent', 'schema-test-envelope')"
        ),
        identifiers,
    )
    connection.execute(
        text(
            "INSERT INTO programmatic_gates "
            "(id, candidate_id, code, label, status) "
            "VALUES (:gate, :candidate, 'schema_test', 'Schema test gate', 'open')"
        ),
        identifiers,
    )
    return identifiers


def _assert_representative_evidence(connection: Connection) -> None:
    for table_name, expected_count in EXPECTED_COUNTS.items():
        assert connection.scalar(text(f"SELECT count(*) FROM {table_name}")) == expected_count
    assert (
        connection.scalar(
            text(
                "SELECT count(*) FROM candidate_onboarding_tasks WHERE reviewed_by_user_id IS NULL"
            )
        )
        == 1
    )


def _catalog_indexes(connection: Connection, table_name: str) -> dict[str, str]:
    return dict(
        connection.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE schemaname = current_schema() AND tablename = :table_name"
            ),
            {"table_name": table_name},
        ).all()
    )


def _catalog_delete_action(connection: Connection, table_name: str, constraint_name: str) -> str:
    action = connection.scalar(
        text(
            "SELECT confdeltype FROM pg_constraint "
            "WHERE conrelid = CAST(:table_name AS regclass) AND conname = :constraint_name"
        ),
        {"table_name": table_name, "constraint_name": constraint_name},
    )
    assert isinstance(action, str)
    return action


def _assert_head_catalog(connection: Connection) -> None:
    esign_indexes = _catalog_indexes(connection, "candidate_esign_envelopes")
    assert (
        "btree (candidate_id, created_at, id)"
        in esign_indexes["ix_candidate_esign_envelopes_candidate"]
    )
    assert "ix_candidate_esign_envelopes_candidate_id" not in esign_indexes

    request_indexes = _catalog_indexes(connection, "candidate_information_requests")
    assert (
        "btree (candidate_id, created_at, id)"
        in request_indexes["ix_candidate_information_requests_candidate_open"]
    )
    assert "ix_candidate_information_requests_candidate_id" not in request_indexes

    assignment_indexes = _catalog_indexes(connection, "candidate_onboarding_assignments")
    assert "ix_candidate_onboarding_assignments_candidate_plan" not in assignment_indexes
    unique_definition = connection.scalar(
        text(
            "SELECT pg_get_constraintdef(oid, true) FROM pg_constraint "
            "WHERE conrelid = 'candidate_onboarding_assignments'::regclass "
            "AND contype = 'u' "
            "AND pg_get_constraintdef(oid, true) = "
            "'UNIQUE (candidate_id, onboarding_plan_id, generation)'"
        )
    )
    assert unique_definition == "UNIQUE (candidate_id, onboarding_plan_id, generation)"

    gate_indexes = _catalog_indexes(connection, "programmatic_gates")
    assert "btree (candidate_id, created_at, id)" in gate_indexes["ix_programmatic_gates_candidate"]
    assert "ix_programmatic_gates_candidate_id" not in gate_indexes

    assert (
        _catalog_delete_action(
            connection,
            "candidate_onboarding_tasks",
            "candidate_onboarding_tasks_onboarding_task_id_fkey",
        )
        == "r"
    )
    assert (
        _catalog_delete_action(
            connection,
            "candidate_onboarding_tasks",
            "candidate_onboarding_tasks_reviewed_by_user_id_fkey",
        )
        == "r"
    )
    assert (
        _catalog_delete_action(
            connection,
            "policy_acknowledgements",
            "policy_acknowledgements_document_version_id_fkey",
        )
        == "r"
    )
    assert (
        connection.scalar(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_schema = current_schema() "
                "AND table_name = 'candidate_onboarding_tasks' "
                "AND column_name = 'reviewed_by_user_id'"
            )
        )
        == "YES"
    )


def _assert_delete_restricted(database_url: str, statement: str, identifier: uuid.UUID) -> None:
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(text(statement), {"identifier": identifier})
    finally:
        engine.dispose()


def test_postgres_upgrade_downgrade_reupgrade_preserves_evidence(
    temporary_postgres_url: str,
) -> None:
    with _alembic_config(temporary_postgres_url) as config:
        command.upgrade(config, "20260717_0006")

    engine = create_engine(temporary_postgres_url, pool_pre_ping=True)
    try:
        with engine.begin() as connection:
            identifiers = _seed_representative_evidence(connection)

        with _alembic_config(temporary_postgres_url) as config:
            command.upgrade(config, "20260718_0007")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "20260718_0007"
            )
            _assert_representative_evidence(connection)
            _assert_head_catalog(connection)

        _assert_delete_restricted(
            temporary_postgres_url,
            "DELETE FROM onboarding_tasks WHERE id = :identifier",
            identifiers["task_reviewed"],
        )
        _assert_delete_restricted(
            temporary_postgres_url,
            "DELETE FROM users WHERE id = :identifier",
            identifiers["reviewer_user"],
        )
        _assert_delete_restricted(
            temporary_postgres_url,
            "DELETE FROM document_versions WHERE id = :identifier",
            identifiers["document_version"],
        )

        with _alembic_config(temporary_postgres_url) as config:
            command.downgrade(config, "20260717_0006")
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "20260717_0006"
            )
            _assert_representative_evidence(connection)
            assert "ix_candidate_onboarding_assignments_candidate_plan" in _catalog_indexes(
                connection, "candidate_onboarding_assignments"
            )
            assert (
                _catalog_delete_action(
                    connection,
                    "candidate_onboarding_tasks",
                    "candidate_onboarding_tasks_onboarding_task_id_fkey",
                )
                == "a"
            )
            assert (
                _catalog_delete_action(
                    connection,
                    "candidate_onboarding_tasks",
                    "candidate_onboarding_tasks_reviewed_by_user_id_fkey",
                )
                == "a"
            )
            assert (
                _catalog_delete_action(
                    connection,
                    "policy_acknowledgements",
                    "policy_acknowledgements_document_version_id_fkey",
                )
                == "a"
            )

        with _alembic_config(temporary_postgres_url) as config:
            command.upgrade(config, "head")
            command.check(config)
        with engine.connect() as connection:
            _assert_representative_evidence(connection)
            _assert_head_catalog(connection)
    finally:
        engine.dispose()


def test_postgres_fresh_upgrade_reaches_clean_head(temporary_postgres_url: str) -> None:
    with _alembic_config(temporary_postgres_url) as config:
        command.upgrade(config, "head")
        command.current(config, check_heads=True)
        command.check(config)
    engine = create_engine(temporary_postgres_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "20260719_0008"
            )
            _assert_head_catalog(connection)
    finally:
        engine.dispose()
