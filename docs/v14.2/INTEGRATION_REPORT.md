# V14.2 Integration Report

## Implemented

- Optional locked `sim-battery` dependency group for PyBaMM 26.10.0.0.
- Allow-listed SPM/Chen2020 CPU adapter, config/result JSON Schemas, execution provenance and result validator.
- Separate solver CLI and renderer `--solver-result` input; plan-only does not execute the solver.
- V9 `battery-simulation-trace/v1` dispatch with result/config/CSV integrity checks.
- Battery topic registration, existing CC0 18650 concept asset contract, Blender scene and Manim voltage trace.
- 24-second/720-frame mixed lesson spec and a 6-second Manim-only integration smoke spec.
- Battery-specific CI workflow that installs PyBaMM and Manim, runs the actual solver, validates outputs, renders from solver output and fully decodes the media.
- Korean scene frame review found and fixed overlap between the voltage-axis label and y ticks.

## Local verification

- Actual PyBaMM execution and result validation: PASS.
- Manim actual-data smoke: PASS, 6 seconds / 180 frames / 960×540 / 30 fps / H.264 / full decode.
- Complete unittest discovery: 204 tests PASS.
- Compileall, asset registry, education-asset metadata validation, plan-only and `git diff --check`: PASS.
- Battery Blender asset validation and 24-second mixed preview: NOT RUN because Windows executable interop failed with `UtilBindVsockAnyPort:309: socket failed 1`. See [Battery Educational QA](BATTERY_EDUCATIONAL_QA.md).
- Dedicated Battery Simulation Actions: PASS — [run 38119694050](https://github.com/hinoonyaso/make_simulation/actions/runs/38119694050) executed PyBaMM, validated the result, rendered Manim from solver output, and decoded the media.
- Education renderer smoke: PASS — [run 38119694096](https://github.com/hinoonyaso/make_simulation/actions/runs/38119694096).
- AI trace reproducibility: PASS — [run 38119694060](https://github.com/hinoonyaso/make_simulation/actions/runs/38119694060).
- Engineering simulation: PASS — [run 38119694053](https://github.com/hinoonyaso/make_simulation/actions/runs/38119694053).

## Merge and release state

V14.2 is not merged to `main`. Do not publish or describe the 6-second Manim-only smoke as the requested mixed preview. The remaining local acceptance item is to run Blender from a working Blender/WSL session, produce the 720-frame composition, inspect its actual frames and rerun delivery validation. Then push the branch, open the PR and confirm the dedicated Actions result.
