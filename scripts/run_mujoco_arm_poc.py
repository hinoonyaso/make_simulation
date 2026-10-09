#!/usr/bin/env python3
"""Run the local fixed-base Unitree H1 arm physics PoC and save a V9 trace."""
from pathlib import Path
import argparse
import importlib.util
import sys

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
    parser.add_argument("--output", type=Path,
                        default=ROOT / "pilots/v10_mujoco_arm/data")
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--timestep", type=float, default=0.002)
    parser.add_argument("--sample-period", type=float, default=0.02)
    args = parser.parse_args()
    trace = adapter.run_arm_experiment(args.model, args.output, args.duration,
                                        args.timestep, args.sample_period)
    print(f"PASS: {trace['schema']} · {len(trace['samples'])} samples · "
          f"FK max error {trace['validation']['fk_max_position_error_m']:.3g} m · "
          f"hand travel {trace['validation']['end_effector_travel_m']:.4f} m")
    print(args.output / "trace.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
