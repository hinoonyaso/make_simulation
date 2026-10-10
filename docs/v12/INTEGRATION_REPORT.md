# V12 integration report

This report records local execution on Ubuntu 24.04.4 LTS / WSL2 / x86_64, Python 3.12.3, uv 0.12.3, Manim Community 0.21.0, and FFmpeg 6.1.1. The machine environment snapshot is [observed_environment.json](observed_environment.json). Full test, trace, timeline, media and replay evidence is in [TEST_RESULTS.md](TEST_RESULTS.md).

## Integrated and checked

- Three lazy-loaded adapters are registered in the existing mechanism catalog and use the V11.5 envelope, execution cache, shared timeline, renderer selection, production report and Manim path.
- Physics uses a mass-spring-damper model, SymPy equation/closed-form checks where applicable, SciPy DOP853 integration, and python-control state-space representation. Undamped, underdamped, critical and overdamped responses plus a forced case are recomputed and domain-validated.
- CAN uses a deterministic Classical CAN 2.0A standard-frame bit/event model with arbitration, stuffing, CRC-15/CAN, ACK and integer ticks. DBC encoding/decoding and python-can VirtualBus are separate integration checks; neither is represented as physical CAN_H/CAN_L behavior.
- Motor FOC uses motulator 0.9's PMSM, sensored machine state, current-vector and speed controllers, an averaged converter, and a load step. Adaptive solver and controller clocks are retained independently. This is a documented demo motor configuration, not a user's measured motor.
- Each topic has a validated source trace, trace-backed storyboard and timeline, 1080p30 final MP4, full decode result, plus a separately replayed 540p30 trace render.
- Review of rendered frames found stale VGroup state across phases in the shared Manim scene. Engineering beats now replace their complete screen state. This behavior is scoped to V12 `engineering` plans; existing topic transition behavior is retained. Reviewed physics, CAN and FOC frames show one active phase at a time.
- CI's `uv export` approach was found to include the project's default AI/media dependency set. It was replaced with `scripts/export_v12_requirements.py`, which follows only selected root groups in `uv.lock`, evaluates platform markers, pins package versions and artifact hashes, and supports `pip --no-deps --require-hashes`. A fresh temporary environment installed the 52-package render closure and passed all 9 V12 tests. The tested motulator execution path does not import torch, so its unused optional torch edge is excluded explicitly.

## Environment boundaries

- The installed Python groups `sim-math`, `sim-can`, and `sim-motor` are READY. The exact versions are in the JSON snapshot.
- `python3-tk`, `python3-venv`, and `can-utils` are absent in this managed WSL environment. The setup check reports these prerequisites; administrator-only installation was not attempted.
- SocketCAN vcan inspection is blocked by `Operation not permitted` on netlink. No host networking or kernel state was changed. Python VirtualBus tests pass without vcan.
- Windows Blender 5.2.1 is installed. Ordinary WSL child-process launch is blocked in this process, but a read-only host-execution probe succeeded and the V11.2 report records an actual Blender mesh render. This does not imply V12 used Blender; the three V12 paths use Manim.
- SoX is absent and Manim prints a warning; silent MP4 output uses FFmpeg and validates successfully.
- PyBaMM and Renode remain optional and were not installed or runtime-tested.
- GitHub Actions was not remotely dispatched or observed; remote CI is NOT_RUN.

No base PyTorch/MuJoCo/Manim dependencies were upgraded by the V12 group setup. No existing `topics/` media, narration, robot assets, meshes, checkpoints or maps were intentionally modified. No GitHub push was performed.
