"""Common trace envelope checks; domain payload validation remains delegated."""
from __future__ import annotations

import math
import hashlib
import json
import platform
from typing import Any

SCHEMA = "mechanism-envelope/v1"
EXECUTION_TYPES = {"model_execution", "reported_result", "numerical_simulation", "toy_simulation", "trace_replay", "illustration"}


def make_envelope(*, domain: str, topic: str, execution_type: str,
                  inputs: list[dict[str, Any]], operations: list[dict[str, Any]],
                  outputs: list[dict[str, Any]], payload: dict[str, Any],
                  provenance: dict[str, Any] | None = None,
                  limitations: list[str] | None = None,
                  hardware: dict[str, Any] | None = None,
                  timestamps: list[float] | None = None) -> dict[str, Any]:
    base = {"domain": domain, "topic": topic, "execution_type": execution_type,
            "inputs": inputs, "operations": operations, "outputs": outputs,
            "payload": payload}
    trace_id = f"{topic}:{hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]}"
    return {"schema": SCHEMA, "trace_id": trace_id, **base,
            "timestamps": timestamps or [], "provenance": provenance or {"source": "local adapter"},
            "software_version": {"python": platform.python_version()},
            "hardware": hardware,
            "evidence_level": execution_type,
            "limitations": limitations or []}


def validate_envelope(trace: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return ["trace must be an object"]
    if trace.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    for name in ("trace_id", "domain", "topic", "execution_type", "evidence_level"):
        if not isinstance(trace.get(name), str) or not trace[name].strip():
            errors.append(f"{name} must be a non-empty string")
    if trace.get("execution_type") not in EXECUTION_TYPES:
        errors.append("execution_type is unsupported")
    for name in ("inputs", "operations", "outputs"):
        if not isinstance(trace.get(name), list):
            errors.append(f"{name} must be a list")
    for name in ("timestamps", "provenance", "software_version", "limitations", "payload"):
        if name not in trace:
            errors.append(f"missing {name}")
    if not isinstance(trace.get("provenance"), dict):
        errors.append("provenance must be an object")
    if not isinstance(trace.get("limitations"), list):
        errors.append("limitations must be a list")
    timestamps = trace.get("timestamps")
    if isinstance(timestamps, list):
        previous = -math.inf
        for index, value in enumerate(timestamps):
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value < previous:
                errors.append(f"timestamps[{index}] must be finite and monotonic")
                break
            previous = float(value)
    if "hardware" not in trace:
        errors.append("missing hardware; use null when not measured")
    return errors
