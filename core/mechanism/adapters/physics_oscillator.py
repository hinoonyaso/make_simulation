"""SymPy/scipy/control mass-spring-damper execution adapter."""
from __future__ import annotations

import importlib.metadata
import math
from pathlib import Path

import control
import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

from core.mechanism.engineering_trace import validate_time_series
from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope


def _build_timestamps(duration: float, sample_period: float, *, max_samples: int = 1_000_000) -> np.ndarray:
    """Build an increasing output clock that always includes the exact stop time."""
    if (isinstance(duration, bool) or not isinstance(duration, (int, float))
            or not math.isfinite(duration) or duration <= 0):
        raise ValueError("duration must be finite and greater than zero")
    if (isinstance(sample_period, bool) or not isinstance(sample_period, (int, float))
            or not math.isfinite(sample_period) or sample_period <= 0):
        raise ValueError("sample_period must be finite and greater than zero")
    ratio = duration / sample_period
    if not math.isfinite(ratio) or ratio > max_samples:
        raise ValueError("duration/sample_period must produce 2..1,000,000 samples")
    count = int(math.floor(ratio + 1e-12)) + 1
    if count > max_samples:
        raise ValueError("duration/sample_period must produce 2..1,000,000 samples")
    timestamps = np.arange(count, dtype=float) * sample_period
    tolerance = max(sample_period * 1e-10, math.ulp(float(duration)) * 2)
    if math.isclose(float(timestamps[-1]), duration, rel_tol=0.0, abs_tol=tolerance):
        timestamps[-1] = duration
    else:
        timestamps = np.append(timestamps, duration)
    if len(timestamps) < 2 or len(timestamps) > max_samples:
        raise ValueError("duration/sample_period must produce 2..1,000,000 samples")
    if (not np.isfinite(timestamps).all() or timestamps[0] != 0.0
            or timestamps[-1] != duration or np.any(np.diff(timestamps) <= 0)):
        raise ValueError("duration/sample_period produced an invalid timestamp sequence")
    return timestamps


class PhysicsOscillatorAdapter:
    def __init__(self, capability=None):
        self.capability = capability or {}

    def describe_capability(self):
        return self.capability

    def prepare(self, request: MechanismRequest):
        return {"topic": request.topic, **request.options}

    @staticmethod
    def _number(config, key, default, *, lower=None, strict=False):
        value = config.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be finite numeric")
        if lower is not None and (value <= lower if strict else value < lower):
            raise ValueError(f"{key} must be {'greater than' if strict else 'at least'} {lower}")
        return float(value)

    def execute(self, config):
        m = self._number(config, "mass_kg", 1.0, lower=0, strict=True)
        c = self._number(config, "damping_n_s_m", 0.6, lower=0)
        k = self._number(config, "stiffness_n_m", 4.0, lower=0, strict=True)
        x0 = self._number(config, "initial_displacement_m", 0.25)
        v0 = self._number(config, "initial_velocity_m_s", 0.0)
        force = self._number(config, "force_amplitude_n", 0.0, lower=0)
        force_hz = self._number(config, "force_frequency_hz", 0.5, lower=0)
        duration = self._number(config, "duration_s", 8.0, lower=0, strict=True)
        sample = self._number(config, "sample_period_s", 0.01, lower=0, strict=True)
        rtol = self._number(config, "rtol", 1e-9, lower=0, strict=True)
        atol = self._number(config, "atol", 1e-11, lower=0, strict=True)
        timestamps = _build_timestamps(duration, sample)
        count = len(timestamps)
        actual_force = lambda t: force * np.sin(2 * math.pi * force_hz * t)

        time = sp.symbols("t", real=True)
        x = sp.Function("x")
        force_term = force * sp.sin(2 * sp.pi * force_hz * time)
        equation = sp.Eq(m * sp.diff(x(time), time, 2) + c * sp.diff(x(time), time) + k * x(time), force_term)
        try:
            hint = "nth_linear_constant_coeff_homogeneous" if force == 0 else "nth_linear_constant_coeff_undetermined_coefficients"
            sympy_solution = sp.dsolve(equation, x(time), hint=hint,
                ics={x(0): x0, sp.diff(x(time), time).subs(time, 0): v0})
        except (NotImplementedError, ValueError, RecursionError):
            sympy_solution = None
        analytic_values = None
        analytic_error = None
        analytical_reason = "SymPy did not provide a supported closed form; SciPy numerical integration remains the recorded result"
        if sympy_solution is not None:
            analytic_fn = sp.lambdify(time, sympy_solution.rhs, modules="numpy")
            analytic_values = np.asarray(analytic_fn(timestamps), dtype=float)
            if analytic_values.ndim == 0:
                analytic_values = np.full_like(timestamps, float(analytic_values))

        A = np.array([[0.0, 1.0], [-k / m, -c / m]], dtype=float)
        B = np.array([[0.0], [1.0 / m]], dtype=float)
        system = control.ss(A, B, np.eye(2), np.zeros((2, 1)))

        def rhs(t, state):
            pos, vel = state
            return (vel, (actual_force(t) - c * vel - k * pos) / m)

        result = solve_ivp(rhs, (0.0, duration), (x0, v0), t_eval=timestamps,
                           rtol=rtol, atol=atol, method="DOP853")
        if not result.success or result.y.shape != (2, count):
            raise RuntimeError(f"SciPy solve_ivp failed: {result.message}")
        position, velocity = result.y
        critical_c = 2.0 * math.sqrt(m*k)
        damping_sweep = {"undamped": 0.0, "critical": critical_c,
                         "overdamped": 1.5 * critical_c}
        sweep_positions = {}
        for case, case_c in damping_sweep.items():
            def case_rhs(t, state, case_c=case_c):
                pos, vel = state
                return (vel, (actual_force(t) - case_c*vel - k*pos)/m)
            case_result = solve_ivp(case_rhs, (0.0, duration), (x0, v0), t_eval=timestamps,
                                    rtol=rtol, atol=atol, method="DOP853")
            if not case_result.success or case_result.y.shape != (2, len(timestamps)):
                raise RuntimeError(f"SciPy damping comparison failed for {case}: {case_result.message}")
            sweep_positions[case] = case_result.y[0]
        energy = .5 * m * velocity**2 + .5 * k * position**2
        if analytic_values is not None:
            analytic_error = float(np.max(np.abs(position - analytic_values)))
            analytical_reason = "closed-form ODE solution from SymPy; compared at recorded output times"
        validation = {"solver_success": bool(result.success), "sample_count": count,
                      "max_abs_analytic_error_m": analytic_error,
                      "relative_energy_drift": float(abs(energy[-1] - energy[0]) / max(energy[0], 1e-30)),
                      "energy_nonincreasing_with_damping": bool(c == 0 or np.all(np.diff(energy) <= max(1e-12, energy[0]*1e-8))),
                      "energy_balance_residual_j": float(energy[-1] - energy[0] - np.trapezoid(-c*velocity**2 + actual_force(timestamps)*velocity, timestamps))}
        payload = {"kind": "time_series", "time_unit": "s", "timestamps": timestamps.tolist(),
                   "signals": {"position": {"unit": "m", "values": position.tolist()},
                               "velocity": {"unit": "m/s", "values": velocity.tolist()},
                               "kinetic_energy": {"unit": "J", "values": (.5*m*velocity**2).tolist()},
                               "potential_energy": {"unit": "J", "values": (.5*k*position**2).tolist()},
                               "total_energy": {"unit": "J", "values": energy.tolist()},
                               "external_force": {"unit": "N", "values": [float(actual_force(t)) for t in timestamps]},
                               "position_undamped": {"unit": "m", "values": sweep_positions["undamped"].tolist()},
                               "position_critical": {"unit": "m", "values": sweep_positions["critical"].tolist()},
                               "position_overdamped": {"unit": "m", "values": sweep_positions["overdamped"].tolist()},
                               **({"analytic_position": {"unit": "m", "values": analytic_values.tolist()}}
                                  if analytic_values is not None else {})},
                   "equation": f"{m:g} x'' + {c:g} x' + {k:g} x = F(t)",
                   "assumptions": ["one translational degree of freedom", "linear spring and viscous damping",
                                   "point mass", "force is zero or sinusoidal as configured"],
                   "parameters": {"mass_kg": m, "damping_n_s_m": c, "stiffness_n_m": k,
                                  "initial_displacement_m": x0, "initial_velocity_m_s": v0,
                                  "force_amplitude_n": force, "force_frequency_hz": force_hz,
                                  "duration_s": duration},
                   "solver": {"name": "scipy.solve_ivp", "method": "DOP853", "rtol": rtol,
                              "atol": atol, "sample_period_s": sample},
                   "math": {"symbolic_equation": str(equation), "sympy_solution": str(sympy_solution) if sympy_solution is not None else None,
                            "analytic_validation": analytical_reason},
                   "validation": validation}
        payload["damping_sweep"] = {"damping_n_s_m": damping_sweep,
                                    "solver": "SciPy solve_ivp DOP853",
                                    "same_mass_stiffness_initial_conditions_force": True}
        return make_envelope(domain="classical_physics", topic="physics_oscillator",
            execution_type="numerical_simulation", inputs=[{"id": "parameters", "value": payload["parameters"]}],
            operations=[{"id": "solve_ode", "engine": "scipy.solve_ivp", "method": "DOP853"},
                        {"id": "symbolic_model", "engine": "SymPy dsolve"},
                        {"id": "state_space", "engine": "python-control StateSpace", "A": A.tolist(), "B": B.tolist()}],
            outputs=[{"id": "position", "unit": "m", "value": position.tolist()},
                     {"id": "velocity", "unit": "m/s", "value": velocity.tolist()},
                     {"id": "total_energy", "unit": "J", "value": energy.tolist()}],
            payload=payload, timestamps=timestamps.tolist(),
            provenance={"engine": "SciPy solve_ivp", "engine_version": importlib.metadata.version("scipy"),
                        "symbolic_engine": "SymPy", "symbolic_engine_version": importlib.metadata.version("sympy"),
                        "control_engine": "python-control", "control_engine_version": importlib.metadata.version("control")},
            limitations=["Linear single-DOF educational model; no material hysteresis, friction or spatial modes.",
                         "A sinusoidally forced response is numerically integrated; no closed-form error is claimed."])

    def validate(self, trace):
        errors = validate_envelope(trace)
        if trace.get("domain") != "classical_physics" or trace.get("topic") != "physics_oscillator":
            errors.append("oscillator trace domain/topic mismatch")
        payload = trace.get("payload", {})
        errors.extend(validate_time_series(payload))
        try:
            p = payload["parameters"]
            if p["mass_kg"] <= 0 or p["stiffness_n_m"] <= 0 or p["damping_n_s_m"] < 0:
                errors.append("oscillator physical parameters are outside valid range")
            signals = payload["signals"]
            times = np.asarray(payload["timestamps"], dtype=float)
            expected_duration = p.get("duration_s", float(times[-1]) if len(times) else None)
            if (len(times) < 2 or times[0] != 0.0 or times[-1] != expected_duration
                    or payload["validation"]["sample_count"] != len(times)):
                errors.append("oscillator duration/sample count does not match source timestamps")
            if trace.get("timestamps") != payload.get("timestamps"):
                errors.append("oscillator envelope and payload timestamps differ")
            x = np.asarray(signals["position"]["values"], dtype=float)
            v = np.asarray(signals["velocity"]["values"], dtype=float)
            e = np.asarray(signals["total_energy"]["values"], dtype=float)
            expected = .5*p["mass_kg"]*v**2 + .5*p["stiffness_n_m"]*x**2
            if not np.allclose(expected, e, rtol=1e-9, atol=1e-12):
                errors.append("oscillator mechanical-energy equation mismatch")
            reference = signals.get("analytic_position")
            if reference:
                err = float(np.max(np.abs(x - np.asarray(reference["values"], dtype=float))))
                if err > max(2e-7, 5*payload["solver"]["rtol"]):
                    errors.append(f"analytic/numeric position error too high: {err}")
            if p["damping_n_s_m"] > 0 and p["force_amplitude_n"] == 0 and np.any(np.diff(e) > max(1e-9, e[0]*2e-7)):
                errors.append("unforced damped oscillator energy increased beyond tolerance")
            sweep = payload["damping_sweep"]["damping_n_s_m"]
            for case, case_c in sweep.items():
                def reference_rhs(t, state):
                    pos, vel = state
                    f = p["force_amplitude_n"]*math.sin(2*math.pi*p["force_frequency_hz"]*t)
                    return (vel, (f-case_c*vel-p["stiffness_n_m"]*pos)/p["mass_kg"])
                times = np.asarray(payload["timestamps"],dtype=float)
                reference = solve_ivp(reference_rhs,(float(times[0]),float(times[-1])),
                    (p["initial_displacement_m"],p["initial_velocity_m_s"]),t_eval=times,
                    rtol=payload["solver"]["rtol"],atol=payload["solver"]["atol"],method="DOP853")
                recorded = np.asarray(signals[f"position_{case}"]["values"],dtype=float)
                if not reference.success or not np.allclose(recorded,reference.y[0],rtol=1e-9,atol=1e-11):
                    errors.append(f"{case} damping comparison does not match its SciPy recomputation")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(f"oscillator trace payload invalid: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        return {"kind": "engineering", "domain": trace["domain"], "topic": trace["topic"],
                "title": "질량–스프링–댐퍼: 실제 수치 해석", "trace_id": trace["trace_id"],
                "timestamps": p["timestamps"], "signals": p["signals"], "units": {k:v["unit"] for k,v in p["signals"].items()},
                "parameters": p["parameters"], "equation": p["equation"],
                "validation": p["validation"], "math": p["math"], "solver": p["solver"],
                "visualization": "sampled_waveforms", "source_time_unit": "s"}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
