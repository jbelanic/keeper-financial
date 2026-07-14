from __future__ import annotations

import json
from pathlib import Path

from keeper_api.main import app

destination = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "openapi.json"
destination.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"wrote {destination}")
