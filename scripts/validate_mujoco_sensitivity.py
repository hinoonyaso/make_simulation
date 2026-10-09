#!/usr/bin/env python3
"""Compare matched H1 arm runs at base and half integration timestep."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mujoco_adapter", ROOT / "core/robotics-simulation/mujoco_adapter.py")
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load MuJoCo adapter")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path,
                        default=ROOT / "assets/unitree_h1/mjcf/h1_with_hand.xml")
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--timestep", type=float, default=.002)
    parser.add_argument("--sample-period", type=float, default=.02)
    parser.add_argument("--tolerance-m", type=float, default=.001)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "pilots/v10_mujoco_arm/data/numerical_validation.json")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="mujoco-sensitivity-") as temp:
        base = adapter.run_arm_experiment(args.model, Path(temp) / "base", args.duration,
                                           args.timestep, args.sample_period)
        refined = adapter.run_arm_experiment(args.model, Path(temp) / "half_step", args.duration,
                                              args.timestep / 2, args.sample_period)
    base_samples, refined_samples = base["samples"], refined["samples"]
    if len(base_samples) != len(refined_samples):
        raise RuntimeError("matched runs produced different sample counts")
    if any(abs(a["t"] - b["t"]) > 1e-9 for a, b in zip(base_samples, refined_samples)):
        raise RuntimeError("matched runs produced different sample timestamps")
    errors = [float(np.linalg.norm(np.asarray(a["ee_pos"]) - np.asarray(b["ee_pos"])))
              for a, b in zip(base_samples, refined_samples)]
    result = {
        "model": "unitree_h1_with_hand",
        "source_sha256": base["model"]["source_sha256"],
        "duration_s": args.duration,
        "base_timestep_s": args.timestep,
        "refined_timestep_s": args.timestep / 2,
        "sample_period_s": args.sample_period,
        "sample_count": len(errors),
        "max_paired_end_effector_deviation_m": max(errors),
        "final_end_effector_deviation_m": errors[-1],
        "tolerance_m": args.tolerance_m,
        "status": "PASS" if max(errors) <= args.tolerance_m else "FAIL",
        "contact_is_lesson_evidence": False,
        "note": "Same fixed-base model and PD target schedule; this is a timestep sensitivity check, not a controller accuracy claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{result['status']}: max paired EE deviation "
          f"{result['max_paired_end_effector_deviation_m']:.9f} m "
          f"(tolerance {args.tolerance_m:g} m)")
    print(args.output)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
