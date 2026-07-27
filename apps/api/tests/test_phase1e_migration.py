from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory

API_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = API_ROOT / "alembic/versions/20260717_0005_phase_1e_agent_profiles.py"
NEW_COLUMNS = {
    "languages",
    "service_areas",
    "specialties",
    "photo_url",
    "photo_alt_text",
    "public_email",
    "public_phone",
    "social_links",
    "version",
}


class OperationRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
        def record(*args: Any, **kwargs: Any) -> None:
            self.calls.append((name, args, kwargs))

        return record


def _migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "phase1e_agent_profiles_migration", MIGRATION_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase1e_migration_alters_foundational_agent_profiles_without_destroying_it() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["20260726_0015"]

    migration = _migration_module()
    assert migration.revision == "20260717_0005"  # type: ignore[attr-defined]
    assert migration.down_revision == "20260716_0004"  # type: ignore[attr-defined]
    upgrade = OperationRecorder()
    migration.op = upgrade  # type: ignore[attr-defined]
    migration.upgrade()  # type: ignore[attr-defined]

    upgrade_names = [name for name, _, _ in upgrade.calls]
    assert "create_table" not in upgrade_names
    assert {
        args[1].name
        for name, args, _ in upgrade.calls
        if name == "add_column" and args[0] == "agent_profiles"
    } == NEW_COLUMNS
    assert [args[0] for name, args, _ in upgrade.calls if name == "create_index"] == [
        "ix_agent_profiles_publication"
    ]

    downgrade = OperationRecorder()
    migration.op = downgrade  # type: ignore[attr-defined]
    migration.downgrade()  # type: ignore[attr-defined]

    downgrade_names = [name for name, _, _ in downgrade.calls]
    assert "drop_table" not in downgrade_names
    assert {
        args[1]
        for name, args, _ in downgrade.calls
        if name == "drop_column" and args[0] == "agent_profiles"
    } == NEW_COLUMNS
    assert [args[0] for name, args, _ in downgrade.calls if name == "drop_index"] == [
        "ix_agent_profiles_publication"
    ]
