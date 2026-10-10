"""motulator 0.9 PMSM vector-control simulation adapter (average inverter model)."""
from __future__ import annotations

import importlib.metadata
import math
from pathlib import Path

import numpy as np
from motulator.common.model import Simulation, SolverCfg
from motulator.common.utils import complex2abc
from motulator.drive.control._common import SpeedController
from motulator.drive.control.sm import CurrentVectorController, CurrentVectorControllerCfg, VectorControlSystem
from motulator.drive.model import Drive, MechanicalSystem, SynchronousMachine, SynchronousMachinePars, VoltageSourceConverter

from core.mechanism.engineering_trace import validate_time_series
from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope


class MotorFOCAdapter:
    def __init__(self, capability=None):
        self.capability = capability or {}

    def describe_capability(self):
        return self.capability

    def prepare(self, request: MechanismRequest):
        return {"topic": request.topic, **request.options}

    @staticmethod
    def _finite(config, key, default, *, minimum=None, strict=False):
        value = config.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be finite numeric")
        if minimum is not None and (value <= minimum if strict else value < minimum):
            raise ValueError(f"{key} must be {'greater than' if strict else 'at least'} {minimum}")
        return float(value)

    def execute(self, config):
        duration = self._finite(config, "duration_s", .30, minimum=0, strict=True)
        sample = self._finite(config, "sample_period_s", .0001, minimum=0, strict=True)
        if duration / sample > 100_000:
            raise ValueError("duration/sample_period is limited to 100,000 controller samples")
        rs = self._finite(config, "stator_resistance_ohm", .3, minimum=0, strict=True)
        ld = self._finite(config, "inductance_d_h", .0015, minimum=0, strict=True)
        lq = self._finite(config, "inductance_q_h", .0015, minimum=0, strict=True)
        flux = self._finite(config, "pm_flux_wb", .08, minimum=0, strict=True)
        poles = config.get("pole_pairs", 3)
        if type(poles) is not int or not 1 <= poles <= 32:
            raise ValueError("pole_pairs must be an integer in [1, 32]")
        inertia = self._finite(config, "inertia_kg_m2", .002, minimum=0, strict=True)
        dc = self._finite(config, "dc_bus_v", 48, minimum=1, strict=True)
        max_current = self._finite(config, "current_limit_a", 15, minimum=0, strict=True)
        speed_ref = self._finite(config, "speed_reference_rad_s", 100, minimum=0)
        load = self._finite(config, "load_torque_nm", .5, minimum=0)
        load_time = self._finite(config, "load_step_time_s", .10, minimum=0)
        speed_step = self._finite(config, "speed_step_time_s", .005, minimum=0)
        bandwidth_hz = self._finite(config, "current_bandwidth_hz", 500, minimum=0, strict=True)
        speed_bandwidth_hz = self._finite(config, "speed_bandwidth_hz", 20, minimum=0, strict=True)
        rtol = self._finite(config, "rtol", 1e-6, minimum=0, strict=True)
        atol = self._finite(config, "atol", 1e-8, minimum=0, strict=True)
        if load_time >= duration or speed_step >= duration:
            raise ValueError("load_step_time_s and speed_step_time_s must be before duration_s")

        par = SynchronousMachinePars(n_p=poles, R_s=rs, L_d=ld, L_q=lq, psi_f=flux)
        mechanics = MechanicalSystem(J=inertia)
        model = Drive(SynchronousMachine(par), mechanics, VoltageSourceConverter(u_dc=dc), pwm=False)
        vector = CurrentVectorController(par, CurrentVectorControllerCfg(
            i_s_max=max_current, alpha_c=2*math.pi*bandwidth_hz, T_s=sample,
            J=inertia, sensorless=False))
        controller = VectorControlSystem(vector, SpeedController(
            J=inertia, alpha_s=2*math.pi*speed_bandwidth_hz,
            tau_M_max=max(1.0, load*4)))
        controller.set_speed_ref(lambda t: speed_ref if t >= speed_step else 0.0)
        mechanics.set_external_load_torque(lambda t: load if t >= load_time else 0.0)
        sim = Simulation(model, controller, show_progress=False,
                         cfg=SolverCfg(max_step=sample/5, method="RK45", rtol=rtol, atol=atol))
        result = sim.simulate(t_stop=duration)
        if not result.success:
            raise RuntimeError("motulator simulation stopped before the requested duration")

        # The motor states use motulator's adaptive solver clock. Controller references
        # use its independent digital sample clock. Keep both clocks in the trace.
        mt_raw = np.asarray(result.mdl.t, dtype=float)
        # motulator records the end of a solver interval and a controller-update
        # boundary at the same time. Keep the last state at each timestamp so the
        # public signal clock remains strictly increasing without interpolation.
        _, reverse_indices = np.unique(mt_raw[::-1], return_index=True)
        mt_indices = np.sort(len(mt_raw) - 1 - reverse_indices)
        mt = mt_raw[mt_indices]
        machine = result.mdl.machine
        mech = result.mdl.mechanics
        iabc = np.asarray([complex2abc(value) for value in np.asarray(machine.i_s_ab)[mt_indices]], dtype=float)
        dq = np.asarray(machine.i_s_dq, dtype=complex)[mt_indices]
        ctrl_t = np.asarray(result.ctrl.t, dtype=float)
        ctrl_ref = np.asarray(result.ctrl.ref.tau_M, dtype=float)
        i_ref = np.asarray(result.ctrl.ref.i_s, dtype=complex)
        i_feedback = np.asarray(result.ctrl.fbk.i_s, dtype=complex)
        if len(mt) < 2 or len(ctrl_t) < 2 or not np.isfinite(iabc).all():
            raise RuntimeError("motulator produced an incomplete or non-finite trace")

        # Preserve the real solver/controller samples; rendering uses a separate
        # display_stride in the visual plan and never rewrites the source arrays.
        signals = {
            "phase_current_a": {"unit": "A_peak", "timestamps": mt.tolist(), "values": iabc[:, 0].tolist()},
            "phase_current_b": {"unit": "A_peak", "timestamps": mt.tolist(), "values": iabc[:, 1].tolist()},
            "phase_current_c": {"unit": "A_peak", "timestamps": mt.tolist(), "values": iabc[:, 2].tolist()},
            "current_d": {"unit": "A_peak", "timestamps": mt.tolist(), "values": dq.real.tolist()},
            "current_q": {"unit": "A_peak", "timestamps": mt.tolist(), "values": dq.imag.tolist()},
            "current_d_reference": {"unit": "A_peak", "timestamps": ctrl_t.tolist(), "values": i_ref.real.tolist()},
            "current_q_reference": {"unit": "A_peak", "timestamps": ctrl_t.tolist(), "values": i_ref.imag.tolist()},
            "current_d_feedback": {"unit": "A_peak", "timestamps": ctrl_t.tolist(), "values": i_feedback.real.tolist()},
            "current_q_feedback": {"unit": "A_peak", "timestamps": ctrl_t.tolist(), "values": i_feedback.imag.tolist()},
            "torque": {"unit": "N·m", "timestamps": mt.tolist(), "values": np.asarray(machine.tau_M, dtype=float)[mt_indices].tolist()},
            "speed_rad_s": {"unit": "rad/s", "timestamps": mt.tolist(), "values": np.asarray(mech.w_M, dtype=float)[mt_indices].tolist()},
            "speed_rpm": {"unit": "rpm", "timestamps": mt.tolist(), "values": (np.asarray(mech.w_M, dtype=float)[mt_indices]*60/(2*math.pi)).tolist()},
            "load_torque": {"unit": "N·m", "timestamps": mt.tolist(), "values": np.asarray(mech.tau_L_tot, dtype=float)[mt_indices].tolist()},
            "speed_reference": {"unit": "rad/s", "timestamps": ctrl_t.tolist(),
                                "values": np.asarray(result.ctrl.ref.w_M, dtype=float).tolist()},
            "torque_reference": {"unit": "N·m", "timestamps": ctrl_t.tolist(), "values": ctrl_ref.tolist()},
        }
        payload = {"kind": "time_series", "time_unit": "s", "timestamps": mt.tolist(),
                   "signals": signals, "parameters": {"pole_pairs": poles,
                       "stator_resistance_ohm": rs, "inductance_d_h": ld, "inductance_q_h": lq,
                       "pm_flux_wb": flux, "inertia_kg_m2": inertia, "dc_bus_v": dc,
                       "current_limit_a": max_current, "speed_reference_rad_s": speed_ref,
                       "load_torque_nm": load, "load_step_time_s": load_time,
                       "sample_period_s": sample},
                   "solver": {"name": "motulator Simulation / scipy.solve_ivp", "method": "RK45",
                              "max_step_s": sample/5, "rtol": rtol, "atol": atol,
                              "controller_sample_period_s": sample},
                   "control": {"topology": "PMSM field-oriented vector control",
                               "speed_feedback": "motulator mechanical state (sensored model input)",
                               "inverter_model": "averaged voltage-source converter; PWM switching waveform not simulated",
                               "current_controller_bandwidth_hz": bandwidth_hz,
                               "speed_controller_bandwidth_hz": speed_bandwidth_hz},
                   "validation": {"solver_success": bool(result.success),
                       "finite_currents": bool(np.isfinite(iabc).all()),
                       "max_abs_phase_current_a": float(np.max(np.abs(iabc))),
                       "load_step_detected": bool(np.any(np.asarray(mech.tau_L_tot) > 0)),
                       "speed_final_rad_s": float(np.asarray(mech.w_M)[mt_indices][-1]),
                       "peak_torque_nm": float(np.max(np.abs(np.asarray(machine.tau_M)[mt_indices]))),
                       "model_parameters_are_demonstration_values": True}}
        if not payload["validation"]["load_step_detected"]:
            raise RuntimeError("configured load step did not appear in motulator result")
        return make_envelope(domain="electric_motor_drive", topic="motor_foc",
            execution_type="numerical_simulation",
            inputs=[{"id": "motor_controller_parameters", "value": payload["parameters"]}],
            operations=[{"id": "pmsm_foc_simulation", "engine": "motulator", "version": importlib.metadata.version("motulator"),
                         "machine": "SynchronousMachine", "control": "CurrentVectorController + speed PI"}],
            outputs=[{"id": "phase_currents", "unit": "A_peak", "value": {k: signals[k]["values"] for k in ("phase_current_a", "phase_current_b", "phase_current_c")}},
                     {"id": "dq_current", "unit": "A_peak", "value": {"d": signals["current_d"]["values"], "q": signals["current_q"]["values"]}},
                     {"id": "torque", "unit": "N·m", "value": signals["torque"]["values"]},
                     {"id": "speed", "unit": "rad/s", "value": signals["speed_rad_s"]["values"]}],
            payload=payload, timestamps=mt.tolist(),
            provenance={"engine": "motulator", "engine_version": importlib.metadata.version("motulator"),
                        "model": "motulator 0.9 PMSM + FOC average-inverter example parameters"},
            limitations=["Demonstration PMSM parameters; not a user's specific motor or hardware measurement.",
                         "Averaged converter model: no high-frequency PWM switch waveform or semiconductor switching loss.",
                         "BLDC six-step commutation is a separate, unimplemented topic."])

    def validate(self, trace):
        errors = validate_envelope(trace)
        if trace.get("topic") != "motor_foc" or trace.get("domain") != "electric_motor_drive":
            errors.append("motor trace domain/topic mismatch")
        p = trace.get("payload", {})
        errors.extend(validate_time_series(p))
        try:
            params, signals = p["parameters"], p["signals"]
            if any(params[name] <= 0 for name in ("stator_resistance_ohm", "inductance_d_h", "inductance_q_h", "pm_flux_wb", "inertia_kg_m2", "dc_bus_v")):
                errors.append("PMSM parameters must be positive")
            if p["control"]["inverter_model"].startswith("averaged") is False:
                errors.append("motor inverter model description is missing")
            if not p["validation"]["solver_success"] or not p["validation"]["finite_currents"]:
                errors.append("motulator solver or finite-current validation failed")
            control_time = np.asarray(signals["speed_reference"]["timestamps"],dtype=float)
            for name in ("current_d_reference","current_q_reference","current_d_feedback","current_q_feedback",
                         "torque_reference","speed_reference"):
                if signals[name]["timestamps"] != signals["speed_reference"]["timestamps"]:
                    errors.append(f"{name} does not use the controller sample clock")
                if len(signals[name]["values"]) != len(control_time):
                    errors.append(f"{name} sample count does not match controller clock")
            t = np.asarray(signals["torque"]["values"], dtype=float)
            speed = np.asarray(signals["speed_rad_s"]["values"], dtype=float)
            load_t = np.asarray(signals["load_torque"]["values"], dtype=float)
            if not np.isfinite(t).all() or not np.isfinite(speed).all() or not np.isfinite(load_t).all():
                errors.append("motor mechanical trace contains non-finite values")
            if not np.any(load_t > 0):
                errors.append("motor load step is absent from the recorded state")
            expected_rpm = speed*60/(2*math.pi)
            if not np.allclose(expected_rpm, signals["speed_rpm"]["values"], rtol=1e-10, atol=1e-10):
                errors.append("rad/s to rpm conversion mismatch")
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(f"motor trace payload invalid: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        return {"kind": "engineering", "domain": trace["domain"], "topic": trace["topic"],
                "title": "PMSM FOC: 3상 전류에서 dq 전류와 부하 응답까지",
                "trace_id": trace["trace_id"], "timestamps": p["timestamps"],
                "signals": p["signals"], "units": {k: v["unit"] for k, v in p["signals"].items()},
                "parameters": p["parameters"], "control": p["control"],
                "visualization": "multichannel_waveforms", "source_time_unit": "s",
                "display_stride": max(1, len(p["timestamps"])//1200)}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
