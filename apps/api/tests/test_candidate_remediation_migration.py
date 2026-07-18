from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from alembic.config import Config
from alembic.script import ScriptDirectory

API_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = API_ROOT / "alembic/versions/20260717_0006_candidate_auth_onboarding_completion.py"


def migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "candidate_auth_onboarding_completion_migration", MIGRATION_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_candidate_remediation_remains_the_issued_revision_after_phase1e() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["20260718_0007"]
    migration = migration_module()
    assert migration.revision == "20260717_0006"  # type: ignore[attr-defined]
    assert migration.down_revision == "20260717_0005"  # type: ignore[attr-defined]


def test_candidate_remediation_does_not_rewrite_issued_migrations_or_general_drift() -> None:
    source = MIGRATION_PATH.read_text()
    assert "candidate_onboarding_document_versions" in source
    assert "application_id" in source
    assert "assignment_id" in source
    assert "candidate_esign_envelopes.candidate_id" not in source
    assert "programmatic_gates.candidate_id" not in source
    assert "reviewed_by_user_id" not in source
