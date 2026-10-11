"""Beat-aware sparse renderer plan using the shared integer-frame timeline."""
from __future__ import annotations

from typing import Any

TOOL_RENDERER = {"M": "manim", "B": "blender"}


def build_sparse_render_plan(
    manifest: dict[str, Any], timeline: dict[str, Any], *,
    supported_renderers: tuple[str, ...], supports_stills: bool,
) -> dict[str, Any]:
    """Build contiguous half-open timeline segments with explicit still policy.

    Timeline frames are zero-based/half-open. Blender source frame numbers are
    one-based/inclusive, so [start, end) maps exactly to [start + 1, end].
    """
    fps = timeline.get("fps")
    total = timeline.get("total_frames")
    beats, phases = manifest.get("beats"), timeline.get("phases")
    if type(fps) is not int or fps <= 0 or type(total) is not int or total <= 0:
        raise ValueError("sparse plan requires positive integer fps and total_frames")
    if not isinstance(beats, list) or not isinstance(phases, list) or len(beats) != len(phases) or not beats:
        raise ValueError("sparse plan requires one ordered timeline phase per manifest beat")

    cursor = 0
    segments: list[dict[str, Any]] = []
    for beat, phase in zip(beats, phases):
        if not isinstance(beat, dict) or not isinstance(phase, dict):
            raise ValueError("sparse plan beats and phases must be objects")
        beat_id = beat.get("id")
        if not beat_id or phase.get("phase_id") != beat.get("phase_id"):
            raise ValueError("sparse plan beat and phase IDs/order do not match")
        start = phase.get("presentation_start_frame")
        end = phase.get("presentation_end_frame")
        if type(start) is not int or type(end) is not int or start != cursor or end <= start or end > total:
            raise ValueError(f"sparse plan has gap, overlap, or invalid range at beat {beat_id}")
        tool = beat.get("tool")
        renderer = TOOL_RENDERER.get(tool)
        if renderer is None or renderer not in supported_renderers:
            raise ValueError(f"unsupported sparse renderer {tool!r} at beat {beat_id}")
        declared_mode = beat.get("render_mode")
        if declared_mode not in (None, "still"):
            raise ValueError(f"unsupported sparse render_mode {declared_mode!r} at beat {beat_id}")
        if declared_mode == "still" and (renderer != "blender" or not supports_stills):
            raise ValueError(f"beat {beat_id} requests a still unsupported by its renderer capability")
        mode = "still" if declared_mode == "still" else ("video" if renderer == "manim" else "animation")
        segment = {
            "beat_id": beat_id, "phase_id": phase["phase_id"], "renderer": renderer, "mode": mode,
            "timeline_start": start, "timeline_end": end, "output_frames": end - start,
        }
        if renderer == "blender":
            if mode == "still":
                segment["source_frame"] = start + 1
            else:
                segment["source_frame_start"] = start + 1
                segment["source_frame_end"] = end
                segment["source_frames"] = end - start
        segments.append(segment)
        cursor = end
    if cursor != total:
        raise ValueError(f"sparse segments cover {cursor} frames, expected {total}")
    return {
        "schema": "education-render-segments/v1", "strategy": "sparse", "fps": fps,
        "total_frames": total, "timeline_sha256": timeline.get("timeline_sha256"),
        "segments": segments,
        "blender_still_count": sum(s["mode"] == "still" and s["renderer"] == "blender" for s in segments),
        "blender_animation_frames": sum(s.get("source_frames", 0) for s in segments if s["renderer"] == "blender"),
    }


def validate_sparse_render_plan(plan: dict[str, Any], timeline: dict[str, Any]) -> list[str]:
    errors = []
    if plan.get("schema") != "education-render-segments/v1":
        return ["unsupported sparse render plan schema"]
    if plan.get("fps") != timeline.get("fps") or plan.get("total_frames") != timeline.get("total_frames"):
        errors.append("sparse plan rate or total frame count differs from timeline")
    if plan.get("timeline_sha256") != timeline.get("timeline_sha256"):
        errors.append("sparse plan timeline hash differs from timeline")
    cursor = 0
    for segment in plan.get("segments", []):
        start, end = segment.get("timeline_start"), segment.get("timeline_end")
        if type(start) is not int or type(end) is not int or start != cursor or end <= start:
            errors.append(f"gap, overlap, or invalid segment range at {segment.get('beat_id')}")
            continue
        if segment.get("output_frames") != end - start:
            errors.append(f"output frame count mismatch at {segment.get('beat_id')}")
        if segment.get("renderer") == "blender":
            if segment.get("mode") == "still":
                if segment.get("source_frame") != start + 1:
                    errors.append(f"Blender still source frame mismatch at {segment.get('beat_id')}")
            elif (segment.get("mode") != "animation"
                  or segment.get("source_frame_start") != start + 1
                  or segment.get("source_frame_end") != end
                  or segment.get("source_frames") != end - start):
                errors.append(f"Blender source frame mapping mismatch at {segment.get('beat_id')}")
        cursor = end
    if cursor != timeline.get("total_frames"):
        errors.append("sparse segments do not cover the full timeline")
    return errors
