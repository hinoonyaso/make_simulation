# V10 MuJoCo H1 arm PoC

A real MuJoCo physics run drives the Unitree H1 left shoulder and elbow, records the resulting full joint state and hand pose, validates an FK replay, then renders the same trace with Manim. The Manim skeleton is a stylized side-on trace projection; the H1 mesh is not rendered. The output is a video-only technical PoC, not a finished narrated episode.

## Reproduce

From repository root:

```bash
uv sync
uv run python scripts/run_mujoco_arm_poc.py
uv run python core/shared-data/validate_trace.py pilots/v10_mujoco_arm/data/trace.json
uv run python scripts/validate_mujoco_sensitivity.py
uv run python scripts/check_scene_style.py pilots/v10_mujoco_arm/arm_trace_scene.py
uv run python pilots/v10_mujoco_arm/build_video.py final
uv run python scripts/validate_delivery.py pilots/v10_mujoco_arm/output/mujoco_h1_arm.mp4 --fps 30 --full-decode
```

## Simulation evidence and boundaries

The run uses the repository's `blender.unitree_h1.v1` asset (`h1_with_hand.xml`, upstream revision recorded in the trace, BSD-3-Clause). The runner parses an in-memory copy of the MJCF, removes only the pelvis freejoint to make a fixed-base arm experiment, sets a 2 ms physics step, retains source inertias/collision geometry and gravity, and does not change the checked-in MJCF. MuJoCo motor commands use a closed-loop PD law at each physics step. Left shoulder pitch and elbow follow a smooth target; other actuated joints hold zero. The model's own collision solver reports 3–4 self contacts during the run; there is no added floor and contact is not the teaching claim.

`data/trace.json` stores the V9-compatible `robotics-visual-trace/v1` samples: timestamps, full qpos/qvel, motor commands, targets, shoulder/elbow/hand positions, hand quaternion and contact count. Model provenance, solver settings, control assumptions and units are included. The trace validator passes. A second `MjData` performs forward kinematics from every recorded qpos; maximum hand-position difference is 0 m at stored precision. A repeat run produces matching recorded joint and hand positions to 1e-12 absolute tolerance.

`data/numerical_validation.json` compares the same run at 2 ms and 1 ms timesteps over 2 seconds, sampling every 20 ms. Maximum paired hand-position deviation is 0.000106713 m against a 0.001 m tolerance. This is a timestep sensitivity result, not a claim that the controller tracks its target exactly. The maximum measured target errors are 0.120 rad (shoulder) and 0.209 rad (elbow), so the plotted target and actual motion remain visibly distinct. Maximum joint-limit excursion is 9.2e-9 rad, below the 1e-6 rad numeric tolerance.

## Render and environment limits

`output/mujoco_h1_arm.mp4` is 9.8 seconds, 1080p30, H.264, full-decode verified. It has no narration/audio. The visual scene is driven only by this recorded trace. Blender CLI, SoX and a local browser are absent in this WSL execution environment; `sudo` cannot install system packages because the container has `no new privileges`. Manim's video-only render succeeds despite its optional SoX warning. No Three.js/Remotion PoC is included: Manim already renders these 2D trace relationships, and there is no browser capture runtime for a fair standalone video comparison.
