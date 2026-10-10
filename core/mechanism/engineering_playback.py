"""Frame-to-sample mapping for trace-backed engineering plots."""
from __future__ import annotations

import math
from bisect import bisect_right
from typing import Any

import numpy as np

from core.mechanism.engineering_trace import validate_time_series
from core.mechanism.timeline import source_time_for_frame, validate_timeline


ZERO_ORDER_HOLD_SIGNALS = {
    "speed_reference", "torque_reference", "current_d_reference", "current_q_reference",
    "current_d_feedback", "current_q_feedback", "controller_output", "pwm_duty", "sample_index",
}


def interpolation_for_signal(name: str) -> str:
    """References and sampled controller feedback hold each recorded update."""
    return "zero_order_hold" if name in ZERO_ORDER_HOLD_SIGNALS or name.endswith("_reference") else "linear"


def source_time_to_x(source_time: float, source_range: tuple[float, float] | list[float],
                     x0: float, x1: float) -> float:
    """Map absolute source time to a shared plot axis without per-signal stretching."""
    values = (source_time, *source_range, x0, x1)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in values):
        raise ValueError("source time, range and plot bounds must be finite numbers")
    start, end = float(source_range[0]), float(source_range[1])
    if end <= start:
        raise ValueError("source range must have positive duration")
    if source_time < start - 1e-9 or source_time > end + 1e-9:
        raise ValueError("signal sample lies outside the common source range")
    ratio = min(1.0, max(0.0, (float(source_time) - start) / (end - start)))
    return float(x0 + ratio * (x1 - x0))


def signal_value_at(signal: dict[str, Any], source_time: float, policy: str) -> float:
    """Evaluate a display state from recorded samples; never mutates the trace.

    Continuous states use linear interpolation inside their sample clock and hold
    the first/last recorded value outside it. Sampled controller values use ZOH.
    """
    if policy not in {"linear", "zero_order_hold"}:
        raise ValueError(f"unsupported signal interpolation policy: {policy}")
    times = signal.get("timestamps")
    values = signal.get("values")
    if (not isinstance(times, list) or not isinstance(values, list) or not times
            or len(times) != len(values)):
        raise ValueError("signal requires matching non-empty timestamp and value arrays")
    t = np.asarray(times, dtype=float)
    v = np.asarray(values, dtype=float)
    if (not math.isfinite(source_time) or not np.isfinite(t).all() or not np.isfinite(v).all()
            or np.any(np.diff(t) <= 0)):
        raise ValueError("signal samples and source time must be finite with increasing timestamps")
    if policy == "zero_order_hold":
        index = max(0, min(len(t) - 1, bisect_right(t.tolist(), source_time) - 1))
        return float(v[index])
    return float(np.interp(source_time, t, v))


def engineering_state_for_frame(trace: dict[str, Any], timeline: dict[str, Any],
                                frame_index: int) -> dict[str, Any]:
    """Resolve one presentation frame through timeline source time into trace samples."""
    payload = trace.get("payload", trace)
    validated_payload = payload if payload.get("kind") == "time_series" else {**payload, "kind": "time_series"}
    errors = validate_time_series(validated_payload)
    if errors:
        raise ValueError("invalid engineering trace: " + "; ".join(errors))
    root_times = payload.get("timestamps")
    if not root_times:
        raise ValueError("engineering playback requires a root source clock")
    source_range = (float(root_times[0]), float(root_times[-1]))
    errors = validate_timeline(timeline, source_range=source_range)
    if errors:
        raise ValueError("invalid engineering timeline: " + "; ".join(errors))
    phase_id, source_time = source_time_for_frame(timeline, frame_index)
    if source_time is None or not math.isfinite(source_time):
        raise ValueError("engineering timeline phase has no finite source time")
    signals = {}
    for name, signal in payload["signals"].items():
        policy = interpolation_for_signal(name)
        signal_clock = signal if signal.get("timestamps") is not None else {
            **signal, "timestamps": root_times,
        }
        signals[name] = {"value": signal_value_at(signal_clock, source_time, policy),
                         "unit": signal["unit"], "interpolation": policy}
    phase = next(item for item in timeline["phases"] if item["phase_id"] == phase_id)
    return {"frame_index": frame_index, "phase_id": phase_id,
            "presentation_time_sec": frame_index / timeline["fps"],
            "source_time_sec": source_time, "playback_mode": phase["playback_mode"],
            "signals": signals}
