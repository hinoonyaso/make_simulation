# Environment validation record

Date: 2026-10-09 (local machine check)

| Environment | Download | Dependency closure | Simulator load | Physics/action | Trace | Render | Result |
|---|---|---|---|---|---|---|---|
| Clearpath office | NOT_RUN | BLOCKED: `ros2` and `gz` executables absent | BLOCKED | NOT_RUN | NOT_RUN | NOT_RUN | Not READY |
| ManiSkill PickCube-v1 | NOT_RUN | BLOCKED: `sapien` import absent; no GPU access | BLOCKED | NOT_RUN | NOT_RUN | BLOCKED: project documents no WSL rendering support | Not READY |
| robosuite Lift | NOT_RUN | BLOCKED: `robosuite` import absent; package index DNS failed | BLOCKED | NOT_RUN | NOT_RUN | NOT_RUN | Not READY |

MuJoCo 3.7.0 is installed. `nvidia-smi` reports GPU access blocked by the OS. `uv run --with robosuite==1.5.2 ...` failed before installation because this runtime could not resolve `pypi.org`; the project dependency files were not changed. No environment or external model was downloaded. Therefore none of the requested two-environment load/render acceptance checks passed.

Required next run: use a network-enabled ROS 2 Jazzy + Gazebo Harmonic host for Clearpath and a Linux/SAPIEN-capable render host for ManiSkill (or an online package/network-enabled host for robosuite); pin exact commits and archive hashes; resolve all model/texture URIs and licenses; then capture world load, collision, robot spawn/action, state trace, and preview evidence. Do not infer these results from this record.
