"""Load and validate solver samples consumed by the battery Manim scene."""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

import numpy as np


def load_samples(context: dict[str, Any], context_path: Path) -> dict[str, np.ndarray]:
    info = context.get("solver_result")
    if not info or info.get("solver_id") != "pybamm":
        raise ValueError("Battery Manim renderer requires a validated PyBaMM result contract")
    path = context_path.parent / info["timeseries_file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != info.get("result_sha256"):
        raise ValueError("Battery Manim result CSV SHA-256 does not match the validated solver contract")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    fields = ("time_s", "terminal_voltage_v", "current_a", "discharge_capacity_ah", "estimated_soc")
    data = {key: np.asarray([float(row[key]) for row in rows], dtype=float) for key in fields}
    if any(not np.isfinite(values).all() for values in data.values()):
        raise ValueError("Battery Manim result samples must contain only finite values")
    if len(data["time_s"]) < 2 or data["time_s"][0] != 0 or np.any(np.diff(data["time_s"]) <= 0):
        raise ValueError("Battery Manim result timestamps are invalid")
    actual_end_time_s = float(info["actual_end_time_s"])
    if not np.isfinite(actual_end_time_s):
        raise ValueError("Battery Manim solver provenance end time must be finite")
    if not np.isclose(data["time_s"][-1], actual_end_time_s, rtol=0, atol=1e-7):
        raise ValueError("Battery Manim result range does not match solver provenance")
    if len(data["time_s"]) != int(info["sample_count"]):
        raise ValueError("Battery Manim sample count does not match solver provenance")
    return data
