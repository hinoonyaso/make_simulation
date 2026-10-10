"""Keep solver execution optional and make every beat's evidence level explicit."""
from __future__ import annotations

from typing import Any

EVIDENCE = {"conceptual_illustration", "derived_calculation", "computed_result", "measured_data"}


def classify_beat(beat: dict[str, Any]) -> str:
    declared = beat.get("evidence_type") or beat.get("evidence") or "conceptual_illustration"
    aliases = {"toy_simulation": "conceptual_illustration", "model_execution": "computed_result"}
    declared = aliases.get(declared, declared)
    if declared not in EVIDENCE:
        raise ValueError(f"unsupported evidence type: {declared}")
    return declared


def route_evidence(spec: dict[str, Any], beats: list[dict[str, Any]]) -> dict[str, Any]:
    solver = spec.get("solver")
    policy = spec.get("computation_policy", "only_when_needed")
    modes = spec.get("modes", ["concept_visualization"])
    needs_solver = any(mode == "computed_engineering_demonstration" for mode in modes)
    if needs_solver and not solver:
        raise ValueError("computed engineering mode requires a named solver")
    if solver and not spec.get("trace"):
        return {"status": "PLANNED", "solver": solver, "reason": "solver adapter/trace is not configured"}
    if policy == "never" and needs_solver:
        raise ValueError("computation_policy=never conflicts with computed engineering mode")
    levels = [classify_beat(beat) for beat in beats]
    if needs_solver:
        return {"status": "BLOCKED", "solver": solver,
                "execution_required": False,
                "reason": "no registered engineering solver adapter can validate this execution"}
    return {"status": "CONCEPT_ONLY",
            "solver": solver, "beat_evidence": levels,
            "execution_required": False,
            "reason": "concept-only lesson; no solver execution requested"}
