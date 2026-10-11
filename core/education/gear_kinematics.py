"""Ideal pitch-point kinematics for an external spur-gear pair."""
from __future__ import annotations

import math


def external_spur_gear_kinematics(
    pinion_teeth: int,
    gear_teeth: int,
    module_m: float,
    omega_pinion_rad_s: float,
) -> dict:
    """Return pitch geometry and ideal no-slip velocities in a 2D frame.

    The pinion center is the origin, the driven gear center is on +x, and the
    common pitch point lies between them. Velocities are ``omega x radius``;
    no tooth-contact force, tooth profile, or friction model is implied.
    """
    if isinstance(pinion_teeth, bool) or not isinstance(pinion_teeth, int) or pinion_teeth <= 0:
        raise ValueError("pinion_teeth must be a positive integer")
    if isinstance(gear_teeth, bool) or not isinstance(gear_teeth, int) or gear_teeth <= 0:
        raise ValueError("gear_teeth must be a positive integer")
    if not math.isfinite(module_m) or module_m <= 0:
        raise ValueError("module_m must be finite and positive")
    if not math.isfinite(omega_pinion_rad_s):
        raise ValueError("omega_pinion_rad_s must be finite")

    r1 = module_m * pinion_teeth / 2
    r2 = module_m * gear_teeth / 2
    center_distance = r1 + r2
    pitch_point = (r1, 0.0)
    omega_gear = -omega_pinion_rad_s * pinion_teeth / gear_teeth
    # In 2D, omega*k cross (x, y) is (-omega*y, omega*x).
    v1 = (-omega_pinion_rad_s * 0.0, omega_pinion_rad_s * r1)
    v2 = (-omega_gear * 0.0, omega_gear * -r2)
    return {
        "pinion_pitch_radius_m": r1,
        "gear_pitch_radius_m": r2,
        "center_distance_m": center_distance,
        "pinion_center_m": (0.0, 0.0),
        "gear_center_m": (center_distance, 0.0),
        "pitch_point_m": pitch_point,
        "pinion_angular_velocity_rad_s": omega_pinion_rad_s,
        "gear_angular_velocity_rad_s": omega_gear,
        "pinion_pitch_velocity_m_s": v1,
        "gear_pitch_velocity_m_s": v2,
    }


def vertical_velocity_direction(velocity: tuple[float, float], *, tolerance: float = 1e-12) -> int:
    """Return -1/0/+1 for vertical motion; zero means draw no direction arrow."""
    if len(velocity) != 2 or not all(math.isfinite(value) for value in velocity):
        raise ValueError("velocity must contain two finite components")
    if abs(velocity[1]) <= tolerance:
        return 0
    return 1 if velocity[1] > 0 else -1
