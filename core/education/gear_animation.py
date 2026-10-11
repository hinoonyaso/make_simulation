"""Pure frame planning for external gear rotation shared by renderers."""
from __future__ import annotations

import math
from typing import Any


def plan_gear_rotation_keys(manifest: dict[str, Any], timeline: dict[str, Any],
                            omega_ratio: float) -> dict[str, list[dict[str, float | int]]]:
    """Map beat input turns to continuous, boundary-aligned gear keyframes.

    Timeline intervals are half-open and zero-based. Blender frame 1 is
    presentation frame 0, so both keyframe boundaries are shifted by one.
    The returned output rotation uses the shared ideal angular-speed ratio.
    """
    if not math.isfinite(omega_ratio):
        raise ValueError("omega_ratio must be finite")
    phases = {phase["phase_id"]: phase for phase in timeline.get("phases", [])}
    if len(phases) != len(timeline.get("phases", [])):
        raise ValueError("timeline phase IDs must be unique")
    beats = manifest.get("beats", [])
    if {beat.get("phase_id") for beat in beats} != set(phases):
        raise ValueError("manifest beats and timeline phases must match")
    keys: dict[str, list[dict[str, float | int]]] = {
        name: [] for name in ("Pinion_20T", "Pinion_Hub", "Gear_40T", "Gear_Hub")
    }
    input_turns = 0.0
    for beat in beats:
        if beat.get("tool") != "B":
            continue
        phase = phases[beat["phase_id"]]
        start_frame = int(phase["presentation_start_frame"]) + 1
        end_frame = int(phase["presentation_end_frame"]) + 1
        if end_frame <= start_frame:
            raise ValueError(f"phase {beat['phase_id']} has an invalid frame interval")
        try:
            turns = float(beat.get("input_turns", 0.0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"phase {beat['phase_id']} input_turns must be finite") from exc
        if not math.isfinite(turns):
            raise ValueError(f"phase {beat['phase_id']} input_turns must be finite")
        start_turns = input_turns
        input_turns += turns
        pair = (("Pinion_20T", "Pinion_Hub", 1.0),
                ("Gear_40T", "Gear_Hub", omega_ratio))
        for first, second, ratio in pair:
            start_angle = math.tau * start_turns * ratio
            end_angle = math.tau * input_turns * ratio
            for name in (first, second):
                keys[name].extend((
                    {"frame": start_frame, "angle_rad": start_angle},
                    {"frame": end_frame, "angle_rad": end_angle},
                ))
    for values in keys.values():
        values.sort(key=lambda row: int(row["frame"]))
        compact: list[dict[str, float | int]] = []
        for item in values:
            if compact and compact[-1]["frame"] == item["frame"]:
                if not math.isclose(float(compact[-1]["angle_rad"]), float(item["angle_rad"]),
                                    rel_tol=0, abs_tol=1e-12):
                    raise ValueError("adjacent gear beats disagree at a shared frame boundary")
                continue
            compact.append(item)
        values[:] = compact
    return keys
