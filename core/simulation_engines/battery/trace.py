"""Shared V9 trace validation bridge for a persisted PyBaMM run."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.simulation_engines.battery.result_validator import load_validated_result

TRACE_SCHEMA = "battery-simulation-trace/v1"


def validate_trace(path: str | Path) -> list[str]:
    trace_path = Path(path).resolve()
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot load battery trace: {exc}"]
    if not isinstance(trace, dict) or trace.get("schema") != TRACE_SCHEMA:
        return [f"schema must be {TRACE_SCHEMA}"]
    if trace.get("solver_id") != "pybamm":
        return ["solver_id must be pybamm"]
    expected_names = {"result_file": "result.json", "config_file": "simulation_config.json",
                      "timeseries_file": "battery_timeseries.csv"}
    if any(trace.get(key) != value for key, value in expected_names.items()):
        return ["trace files must use the colocated result.json, simulation_config.json and battery_timeseries.csv"]
    try:
        loaded = load_validated_result(trace_path.parent)
    except (OSError, ValueError, KeyError) as exc:
        return [f"PyBaMM run validation failed: {exc}"]
    result = loaded["result"]
    if (trace.get("run_id") != result.get("solver_execution", {}).get("run_id")
            or trace.get("result_sha256") != result.get("result_sha256")
            or trace.get("config_sha256") != result.get("config_sha256")
            or trace.get("sample_count") != result.get("sample_count")
            or trace.get("actual_end_time_s") != result.get("actual_end_time_s")):
        return ["battery trace provenance does not match the validated result.json"]
    return []
