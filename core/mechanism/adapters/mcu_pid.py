"""Discrete sampled PID plus a first-order motor and quantized encoder model."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope


class MCUPIDAdapter:
    def __init__(self, capability: dict[str, Any] | None = None): self.capability = capability or {}
    def describe_capability(self): return self.capability
    def prepare(self, request: MechanismRequest): return {"topic": request.topic, **request.options}

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        dt = float(config.get("dt", .02)); duration = float(config.get("duration", 4.0))
        target = float(config.get("target_rad_s", 12.0)); max_speed = float(config.get("max_speed_rad_s", 20.0))
        tau = float(config.get("motor_time_constant_s", .35)); ticks = int(config.get("encoder_ticks_per_rev", 2048))
        kp, ki, kd = (float(config.get(k, default)) for k, default in (("kp", .08), ("ki", .2), ("kd", .001)))
        if not all(math.isfinite(x) for x in (dt, duration, target, max_speed, tau, kp, ki, kd)):
            raise ValueError("PID parameters must be finite")
        if dt <= 0 or duration <= 0 or max_speed <= 0 or tau <= 0 or ticks < 1:
            raise ValueError("dt, duration, max speed, motor time constant and encoder ticks must be positive")
        steps_float = duration / dt
        steps = round(steps_float)
        if not math.isclose(steps_float, steps, abs_tol=1e-9) or steps > 10000:
            raise ValueError("duration must be divisible by dt and produce at most 10000 steps")
        samples = []
        speed = integral = previous_error = position = 0.0
        previous_count = 0
        for index in range(steps + 1):
            time_s = index * dt
            count = round(position / (2 * math.pi) * ticks)
            measured = ((count - previous_count) * (2 * math.pi / ticks) / dt) if index else 0.0
            error = target - measured
            derivative = (error - previous_error) / dt if index else 0.0
            raw_pwm = kp * error + ki * integral + kd * derivative
            integral_state = integral
            pwm = max(-1.0, min(1.0, raw_pwm))
            if -1.0 < raw_pwm < 1.0 or error * raw_pwm < 0:
                integral += error * dt
            samples.append({"time_s": time_s, "target_rad_s": target, "motor_speed_rad_s": speed,
                            "encoder_speed_rad_s": measured, "error_rad_s": error,
                            "derivative_rad_s2": derivative, "integral_state": integral_state,
                            "raw_pwm": raw_pwm, "pwm_duty": pwm, "encoder_count": count})
            if index < steps:
                speed += dt * ((pwm * max_speed - speed) / tau)
                position += speed * dt
            previous_count, previous_error = count, error
        payload = {"sample_period_s": dt, "duration_s": duration, "target_rad_s": target,
                   "max_speed_rad_s": max_speed, "motor_time_constant_s": tau,
                   "encoder_ticks_per_rev": ticks, "pid": {"kp": kp, "ki": ki, "kd": kd},
                   "pwm_range": [-1.0, 1.0], "samples": samples,
                   "final_speed_rad_s": samples[-1]["motor_speed_rad_s"],
                   "final_encoder_speed_rad_s": samples[-1]["encoder_speed_rad_s"],
                   "hardware_firmware_executed": False}
        trace = make_envelope(domain="mcu_embedded", topic="mcu_pid", execution_type="numerical_simulation",
            inputs=[{"id": "speed_reference", "value": target, "unit": "rad/s"}],
            operations=[{"id": "sampled_pid", "dt_s": dt, "gains": payload["pid"]},
                        {"id": "motor_plant", "type": "first_order", "time_constant_s": tau},
                        {"id": "encoder", "ticks_per_revolution": ticks}],
            outputs=[{"id": "motor_response", "final_speed_rad_s": payload["final_speed_rad_s"]}],
            payload=payload, provenance={"backend": "deterministic discrete-time numerical simulation", "hardware": None},
            hardware=None, timestamps=[row["time_s"] for row in samples],
            limitations=["No STM32/ESP32 firmware, peripheral simulator, or physical motor board was executed."])
        return trace

    def validate(self, trace):
        errors = validate_envelope(trace)
        if trace.get("topic") != "mcu_pid" or trace.get("domain") != "mcu_embedded":
            errors.append("PID trace domain/topic mismatch")
        payload = trace.get("payload", {})
        samples = payload.get("samples", [])
        if not samples:
            errors.append("PID trace must contain samples")
            return errors
        if any(not all(math.isfinite(float(row.get(field, float("nan")))) for field in
                       ("time_s", "target_rad_s", "motor_speed_rad_s", "encoder_speed_rad_s", "pwm_duty"))
               for row in samples):
            errors.append("PID samples contain non-finite values")
        else:
            dt = float(payload.get("sample_period_s", float("nan")))
            if not math.isfinite(dt) or dt <= 0:
                errors.append("PID sample period must be finite and positive")
            elif any(not math.isclose(row["time_s"], i * dt, rel_tol=0, abs_tol=1e-10)
                     for i, row in enumerate(samples)):
                errors.append("PID sample timestamps do not match the configured sample period")
        if any(abs(row.get("pwm_duty", 0)) > 1 for row in samples):
            errors.append("PID PWM duty exceeds configured saturation")
        try:
            dt = float(payload["sample_period_s"]); tau = float(payload["motor_time_constant_s"])
            max_speed = float(payload["max_speed_rad_s"]); ticks = int(payload["encoder_ticks_per_rev"])
            target = float(payload["target_rad_s"]); gains = payload["pid"]
            kp, ki, kd = (float(gains[name]) for name in ("kp", "ki", "kd"))
            if tau <= 0 or ticks <= 0:
                raise ValueError("motor time constant and encoder resolution must be positive")
            steps = float(payload["duration_s"]) / dt
            if not math.isclose(steps, round(steps), abs_tol=1e-9) or len(samples) != round(steps) + 1:
                errors.append("PID sample count does not match duration and sample period")
            integral = 0.0; previous_error = 0.0
            if samples and (samples[0]["encoder_count"] != 0 or samples[0]["encoder_speed_rad_s"] != 0):
                errors.append("PID initial encoder state must be zero")
            for index, row in enumerate(samples):
                expected_error = target - row["encoder_speed_rad_s"]
                expected_derivative = (expected_error - previous_error) / dt if index else 0.0
                expected_raw = kp * expected_error + ki * integral + kd * expected_derivative
                for key, actual, expected in (("error", row.get("error_rad_s"), expected_error),
                        ("derivative", row.get("derivative_rad_s2"), expected_derivative),
                        ("integral state", row.get("integral_state"), integral),
                        ("raw PWM", row.get("raw_pwm"), expected_raw),
                        ("saturated PWM", row.get("pwm_duty"), max(-1., min(1., expected_raw)))):
                    if actual is None or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9):
                        errors.append(f"PID {key} equation mismatch at sample {index}")
                        break
                if -1.0 < expected_raw < 1.0 or expected_error * expected_raw < 0:
                    integral += expected_error * dt
                previous_error = expected_error
            for index, (row, nxt) in enumerate(zip(samples, samples[1:])):
                predicted = row["motor_speed_rad_s"] + dt * ((row["pwm_duty"] * max_speed - row["motor_speed_rad_s"]) / tau)
                if not math.isclose(predicted, nxt["motor_speed_rad_s"], rel_tol=1e-9, abs_tol=1e-9):
                    errors.append(f"PID motor plant transition mismatch after sample {index}")
                    break
                measured = ((nxt["encoder_count"] - row["encoder_count"]) * (2 * math.pi / ticks) / dt)
                if not math.isclose(measured, nxt["encoder_speed_rad_s"], rel_tol=1e-9, abs_tol=1e-9):
                    errors.append(f"PID encoder speed/count mismatch at sample {index + 1}")
                    break
            if samples and (not math.isclose(samples[-1]["motor_speed_rad_s"], payload["final_speed_rad_s"], abs_tol=1e-10) or
                            not math.isclose(samples[-1]["encoder_speed_rad_s"], payload["final_encoder_speed_rad_s"], abs_tol=1e-10)):
                errors.append("PID final speed summary does not match the last sample")
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            errors.append(f"invalid PID simulation payload: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        return {"kind": "mcu_pid", "samples": p["samples"], "target_rad_s": p["target_rad_s"],
                "pwm_range": p["pwm_range"], "duration_s": p["duration_s"]}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
