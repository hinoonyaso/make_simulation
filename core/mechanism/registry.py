"""Import-light capability lookup and lazy adapter loading."""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = Path(__file__).with_name("catalog.json")


class MechanismRegistry:
    def __init__(self, catalog_path: str | Path = CATALOG_PATH):
        self.path = Path(catalog_path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))
        if self.data.get("schema") != "mechanism-capability-catalog/v1":
            raise ValueError("unsupported capability catalog schema")
        self._rows = self._materialize()

    def _materialize(self) -> list[dict[str, Any]]:
        rows = []
        defaults = {"support_level": "unsupported", "implementation_status": "planned",
                    "adapter": None, "execution_backend": None,
                    "trace_schema": "none", "renderers": [], "asset_requirements": [],
                    "software_requirements": [], "hardware_requirements": [],
                    "benchmark_requirements": [], "supported_features": [],
                    "known_limitations": ["No executable adapter is registered."]}
        overrides = self.data.get("overrides", {})
        for domain, topics in self.data.get("domains", {}).items():
            for raw in topics:
                topic = raw["topic"] if isinstance(raw, dict) else raw
                row = {**defaults, "domain": domain, "topic": topic,
                       "aliases": list(raw.get("aliases", [])) if isinstance(raw, dict) else []}
                row.update(overrides.get(topic, {}))
                row["domain"] = overrides.get(topic, {}).get("domain", domain)
                row["topic"] = topic
                row["aliases"] = list(dict.fromkeys(
                    row["aliases"] + self.data.get("aliases", {}).get(topic, [])))
                rows.append(row)
        return rows

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")

    def list_capabilities(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows]

    def resolve(self, topic_or_alias: str) -> dict[str, Any] | None:
        key = self._normalize(topic_or_alias)
        for row in self._rows:
            if key == self._normalize(row["topic"]):
                return dict(row)
            if any(key == self._normalize(alias) for alias in row["aliases"]):
                return dict(row)
        return None

    def require_executable(self, topic_or_alias: str) -> dict[str, Any]:
        row = self.resolve(topic_or_alias)
        if row is None:
            raise KeyError(f"unknown mechanism topic: {topic_or_alias}")
        if row["implementation_status"] != "ready" or not row.get("adapter"):
            raise NotImplementedError(
                f"{row['topic']} is not executable (level={row['support_level']}, "
                f"status={row['implementation_status']})")
        return row

    def load_adapter(self, topic_or_alias: str):
        row = self.require_executable(topic_or_alias)
        module_name, class_name = row["adapter"].split(":", 1)
        if str(ROOT) not in __import__("sys").path:
            __import__("sys").path.insert(0, str(ROOT))
        module = importlib.import_module(module_name)
        adapter_type = getattr(module, class_name)
        return adapter_type(row)
