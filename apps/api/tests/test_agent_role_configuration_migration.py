from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory

API_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = API_ROOT / "alembic/versions/20260722_0010_agent_role_configuration.py"


class OperationRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str):  # type: ignore[no-untyped-def]
        def record(*args: Any, **kwargs: Any) -> None:
            self.calls.append((name, args, kwargs))

        return record


def _migration_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "agent_role_configuration_migration", MIGRATION_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_agent_role_configuration_is_one_forward_data_revision() -> None:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["20260726_0013"]

    migration = _migration_module()
    assert migration.revision == "20260722_0010"  # type: ignore[attr-defined]
    assert migration.down_revision == "20260722_0009"  # type: ignore[attr-defined]

    upgrade = OperationRecorder()
    migration.op = upgrade  # type: ignore[attr-defined]
    migration.upgrade()  # type: ignore[attr-defined]
    assert [name for name, _, _ in upgrade.calls] == ["execute"]
    statement = str(upgrade.calls[0][1][0])
    assert "INSERT INTO roles" in statement
    assert "'agent'" in statement
    assert "ON CONFLICT (code) DO NOTHING" in statement
    assert "user_roles" not in statement

    downgrade = OperationRecorder()
    migration.op = downgrade  # type: ignore[attr-defined]
    migration.downgrade()  # type: ignore[attr-defined]
    assert downgrade.calls == []
