"""Build V9-compatible manifest and V12 timeline without a solver dependency."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.education.evidence_router import route_evidence
from core.education.lesson_validator import validate_manifest
from core.education.renderer_registry import resolve_lesson_contract
from core.education.solver_registry import load_solver_config
from core.mechanism.timeline import build_timeline


def plan_lesson(spec: dict[str, Any], *, fps: int = 30) -> dict[str, Any]:
    source_beats = spec.get("beats")
    if not isinstance(source_beats, list):
        raise ValueError("lesson spec must contain beats; V9 manifest remains the single beat source")
    beats = deepcopy(source_beats)
    target = spec.get("duration_target_sec")
    actual = sum(float(beat.get("sec", 0)) for beat in beats if isinstance(beat, dict))
    if target and abs(actual - target) / target > .20:
        raise ValueError(f"beat duration {actual:.2f}s differs from duration_target_sec={target}s by more than 20%")
    visual_profile = spec.get("visual_profile", "technical_dark")
    manifest = {"language": spec.get("language", "ko-KR"), "voice": spec.get("voice", "ko-KR-SunHiNeural"),
                "rate": spec.get("rate", "+0%"), "format": "technical_preview",
                "title": spec.get("title", spec["question"]), "visual_profile": visual_profile, "beats": beats}
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("invalid V9 visual manifest: " + "; ".join(errors))
    renderer_contract = resolve_lesson_contract(spec)
    solver_config = load_solver_config(spec)
    evidence = route_evidence(spec, beats)
    if evidence["status"] == "BLOCKED":
        raise ValueError(f"engineering solver route is blocked: {evidence.get('reason')}")
    for beat, evidence_type in zip(beats, evidence.get("beat_evidence", [])):
        beat["evidence_type"] = evidence_type
        beat["evidence"] = {"conceptual_illustration": "illustration",
                             "derived_calculation": "reported_result",
                             "computed_result": "model_execution",
                             "measured_data": "trace_playback"}[evidence_type]
        beat.setdefault("trace", "")
        beat.setdefault("min_sec", beat["sec"])
    timeline = build_timeline([{"phase_id": beat["phase_id"], "sec": beat["sec"]} for beat in beats], fps=fps)
    return {"visual_manifest": manifest, "timeline": timeline,
            "visual_plan": {"kind": "education", "topic": spec["topic"], "title": manifest["title"],
                            "visual_profile": visual_profile,
                            "blueprints": [beat.get("blueprint") for beat in beats],
                            "beat_evidence": evidence.get("beat_evidence", []),
                            "renderer_registry_id": renderer_contract["registry_id"],
                            "asset_id": renderer_contract["asset_id"],
                            "solver": spec.get("solver"),
                            "solver_config": (solver_config[0] if solver_config else None)},
            "renderer_contract": renderer_contract,
            "evidence": evidence}
