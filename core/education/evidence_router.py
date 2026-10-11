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


def route_evidence(spec: dict[str, Any], beats: list[dict[str, Any]],
                   solver_result: dict[str, Any] | None = None) -> dict[str, Any]:
    solver = spec.get("solver")
    policy = spec.get("computation_policy", "only_when_needed")
    modes = spec.get("modes", ["concept_visualization"])
    needs_solver = any(mode == "computed_engineering_demonstration" for mode in modes)
    if needs_solver and not solver:
        raise ValueError("computed engineering mode requires a named solver")
    if policy == "never" and needs_solver:
        raise ValueError("computation_policy=never conflicts with computed engineering mode")
    levels = [classify_beat(beat) for beat in beats]
    computed = needs_solver or "computed_result" in levels
    if computed:
        if not solver:
            raise ValueError("computed engineering evidence requires a named solver")
        from core.education.solver_registry import SOLVER_IDS
        if solver not in SOLVER_IDS:
            return {"status": "BLOCKED", "solver": solver, "execution_required": False,
                    "beat_evidence": levels,
                    "reason": "no registered engineering solver adapter can validate this execution"}
        if not spec.get("solver_config"):
            return {"status": "BLOCKED", "solver": solver, "execution_required": False,
                    "beat_evidence": levels, "reason": "registered solver requires a validated solver_config"}
        if solver_result is None:
            return {"status": "PLANNED", "solver": solver, "execution_required": True,
                    "beat_evidence": levels, "reason": "registered solver input is valid; execution is a separate stage"}
        provenance = solver_result.get("solver_execution", {})
        if (solver_result.get("status") != "PASS" or provenance.get("executed") is not True
                or provenance.get("solver_id") != solver or not solver_result.get("result_sha256")
                or not solver_result.get("config_sha256")):
            return {"status": "BLOCKED", "solver": solver, "execution_required": False,
                    "beat_evidence": levels, "reason": "solver result lacks validated execution provenance"}
        return {"status": "RESULT_VALIDATED", "solver": solver, "execution_required": False,
                "beat_evidence": levels, "result_sha256": solver_result["result_sha256"],
                "run_id": provenance["run_id"],
                "reason": "saved solver output and execution provenance were validated before rendering"}
    return {"status": "CONCEPT_ONLY",
            "solver": solver, "beat_evidence": levels,
            "execution_required": False,
            "reason": "concept-only lesson; no solver execution requested"}
