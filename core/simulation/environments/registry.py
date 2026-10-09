"""Read-only catalog for environment candidates and evidence status."""
from __future__ import annotations
import json
from pathlib import Path

CATALOG = Path(__file__).with_name("registry.json")

class EnvironmentRegistry:
    def __init__(self, path: str | Path = CATALOG):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        if self.data.get("schema") != "simulation-environment-catalog/v1" or not isinstance(self.data.get("environments"), list):
            raise ValueError("unsupported simulation environment catalog")
        ids = [item.get("id") for item in self.data["environments"]]
        if len(ids) != len(set(ids)) or any(not isinstance(x, str) for x in ids):
            raise ValueError("environment IDs must be unique strings")
    def list(self, category: str | None = None):
        rows = self.data["environments"]
        if category:
            rows = [item for item in rows if category.casefold() in item.get("category", "").casefold()]
        return [dict(row) for row in rows]
    def get(self, env_id: str):
        found = [item for item in self.data["environments"] if item["id"] == env_id]
        if len(found) != 1: raise KeyError(f"unknown environment: {env_id}")
        return dict(found[0])
