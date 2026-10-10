"""Cross-check education metadata with the existing V9 manifest contract."""
from __future__ import annotations

from typing import Any

from core.education.evidence_router import classify_beat

REQUIRED_BEAT_FIELDS = ("id", "text", "caption", "sec", "object", "state_change", "focus", "tool")


def validate_manifest(manifest: Any) -> list[str]:
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    beats = manifest.get("beats")
    if not isinstance(beats, list) or not beats:
        return ["manifest beats must be a non-empty list"]
    errors, ids = [], []
    for index, beat in enumerate(beats):
        prefix = f"beats[{index}]"
        if not isinstance(beat, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in REQUIRED_BEAT_FIELDS:
            if key not in beat:
                errors.append(f"{prefix}.{key} is required")
        if beat.get("tool") not in {"M", "B", "E"}:
            errors.append(f"{prefix}.tool must be M, B or E")
        if beat.get("evidence_type", "conceptual_illustration") not in {
                "conceptual_illustration", "derived_calculation", "computed_result", "measured_data"}:
            errors.append(f"{prefix}.evidence_type is unsupported")
        if not isinstance(beat.get("id"), str) or not beat["id"].strip():
            errors.append(f"{prefix}.id must be non-empty")
        else:
            ids.append(beat["id"])
        if not isinstance(beat.get("phase_id"), str) or not beat["phase_id"].strip():
            errors.append(f"{prefix}.phase_id must be non-empty")
        try:
            if float(beat.get("sec", 0)) <= 0:
                errors.append(f"{prefix}.sec must be positive")
        except (TypeError, ValueError):
            errors.append(f"{prefix}.sec must be numeric")
        try:
            classify_beat(beat)
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
    if len(ids) != len(set(ids)):
        errors.append("beat IDs must be unique")
    return errors
