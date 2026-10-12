"""Build V9-compatible manifest and V12 timeline without a solver dependency."""
from __future__ import annotations

from typing import Any

from core.education.blueprint_registry import get_blueprint, validate_asset_blueprint
from core.education.evidence_router import route_evidence
from core.education.lesson_validator import validate_manifest
from core.mechanism.timeline import build_timeline


def plan_lesson(spec: dict[str, Any], *, fps: int = 30) -> dict[str, Any]:
    beats = spec.get("beats")
    if not isinstance(beats, list):
        raise ValueError("lesson spec must contain beats; V9 manifest remains the single beat source")
    target = spec.get("duration_target_sec")
    actual = sum(float(beat.get("sec", 0)) for beat in beats if isinstance(beat, dict))
    if target and abs(actual - target) / target > .20:
        raise ValueError(f"beat duration {actual:.2f}s differs from duration_target_sec={target}s by more than 20%")
    manifest = {"language": spec.get("language", "ko-KR"), "voice": spec.get("voice", "ko-KR-SunHiNeural"),
                "rate": spec.get("rate", "+0%"), "format": "technical_preview",
                "title": spec.get("title", spec["question"]), "beats": beats}
    if spec.get("asset_id"):
        manifest["asset_id"] = spec["asset_id"]
    if spec.get("blueprint"):
        manifest["blueprint"] = spec["blueprint"]
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("invalid V9 visual manifest: " + "; ".join(errors))
    for beat in beats:
        blueprint = beat.get("blueprint")
        if blueprint:
            capabilities = get_blueprint(blueprint)
            expected_renderer = {"B": "blender", "M": "manim"}.get(beat.get("tool"))
            if expected_renderer and expected_renderer not in capabilities["renderers"]:
                raise ValueError(f"beat {beat.get('id')}: blueprint {blueprint} does not support renderer {expected_renderer}")
            if spec.get("asset_id"):
                validate_asset_blueprint(spec["asset_id"], blueprint,
                                         beat.get("animation", spec.get("animation")))
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
                            "blueprints": [beat.get("blueprint") for beat in beats],
                            "beat_evidence": evidence.get("beat_evidence", [])},
            "evidence": evidence}
