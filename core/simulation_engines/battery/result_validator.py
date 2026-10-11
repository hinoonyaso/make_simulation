"""Validate solver output files and their config/result provenance."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from core.simulation_engines.battery.schema import (CSV_COLUMNS, RESULT_SCHEMA, UNITS,
                                                     validate_config)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_timeseries(rows: list[dict[str, Any]], metadata: dict[str, Any]) -> list[str]:
    errors = []
    if len(rows) < 2:
        return ["timeseries must contain at least two samples"]
    values: dict[str, list[float]] = {key: [] for key in CSV_COLUMNS}
    for index, row in enumerate(rows):
        for key in CSV_COLUMNS:
            try:
                value = float(row[key])
            except (KeyError, TypeError, ValueError):
                errors.append(f"sample {index} has invalid {key}")
                continue
            if not math.isfinite(value):
                errors.append(f"sample {index} has non-finite {key}")
            values[key].append(value)
    if errors:
        return errors
    time_s = values["time_s"]
    if time_s[0] != 0 or any(right <= left for left, right in zip(time_s, time_s[1:])):
        errors.append("time_s must start at zero and increase strictly")
    end_time = metadata.get("actual_end_time_s")
    requested = metadata.get("requested_duration_s")
    if not isinstance(end_time, (int, float)) or not math.isclose(time_s[-1], end_time, abs_tol=1e-7):
        errors.append("last timeseries timestamp does not match actual_end_time_s")
    if isinstance(requested, (int, float)) and time_s[-1] > requested + 1e-7:
        errors.append("actual simulation time exceeds requested duration")
    lower = metadata.get("voltage_cutoff_lower_v")
    upper = metadata.get("voltage_cutoff_upper_v")
    voltage = values["terminal_voltage_v"]
    if min(voltage) < 1.5 or max(voltage) > 5.0:
        errors.append("terminal voltage is outside the broad physical validation range [1.5, 5.0] V")
    if isinstance(lower, (int, float)) and min(voltage) < lower - .05:
        errors.append("terminal voltage crossed the configured lower voltage boundary beyond tolerance")
    if isinstance(upper, (int, float)) and max(voltage) > upper + .05:
        errors.append("terminal voltage crossed the configured upper voltage boundary beyond tolerance")
    currents = values["current_a"]
    if any(current <= 0 for current in currents):
        errors.append("PyBaMM discharge convention expects positive Current [A] for this constant-current run")
    if any(right + 1e-9 < left for left, right in zip(values["discharge_capacity_ah"],
                                                        values["discharge_capacity_ah"][1:])):
        errors.append("discharge capacity must not decrease during this discharge run")
    capacity = values["discharge_capacity_ah"]
    integrated_ah = sum((left + right) * .5 * (t1 - t0) / 3600
                        for t0, t1, left, right in zip(time_s, time_s[1:], currents, currents[1:]))
    observed_ah = capacity[-1] - capacity[0]
    if abs(integrated_ah - observed_ah) > max(1e-5, .005 * max(observed_ah, 1e-6)):
        errors.append("discharge capacity does not agree with the current-time integral within 0.5%")
    soc = values["estimated_soc"]
    initial = metadata.get("initial_soc")
    nominal_capacity = metadata.get("nominal_capacity_ah")
    if not isinstance(initial, (int, float)) or not isinstance(nominal_capacity, (int, float)) or nominal_capacity <= 0:
        errors.append("SOC validation requires initial_soc and positive nominal_capacity_ah metadata")
    else:
        expected_soc = [initial - (q - capacity[0]) / nominal_capacity for q in capacity]
        if any(abs(a - b) > 1e-7 for a, b in zip(soc, expected_soc)):
            errors.append("estimated_soc does not match Coulomb Counting from model discharge capacity")
        if any(value < -1e-6 or value > initial + 1e-6 for value in soc):
            errors.append("estimated_soc lies outside the physical run bounds")
    return errors


def load_validated_result(directory: str | Path) -> dict[str, Any]:
    root = Path(directory).resolve()
    result_path = root / "result.json"
    timeseries_path = root / "battery_timeseries.csv"
    config_path = root / "simulation_config.json"
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load battery result/config files: {exc}") from exc
    provenance = result.get("solver_execution", {})
    if result.get("schema") != RESULT_SCHEMA or result.get("status") != "PASS":
        raise ValueError("battery result schema/status is not a validated PASS result")
    if result.get("validation", {}).get("status") != "PASS":
        raise ValueError("battery result validation report is not PASS")
    if provenance.get("executed") is not True or provenance.get("solver_id") != "pybamm":
        raise ValueError("battery result lacks executed PyBaMM solver provenance")
    if result.get("units") != UNITS:
        raise ValueError("battery result units do not match the v1 contract")
    config_errors = validate_config(config)
    if config_errors:
        raise ValueError("battery simulation config is invalid: " + "; ".join(config_errors))
    for result_key, config_key in (("model", "model"), ("parameter_set", "parameter_set"),
                                   ("initial_soc", "initial_soc"),
                                   ("discharge_c_rate", "discharge_c_rate"),
                                   ("requested_duration_s", "requested_duration_s"),
                                   ("sample_interval_s", "sample_interval_s")):
        if result.get(result_key) != config.get(config_key):
            raise ValueError(f"battery result {result_key} does not match its simulation config")
    if not result.get("termination_reason"):
        raise ValueError("battery result is missing the solver termination reason")
    config_hash = sha256_file(config_path)
    if result.get("config_sha256") != config_hash:
        raise ValueError("battery simulation config SHA-256 mismatch")
    timeseries_hash = sha256_file(timeseries_path)
    if result.get("result_sha256") != timeseries_hash:
        raise ValueError("battery timeseries SHA-256 mismatch")
    if result.get("result_file") != timeseries_path.name:
        raise ValueError("battery result_file must name the colocated result CSV")
    with timeseries_path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
            raise ValueError("battery timeseries CSV columns do not match the v1 contract")
        rows = list(reader)
    errors = validate_timeseries(rows, result)
    if errors:
        raise ValueError("battery result validation failed: " + "; ".join(errors))
    return {"directory": root, "result": result, "config": config, "rows": rows,
            "result_path": result_path, "timeseries_path": timeseries_path,
            "config_path": config_path}
