"""Validation helpers for sampled engineering signals and integer event clocks.

The V11 mechanism envelope remains the outer contract. These payload helpers
make units, independent sample clocks and integer protocol ticks explicit.
"""
from __future__ import annotations

import math
from typing import Any


def _times(values: Any, name: str, *, integer: bool = False) -> list[str]:
    if not isinstance(values, list) or not values:
        return [f"{name} must be a non-empty list"]
    errors = []
    previous = None
    for i, value in enumerate(values):
        valid_type = type(value) is int if integer else (type(value) in (int, float))
        if not valid_type or (not integer and not math.isfinite(value)):
            errors.append(f"{name}[{i}] must be {'an integer tick' if integer else 'finite numeric'}")
            break
        if previous is not None and value <= previous:
            errors.append(f"{name} must strictly increase")
            break
        previous = value
    return errors


def validate_time_series(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict) or payload.get("kind") != "time_series":
        return ["engineering payload kind must be time_series"]
    inherited = payload.get("timestamps")
    if inherited is not None:
        errors.extend(_times(inherited, "timestamps"))
    signals = payload.get("signals")
    if not isinstance(signals, dict) or not signals:
        return errors + ["signals must be a non-empty object"]
    for name, signal in signals.items():
        if not isinstance(name, str) or not isinstance(signal, dict):
            errors.append("signal entries require a name and object")
            continue
        if not isinstance(signal.get("unit"), str) or not signal["unit"].strip():
            errors.append(f"signal {name} requires a unit")
        values = signal.get("values")
        if not isinstance(values, list) or not values:
            errors.append(f"signal {name} values must be a non-empty list")
            continue
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            errors.append(f"signal {name} contains non-finite or non-numeric values")
        times = signal.get("timestamps", inherited)
        if times is None:
            errors.append(f"signal {name} has no timestamp source")
        else:
            errors.extend(_times(times, f"signal {name} timestamps"))
            if len(times) != len(values):
                errors.append(f"signal {name} timestamp/value lengths differ")
    return errors


def validate_discrete_events(payload: dict[str, Any]) -> list[str]:
    if not isinstance(payload, dict) or payload.get("kind") != "discrete_events":
        return ["engineering payload kind must be discrete_events"]
    events = payload.get("events")
    if not isinstance(events, list):
        return ["events must be a list"]
    previous = -1
    errors = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f"events[{index}] must be an object")
            continue
        tick = event.get("timestamp")
        if type(tick) is not int or tick < 0:
            errors.append(f"events[{index}].timestamp must be a non-negative integer tick")
        elif tick < previous:
            errors.append(f"events[{index}] is out of timestamp order")
        else:
            previous = tick
        if not isinstance(event.get("node"), str) or not event["node"]:
            errors.append(f"events[{index}].node must be non-empty")
        if not isinstance(event.get("event"), str) or not event["event"]:
            errors.append(f"events[{index}].event must be non-empty")
    return errors
