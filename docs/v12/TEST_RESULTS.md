# V12 test and render evidence

## V12.1 accuracy hardening — local evidence (2026-10-10)

Base commit: `2af957f442d8919946cabd32e30152113bc47a20` (`origin/main` at task start). The pre-change full suite passed **129 tests**. Current local full suite passes **136 tests** (7 added tests), including non-divisible Physics duration, final timestamp/sample/analytic/energy checks, invalid timestamp input boundaries, CAN bit-slot and ACK checks, rehashed trace/cache evidence mutations, a CRC-15/CAN catalogue check value, and timeline/frame interpolation and FPS invariants.

Three real silent preview MP4s were rendered at 960×540, 30 fps and fully decoded. The Physics render uses the new non-divisible configuration and carries 12 source samples ending at exactly 1.05 s. Physics and FOC also recorded per-frame renderer state; `validate_mechanism_render.py --engineering-frames` verified the observed frame samples against the shared timeline and trace. Extracted actual frames were inspected for Physics energy-legend legibility, CAN winner/ACK result, and FOC unit-separated load response. This is sampled-frame review, not a full normal-speed playback review.

| Topic | Run directory (under `pilots/v12_engineering/output/v12_1_renders/runs/`) | Duration | Frames | Trace SHA-256 | Timeline SHA-256 |
|---|---|---:|---:|---|---|
| Physics oscillator | `physics_oscillator-a086ab551dc69fe01680-rerun-20261010T065227-081678968` | 26.466341 s | 794 | `e79c726079b76eeaa5a5dda31cce884bf5466f96e60fda36d1ad1e60f857b43f` | `18665ef5202d335459423fddc24e2e70444229884d899887768f695863f628b5` |
| CAN arbitration | `can_arbitration-16222e56fa1caefbc129-rerun-20261010T065518-584951824` | 22.066667 s | 662 | `69801c5ef090214ebb225942c61429b11569ecd946c790eb63d12c8f6232f935` | `fbc172a706ccae0d2e9264e37d04de829493b1c076e52d3b17811c0a19a0602d` |
| PMSM FOC | `motor_foc-cf03e2cfe35bb86fe73f-rerun-20261010T065251-660550066` | 23.400000 s | 702 | `f1e35d4f41f9706077705d41545101a43b3d079c9b9235bc36fd19cd9f50fd5e` | `9525d695709fa8e580da482c83f483a1b249dd93fa0aea9dd1e67176ac487be3` |

The Physics and FOC frame-sample mapping checks and all three full-decode checks passed. Sampled arbitration-phase frames show the red loss marker at the recomputed loss bit and green winner marker at the arbitration boundary. The Physics and FOC traces reused validated execution-cache entries; their visual renders were cache misses after the renderer update.

On commit `13137046d3c2afaf4f8b78f687d1148802c3c199` (PR [#2](https://github.com/hinoonyaso/make_simulation/pull/2)), Engineering simulation [run 38033169279](https://github.com/hinoonyaso/make_simulation/actions/runs/38033169279) completed successfully with all five jobs, including three 540p30 render/full-decode previews; artifact `v12-engineering-preview-renders` was uploaded. AI trace reproducibility [run 38033169339](https://github.com/hinoonyaso/make_simulation/actions/runs/38033169339) completed successfully, including the full CPU regression suite. This CI pass validates the V12.1 code and tests. The documentation-only follow-up commit records these results.

Observed on 2026-10-10 (Asia/Seoul), repository starting HEAD `7b8a926`.

## Local validation

- Baseline before V12 implementation: 120 existing unit tests passed.
- Final `uv run --offline python -m unittest discover -s tests -v`: **129 passed**.
- Isolated lock-derived CI environment: Python 3.12.3; 52 packages selected for `sim-math sim-can sim-motor sim-render`; all 9 V12 tests passed in that fresh environment.
- Fresh environment imports SymPy, SciPy, python-control, python-can, cantools, motulator and Manim. The tested motulator PMSM drive imports without importing PyTorch.
- `scripts/setup_v12_ubuntu.sh --check`: exit 0. Doctor reports three engineering groups, Manim and FFmpeg READY. Blender is installed; its normal WSL child-process probe is blocked, while the approved host-execution `--version` probe returned Blender 5.2.1 LTS. Prior H1 mesh render evidence is linked from the environment report. PyBaMM and Renode are optional missing; SocketCAN/vcan is blocked by WSL netlink permissions.
- Three executable runs each produced a validated trace and a silent **1920×1080 H.264, 30 fps** MP4. All ran through `validate_delivery.py --full-decode` in the production pipeline.
- Three separate `--mode replay` runs accepted each saved trace and produced 960×540, 30 fps previews; full decode passed.
- Trace cache test verifies identical inputs hit and a modified cached trace is rejected. Existing V11.5 regression tests remained green.
- `git diff --check`: PASS.

## Final media artifacts

All paths are relative to repository root and are under `pilots/v12_engineering/output/final_verified/`.

| Topic | Run ID | Duration | Frames | Trace SHA-256 | Timeline SHA-256 |
|---|---|---:|---:|---|---|
| Physics oscillator | `physics_oscillator-e0e15f9c18e342b0ab74` | 26.466667 s | 794 | `a40a8e0914502ff7fb9c83f5fc6155e8fdbf98cbd2924ca37f34876a6aea2900` | `5cd8f37e94d0d1f606924a9f8b30cec094cf6415d54e31a4fd1e2f737386fc90` |
| CAN arbitration | `can_arbitration-3e42f84bf52609680ace` | 22.066667 s | 662 | `9291e2d769f90bb7e02271f9883673e9c78b37296ca7ce87c6c49b14d056b6ac` | `fbc172a706ccae0d2e9264e37d04de829493b1c076e52d3b17811c0a19a0602d` |
| PMSM FOC | `motor_foc-fbe66a56f325b181aad0` | 23.4 s | 702 | `f1e35d4f41f9706077705d41545101a43b3d079c9b9235bc36fd19cd9f50fd5e` | `9525d695709fa8e580da482c83f483a1b249dd93fa0aea9dd1e67176ac487be3` |

Each run directory contains the source `trace.json`, `timeline.json`, rendered `final.mp4`, and `production_report.json`. Video SHA-256 values are recorded in each report. Physics validation reports a maximum analytic/numeric position error of `2.78e-10 m` and an energy balance residual of `4.51e-9 J`; CAN arbitration selects `ECU_A`, ACK is observed, and the generated frame contains 87 bits at 1 Mbit/s; FOC solver validation detects the load step, with final speed `100.000001 rad/s`, peak torque `1.9915 Nm`, and peak phase current `5.532 A`. Videos intentionally have no audio or narration: V12's requested scope is engineering simulation visualization, and existing narration/TTS behavior was not modified.

## Remote CI

The first PR-triggered run on 2026-10-10 executed Engineering simulation [38030323845](https://github.com/hinoonyaso/make_simulation/actions/runs/38030323845) and AI trace reproducibility [38030323831](https://github.com/hinoonyaso/make_simulation/actions/runs/38030323831). The isolated math, CAN, FOC and V12 trace/timeline jobs passed. Render smoke initially failed while building `manimpango` because the runner lacked `pangocairo`; the full AI regression job initially failed because it collected V12 tests without installing the `sim-math`, `sim-can`, and `sim-motor` groups. The fixes add Pango/Cairo build dependencies and install the lock-derived V12 groups for the full regression suite.

On the corrected code commit, Engineering simulation [38030508028](https://github.com/hinoonyaso/make_simulation/actions/runs/38030508028) passed all five jobs, including all three 540p30 preview renders, full decode and upload of artifact `v12-engineering-preview-renders`. AI trace reproducibility [38030507975](https://github.com/hinoonyaso/make_simulation/actions/runs/38030507975) passed all steps, including 129 CPU regression tests, trace/manifest checks, capability checks, Python compilation and the Three.js projection build. These were actual PR-triggered GitHub Actions runs.
