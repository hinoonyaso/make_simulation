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
            pwm = max(-1.0, min(1.0, raw_pwm))
            if -1.0 < raw_pwm < 1.0 or error * raw_pwm < 0:
                integral += error * dt
            samples.append({"time_s": time_s, "target_rad_s": target, "motor_speed_rad_s": speed,
                            "encoder_speed_rad_s": measured, "error_rad_s": error,
                            "pwm_duty": pwm, "encoder_count": count})
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
        payload = trace.get("payload", {})
        samples = payload.get("samples", [])
        if not samples:
            errors.append("PID trace must contain samples")
            return errors
        if any(not all(math.isfinite(float(row.get(field, float("nan")))) for field in
                       ("time_s", "target_rad_s", "motor_speed_rad_s", "encoder_speed_rad_s", "pwm_duty"))
               for row in samples):
            errors.append("PID samples contain non-finite values")
        elif any(b["time_s"] <= a["time_s"] for a, b in zip(samples, samples[1:])):
            errors.append("PID sample timestamps must increase")
        if any(abs(row.get("pwm_duty", 0)) > 1 for row in samples):
            errors.append("PID PWM duty exceeds configured saturation")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        return {"kind": "mcu_pid", "samples": p["samples"], "target_rad_s": p["target_rad_s"],
                "pwm_range": p["pwm_range"], "duration_s": p["duration_s"]}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
