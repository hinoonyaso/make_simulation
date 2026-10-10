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
- The first PR-triggered remote run (Engineering simulation `38030323845`, AI trace `38030323831`) exposed two CI environment gaps: Manim's `manimpango` build could not find `pangocairo`, and the existing full regression workflow did not install the new V12 execution groups. The focused engineering math, CAN, FOC and trace/timeline jobs passed. Workflow fixes add the Ubuntu Pango/Cairo build packages and install only the hash-locked V12 execution groups in the full regression job. The subsequent full regression and preview-render runs passed; details are recorded in [TEST_RESULTS.md](TEST_RESULTS.md).

## V12.1 accuracy hardening status

The V12.1 review is recorded in [TEST_RESULTS.md](TEST_RESULTS.md). Physics now builds its terminal source clock before sizing solver arrays; engineering charts use separate rows for different physical units and one shared source-time axis; frame cursors sample the trace through the unified timeline; CAN validation recomputes all protocol-critical evidence and event ticks. Local validation passed 136 tests, Python compilation, diff checks and full decode for all three preview MP4s. Selected actual frames were inspected. On commit `13137046d3c2afaf4f8b78f687d1148802c3c199`, the Engineering simulation workflow passed all five jobs and the AI trace reproducibility workflow passed; links and artifact details are in [TEST_RESULTS.md](TEST_RESULTS.md).

### V12.1 final plot and CAN presentation fix

The final accuracy follow-up gives signals in one plotted comparison group a shared scale per physical unit, preserves both sides of ZOH transitions and labels over-budget plots `OVERVIEW`, and derives the displayed CAN arbitration end boundary from the engine's stuffed physical-wire event tick. Local full-suite validation passes 139 tests. Physics, CAN and PMSM FOC previews pass full decode; Physics/FOC timeline-to-rendered-sample checks pass; extracted before/after frames were visually inspected. Saved traces compare equal to their pre-fix traces. This follow-up is local and unpushed: the final-patch GitHub Actions state is **NOT_RUN** pending explicit permission to push. Full evidence is in [TEST_RESULTS.md](TEST_RESULTS.md); next hardware-model candidates and licensing constraints are in [ASSET_ACQUISITION_PLAN.md](ASSET_ACQUISITION_PLAN.md).

No base PyTorch/MuJoCo/Manim dependencies were upgraded by the V12 group setup. No existing `topics/` media, narration, robot assets, meshes, checkpoints or maps were intentionally modified.
