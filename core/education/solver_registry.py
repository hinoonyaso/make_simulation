"""Allow-list optional solver IDs and validate their input contracts at plan time."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.simulation_engines.battery.schema import SOLVER_ID, validate_config

ROOT = Path(__file__).resolve().parents[2]
SOLVER_IDS = {SOLVER_ID}


def load_solver_config(spec: dict[str, Any], *, root: Path = ROOT) -> tuple[dict[str, Any], Path] | None:
    solver_id = spec.get("solver")
    if solver_id is None:
        return None
    if solver_id not in SOLVER_IDS:
        raise ValueError(f"unsupported education solver {solver_id!r}; registered solver IDs: {sorted(SOLVER_IDS)}")
    relative = spec.get("solver_config")
    if not isinstance(relative, str) or not relative:
        raise ValueError(f"solver {solver_id!r} requires a repository-relative solver_config path")
    config_path = (root / relative).resolve()
    try:
        config_path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("solver_config must remain inside the repository") from exc
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read solver_config {relative!r}: {exc}") from exc
    errors = validate_config(config)
    if errors:
        raise ValueError("invalid PyBaMM config: " + "; ".join(errors))
    if config.get("solver") != solver_id:
        raise ValueError("lesson solver ID does not match solver_config solver")
    return config, config_path
