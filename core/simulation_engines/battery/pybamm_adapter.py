"""Run a reproducible CPU SPM discharge and write validated trace artifacts."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import time
from typing import Any

from core.simulation_engines.battery.result_validator import load_validated_result, sha256_file, validate_timeseries
from core.simulation_engines.battery.schema import CSV_COLUMNS, RESULT_SCHEMA, SOLVER_ID, UNITS, validate_config


def execute_config(config_path: str | Path, output_dir: str | Path, run_id: str | None = None) -> dict[str, Any]:
    source = Path(config_path).resolve()
    try:
        config = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load simulation config: {exc}") from exc
    errors = validate_config(config)
    if errors:
        raise ValueError("invalid battery simulation config: " + "; ".join(errors))
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=False)
    config_copy = root / "simulation_config.json"
    config_copy.write_bytes(source.read_bytes())

    try:
        import numpy as np
        import pybamm
    except ImportError as exc:
        raise RuntimeError("PyBaMM battery solver is unavailable; install with `uv sync --group sim-battery`") from exc

    parameter_values = pybamm.ParameterValues(config["parameter_set"])
    nominal_capacity = float(parameter_values["Nominal cell capacity [A.h]"])
    if not nominal_capacity > 0:
        raise RuntimeError("PyBaMM parameter set reports a non-positive nominal cell capacity")
    parameter_values.set_initial_state(float(config["initial_soc"]))
    parameter_values["Current function [A]"] = nominal_capacity * float(config["discharge_c_rate"])
    model = pybamm.lithium_ion.SPM()
    options = config["solver_options"]
    solver = pybamm.IDAKLUSolver(rtol=float(options["rtol"]), atol=float(options["atol"]))
    simulation = pybamm.Simulation(model, parameter_values=parameter_values, solver=solver)
    duration = config["requested_duration_s"]
    interval = config["sample_interval_s"]
    t_eval = np.arange(0, duration + interval, interval, dtype=float)
    started = time.perf_counter()
    solution = simulation.solve(t_eval=t_eval)
    execution_seconds = time.perf_counter() - started

    # IDAKLU may retain adaptive internal solver points. Evaluate the saved
    # solution at the declared fixed output clock for stable renderer sampling.
    time_s = t_eval
    voltage = np.asarray(solution["Voltage [V]"](t_eval), dtype=float).reshape(-1)
    current = np.asarray(solution["Current [A]"](t_eval), dtype=float).reshape(-1)
    capacity = np.asarray(solution["Discharge capacity [A.h]"](t_eval), dtype=float).reshape(-1)
    arrays = (time_s, voltage, current, capacity)
    if any(len(array) != len(time_s) for array in arrays):
        raise RuntimeError("PyBaMM returned inconsistent output array lengths")
    estimated_soc = float(config["initial_soc"]) - (capacity - capacity[0]) / nominal_capacity
    rows = [{"time_s": t, "terminal_voltage_v": v, "current_a": i,
             "discharge_capacity_ah": q, "estimated_soc": soc}
            for t, v, i, q, soc in zip(time_s, voltage, current, capacity, estimated_soc)]
    csv_path = root / "battery_timeseries.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: format(float(row[key]), ".12g") for key in CSV_COLUMNS})

    parameter_keys = (
        "Nominal cell capacity [A.h]", "Lower voltage cut-off [V]", "Upper voltage cut-off [V]",
        "Current function [A]",
    )
    relevant_parameters = {key: float(parameter_values[key]) for key in parameter_keys}
    result = {
        "schema": RESULT_SCHEMA,
        "status": "PENDING_VALIDATION",
        "engine": "PyBaMM",
        "model": "SPM",
        "parameter_set": config["parameter_set"],
        "units": UNITS,
        "solver_execution": {
            "executed": True,
            "solver_id": SOLVER_ID,
            "solver_name": type(solver).__name__,
            "solver_options": options,
            "pybamm_version": pybamm.__version__,
            "pybammsolvers_version": _package_version("pybammsolvers"),
            "casadi_version": _package_version("casadi"),
            "python_version": platform.python_version(),
            "execution_seconds": execution_seconds,
            "run_id": run_id or f"battery-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "initial_soc": float(config["initial_soc"]),
        "estimated_soc_method": "coulomb_counting_from_model_output",
        "discharge_c_rate": float(config["discharge_c_rate"]),
        "nominal_capacity_ah": nominal_capacity,
        "requested_duration_s": duration,
        "actual_end_time_s": float(time_s[-1]),
        "termination_reason": str(solution.termination),
        "sample_interval_s": interval,
        "result_sampling": "PyBaMM Solution evaluation at fixed sample times; no renderer interpolation or extrapolation.",
        "sample_count": len(rows),
        "voltage_cutoff_lower_v": relevant_parameters["Lower voltage cut-off [V]"],
        "voltage_cutoff_upper_v": relevant_parameters["Upper voltage cut-off [V]"],
        "parameter_values": relevant_parameters,
        "config_sha256": sha256_file(config_copy),
        "result_file": csv_path.name,
        "result_sha256": sha256_file(csv_path),
        "assumptions": [
            "Isothermal Single Particle Model (SPM); not a full electrochemical or thermal cell model.",
            "Chen2020 parameter set is not evidence that the educational 18650 mesh has matching cell chemistry or geometry.",
            "estimated_soc is Coulomb Counting from the model discharge-capacity output, not measured SOC or a BMS estimator.",
        ],
        "limitations": [
            "No electrolyte concentration gradients, heat generation, cell-to-cell variation, ageing, or BMS behavior is modeled.",
            "The Blender 18650 geometry is an educational concept and does not encode spatial PyBaMM fields.",
        ],
    }
    errors = validate_timeseries(rows, result)
    if errors:
        result["status"] = "FAIL"
        result["validation"] = {"status": "FAIL", "errors": errors}
        (root / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError("PyBaMM result validation failed: " + "; ".join(errors))
    result["status"] = "PASS"
    result["validation"] = {
        "status": "PASS",
        "checks": ["finite monotonic timestamps", "equal output lengths", "finite voltage/current/capacity/SOC",
                   "discharge sign", "capacity-current integral consistency", "SOC coulomb-counting consistency",
                   "voltage bounds", "config and result SHA-256"],
    }
    (root / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_validated_result(root)
    return result


def _package_version(package: str) -> str:
    from importlib.metadata import version
    return version(package)
