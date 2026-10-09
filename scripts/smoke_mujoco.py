#!/usr/bin/env python3
"""Load an MJCF model and run a deterministic headless MuJoCo smoke simulation."""
from __future__ import annotations

import argparse
from pathlib import Path

import mujoco
import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="MJCF XML file")
    parser.add_argument("--steps", type=int, default=1000)
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("--steps must be positive")
    model_path = args.model.resolve()
    if not model_path.is_file():
        parser.error(f"MJCF file does not exist: {model_path}")

    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    for _ in range(args.steps):
        mujoco.mj_step(model, data)
    if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
        raise RuntimeError("simulation produced non-finite joint state")

    print(f"MuJoCo {mujoco.__version__}: PASS")
    print(f"model={model_path}")
    print(f"bodies={model.nbody} joints={model.njnt} actuators={model.nu}")
    print(f"timestep={model.opt.timestep:g}s steps={args.steps} simulated={data.time:.6f}s")
    print(f"contacts={data.ncon} qpos_finite=true qvel_finite=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
