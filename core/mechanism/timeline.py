"""Integer-frame presentation timeline shared by mechanism renderers.

Trace/source time is optional for non-temporal execution traces. In that case
the phase still points to an exact trace-derived state, but makes no claim that
the algorithm itself ran over the presentation interval.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import math
from typing import Any

SCHEMA = "mechanism-timeline/v1"
PLAYBACK_MODES = {"normal_speed", "slow_motion", "hold", "hold_and_analysis", "replay"}
VISUAL_GOALS = {"numerical_explanation", "algorithm_flow", "image_space", "motion_3d",
                "spatial_relationship", "comparative_analysis"}


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _frame_boundary(seconds: Decimal, fps: int) -> int:
    return int((seconds * fps).to_integral_value(rounding=ROUND_HALF_UP))


def build_timeline(beats: list[dict[str, Any]], *, fps: int = 30,
                   source_range: tuple[float, float] | None = None,
                   phase_source: dict[str, dict[str, Any]] | None = None,
                   default_visual_goal: str = "algorithm_flow") -> dict[str, Any]:
    """Build contiguous half-open frame intervals from V9 `sec` values."""
    if not isinstance(fps, int) or isinstance(fps, bool) or fps <= 0:
        raise ValueError("timeline fps must be a positive integer")
    if not isinstance(beats, list) or not beats:
        raise ValueError("timeline requires at least one storyboard beat")
    if default_visual_goal not in VISUAL_GOALS:
        raise ValueError(f"unsupported visual goal: {default_visual_goal}")
    if source_range is not None:
        src_start = _finite_number(source_range[0], "source range start")
        src_end = _finite_number(source_range[1], "source range end")
        if src_end < src_start:
            raise ValueError("source range end precedes source range start")
        source_range = (src_start, src_end)

    phases = []
    elapsed = Decimal("0")
    previous_frame = 0
    phase_source = phase_source or {}
    for beat in beats:
        phase_id = beat.get("phase_id")
        if not isinstance(phase_id, str) or not phase_id.strip():
            raise ValueError("every timeline beat requires a non-empty phase_id")
        try:
            duration = Decimal(str(beat.get("sec")))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(f"phase {phase_id} has an invalid duration") from exc
        if not duration.is_finite() or duration <= 0:
            raise ValueError(f"phase {phase_id} duration must be finite and positive")
        elapsed += duration
        end_frame = _frame_boundary(elapsed, fps)
        if end_frame <= previous_frame:
            raise ValueError(f"phase {phase_id} maps to an empty frame interval at {fps} fps")

        mapping = phase_source.get(phase_id, {})
        mode = mapping.get("playback_mode", "hold")
        goal = mapping.get("visual_goal", default_visual_goal)
        if mode not in PLAYBACK_MODES:
            raise ValueError(f"phase {phase_id} has unsupported playback_mode {mode!r}")
        if goal not in VISUAL_GOALS:
            raise ValueError(f"phase {phase_id} has unsupported visual_goal {goal!r}")
        source_start = mapping.get("source_start_sec")
        source_end = mapping.get("source_end_sec")
        if source_range is not None and source_start is None and source_end is None:
            if mode in {"hold", "hold_and_analysis"}:
                source_start = source_end = source_range[0] if mode == "hold" else source_range[1]
            else:
                source_start, source_end = source_range
        if (source_start is None) != (source_end is None):
            raise ValueError(f"phase {phase_id} must provide both source interval endpoints")
        if source_start is not None:
            source_start = _finite_number(source_start, f"{phase_id} source start")
            source_end = _finite_number(source_end, f"{phase_id} source end")
            if source_end < source_start and mode not in {"replay"}:
                raise ValueError(f"phase {phase_id} source time moves backward without replay mode")
            if source_range is not None and (source_start < source_range[0] - 1e-9 or
                                             source_end > source_range[1] + 1e-9):
                raise ValueError(f"phase {phase_id} source interval exceeds trace range")
        phases.append({
            "phase_id": phase_id,
            "presentation_start_frame": previous_frame,
            "presentation_end_frame": end_frame,
            "presentation_start_sec": previous_frame / fps,
            "presentation_end_sec": end_frame / fps,
            "source_start_sec": source_start,
            "source_end_sec": source_end,
            "playback_mode": mode,
            "visual_goal": goal,
        })
        previous_frame = end_frame
    timeline = {"schema": SCHEMA, "fps": fps, "total_frames": previous_frame,
                "total_duration_sec": previous_frame / fps,
                "source_range_sec": list(source_range) if source_range is not None else None,
                "source_time_semantics": "recorded trace time" if source_range is not None else
                    "trace state/event; no execution timestamp asserted",
                "phases": phases}
    errors = validate_timeline(timeline, expected_phase_ids=[b["phase_id"] for b in beats],
                               source_range=source_range)
    if errors:
        raise ValueError("invalid timeline: " + "; ".join(errors))
    timeline["timeline_sha256"] = timeline_hash(timeline)
    return timeline


def validate_timeline(timeline: dict[str, Any], *, expected_phase_ids: list[str] | None = None,
                      source_range: tuple[float, float] | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(timeline, dict) or timeline.get("schema") != SCHEMA:
        return [f"timeline schema must be {SCHEMA}"]
    fps, total = timeline.get("fps"), timeline.get("total_frames")
    if not isinstance(fps, int) or isinstance(fps, bool) or fps <= 0:
        errors.append("fps must be a positive integer")
        return errors
    if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
        errors.append("total_frames must be a positive integer")
    phases = timeline.get("phases")
    if not isinstance(phases, list) or not phases:
        return errors + ["phases must be a non-empty list"]
    ids = [p.get("phase_id") for p in phases if isinstance(p, dict)]
    if len(ids) != len(phases) or any(not isinstance(i, str) or not i for i in ids):
        errors.append("each phase requires a phase_id")
    if len(set(ids)) != len(ids):
        errors.append("phase IDs must be unique")
    if expected_phase_ids is not None and ids != expected_phase_ids:
        errors.append("timeline phase IDs/order do not match storyboard")
    cursor = 0
    source_low, source_high = source_range if source_range is not None else (None, None)
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        start, end = phase.get("presentation_start_frame"), phase.get("presentation_end_frame")
        if not isinstance(start, int) or not isinstance(end, int) or start != cursor or end <= start:
            errors.append(f"phase {phase.get('phase_id')} has gap, overlap, or empty frame range")
            if isinstance(end, int) and end > cursor:
                cursor = end
            continue
        if total and end > total:
            errors.append(f"phase {phase.get('phase_id')} exceeds total frame count")
        if phase.get("playback_mode") not in PLAYBACK_MODES:
            errors.append(f"phase {phase.get('phase_id')} has invalid playback_mode")
        if phase.get("visual_goal") not in VISUAL_GOALS:
            errors.append(f"phase {phase.get('phase_id')} has invalid visual_goal")
        start_source, end_source = phase.get("source_start_sec"), phase.get("source_end_sec")
        if (start_source is None) != (end_source is None):
            errors.append(f"phase {phase.get('phase_id')} has incomplete source interval")
        elif start_source is not None:
            try:
                a = _finite_number(start_source, "source_start_sec")
                b = _finite_number(end_source, "source_end_sec")
                if b < a and phase["playback_mode"] != "replay":
                    errors.append(f"phase {phase.get('phase_id')} moves source time backward")
                if source_low is not None and (a < source_low - 1e-9 or b > source_high + 1e-9):
                    errors.append(f"phase {phase.get('phase_id')} exceeds source range")
            except ValueError as exc:
                errors.append(str(exc))
        cursor = end
    if isinstance(total, int) and cursor != total:
        errors.append("last phase end does not equal total_frames")
    try:
        duration = _finite_number(timeline.get("total_duration_sec"), "total_duration_sec")
        if isinstance(total, int) and not math.isclose(duration, total / fps, abs_tol=1e-9):
            errors.append("total_duration_sec does not match total_frames/fps")
    except ValueError as exc:
        errors.append(str(exc))
    stored_hash = timeline.get("timeline_sha256")
    if stored_hash is not None and stored_hash != timeline_hash(timeline):
        errors.append("timeline_sha256 does not match timeline contents")
    return errors


def timeline_hash(timeline: dict[str, Any]) -> str:
    value = {key: item for key, item in timeline.items() if key != "timeline_sha256"}
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def source_time_for_frame(timeline: dict[str, Any], frame: int) -> tuple[str, float | None]:
    """Map one zero-based video frame to the recorded source time for its phase."""
    if not isinstance(frame, int) or frame < 0 or frame >= timeline.get("total_frames", 0):
        raise ValueError("frame is outside timeline")
    for phase in timeline["phases"]:
        start = phase["presentation_start_frame"]
        end = phase["presentation_end_frame"]
        if start <= frame < end:
            a, b = phase["source_start_sec"], phase["source_end_sec"]
            if a is None:
                return phase["phase_id"], None
            if phase["playback_mode"] == "hold":
                return phase["phase_id"], float(a)
            if phase["playback_mode"] == "hold_and_analysis":
                return phase["phase_id"], float(b)
            ratio = (frame - start) / max(1, end - start - 1)
            return phase["phase_id"], float(a + (b - a) * ratio)
    raise ValueError("frame has no phase mapping")
