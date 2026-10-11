# V14.2 PyBaMM Battery Simulation Integration

V14.2 adds an optional, reproducible PyBaMM SPM discharge path to the education lesson pipeline. Solver execution is separate from planning and rendering.

## Reproduce locally

```bash
uv sync --locked --group sim-battery --group sim-render
uv run python scripts/run_battery_simulation.py \
  --config examples/education/battery_spm_config.json \
  --output-dir pilots/v14_education/output/battery-solver-run
uv run python scripts/validate_battery_result.py pilots/v14_education/output/battery-solver-run
uv run python scripts/produce_lesson.py \
  --spec examples/education/battery_spm_smoke.json \
  --solver-result pilots/v14_education/output/battery-solver-run \
  --preview --output-root pilots/v14_education/output/lessons \
  --run-id battery-spm-preview
```

Planning with `--plan-only` does not execute PyBaMM. Computed rendering requires a validated result directory. The workflow is [V14.2 Battery Simulation](../../.github/workflows/v14.2-battery.yml).

## Verified results

- Solver: PyBaMM 26.10.0.0, CPU, isothermal SPM / Chen2020, IDAKLUSolver. Normal discharge: 1C for 1800 s, 361 samples at 5 s, result SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`.
- Early cutoff: 7200 s requested; `Minimum voltage [V]` event at 3606.549305848152 s; 62 saved samples; validated result SHA-256 `f2631a1c28111bf4e19af646a6c82978990f36e9025480ee107235b22d43c66a`.
- Battery workflow [run 38122266473](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266473): both `battery-simulation-smoke` and `battery-mixed-preview` succeeded. The latter used Blender 5.2.1 LTS, loaded the registered asset and produced a silent 24 s, 960×540, H.264, 30 fps, 720-frame preview. CI video SHA-256: `61dd936667f7d56764519f52dfe4a2b1fbd32d8afc209cd02aa1a8da60972037`.
- The CI artifact frame review found stale Manim chart objects in the later summary beat. `battery_scene.py` now fades Manim objects during Blender-owned beats and makes a fresh title per Manim beat. The corrected local re-composition uses the successful CI Blender output and a new Manim render; SHA-256 `05823bffa2d7a939731cc75ab152dace82cab107f4cc86910f185b67cb0f1af8`. It passes manifest validation, full decode and 720-frame delivery validation. A CI run on the corrected source is still required before calling that revision remotely verified.
- Regression: 207 unit tests pass; Python `compileall`, the 39-entry asset registry, six catalog/generated asset checks, and both battery result validators pass.
- Other workflows passed: [Education Renderer run 38122266490](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266490), [AI Trace run 38122266514](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266514), and [Engineering Simulation run 38122266495](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266495).
- Blender could not be launched from this WSL session, so local Blender rerendering was unavailable. The CI artifact is the evidence for the actual Blender 5.2.1 scene and asset load. TTS, 1080p and a narrated 60–90 second lesson are out of scope.

The Blender time for the successful mixed CI run was 4965.80 s (about 82 min 46 s); Manim took 12.66 s. Workflow elapsed time was about 84 min 39 s. FFmpeg composition time was not separately recorded. Beat-aware sparse Blender rendering is a future optimization, not implemented here.

## Model boundary

The CC0 18650 asset is an educational concept mesh, not Chen2020 cell geometry. SPM output is a model calculation, not experimental data. Displayed SOC is Coulomb Counting over model discharge capacity, not measured SOC or BMS state. See [integration](PYBAMM_INTEGRATION.md), [educational QA](BATTERY_EDUCATIONAL_QA.md), and [provenance](SOLVER_PROVENANCE.md).
