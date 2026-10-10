# V12 test and render evidence

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

The GitHub Actions API was inspected on 2026-10-10. The latest `main` run was AI trace workflow run [38024214790](https://github.com/hinoonyaso/make_simulation/actions/runs/38024214790), successful at starting HEAD `7b8a926`; this does not test V12. `.github/workflows/engineering-sim.yml` exists only in the local worktree and has not been published, so a V12 Actions run is still **NOT_RUN**. Once the V12 workflow is on a PR or `main`, it installs the selected group closure from `uv.lock` using hashes and renders three 540p30 previews.
