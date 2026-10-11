"""Stable contracts for PyBaMM input and education-ready result files."""

CONFIG_SCHEMA = "battery-simulation-config/v1"
RESULT_SCHEMA = "battery-simulation-result/v1"
SOLVER_ID = "pybamm"
MODEL_ID = "SPM"
PARAMETER_SET_ID = "Chen2020"
CSV_COLUMNS = (
    "time_s",
    "terminal_voltage_v",
    "current_a",
    "discharge_capacity_ah",
    "estimated_soc",
)
UNITS = {
    "time": "s",
    "terminal_voltage": "V",
    "current": "A",
    "discharge_capacity": "Ah",
    "estimated_soc": "1",
}


def validate_config(config: object) -> list[str]:
    if not isinstance(config, dict):
        return ["config must be a JSON object"]
    errors = []
    if config.get("schema") != CONFIG_SCHEMA:
        errors.append(f"schema must be {CONFIG_SCHEMA}")
    if config.get("solver") != SOLVER_ID:
        errors.append(f"solver must be {SOLVER_ID!r}")
    if config.get("model") != MODEL_ID:
        errors.append(f"model must be {MODEL_ID!r}; only SPM is registered")
    if config.get("parameter_set") != PARAMETER_SET_ID:
        errors.append(f"parameter_set must be {PARAMETER_SET_ID!r}")
    initial_soc = config.get("initial_soc")
    if type(initial_soc) not in (int, float) or not 0 < initial_soc <= 1:
        errors.append("initial_soc must be finite and in (0, 1]")
    elif not __import__("math").isfinite(initial_soc):
        errors.append("initial_soc must be finite and in (0, 1]")
    c_rate = config.get("discharge_c_rate")
    if type(c_rate) not in (int, float) or not __import__("math").isfinite(c_rate) or c_rate <= 0:
        errors.append("discharge_c_rate must be a finite positive number")
    duration = config.get("requested_duration_s")
    if type(duration) is not int or not 60 <= duration <= 24 * 3600:
        errors.append("requested_duration_s must be an integer from 60 to 86400")
    sample = config.get("sample_interval_s")
    if type(sample) is not int or sample < 1 or sample > 60:
        errors.append("sample_interval_s must be an integer from 1 to 60")
    elif type(duration) is int and duration % sample:
        errors.append("requested_duration_s must be divisible by sample_interval_s")
    solver_options = config.get("solver_options")
    if (not isinstance(solver_options, dict)
            or set(solver_options) != {"rtol", "atol"}
            or any(type(solver_options.get(key)) not in (int, float)
                   or not __import__("math").isfinite(solver_options[key])
                   or solver_options[key] <= 0 for key in ("rtol", "atol"))):
        errors.append("solver_options must contain finite positive rtol and atol")
    return errors
