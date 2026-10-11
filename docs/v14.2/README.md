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
- Early cutoff: 7200 s requested; `Minimum voltage [V]` event at 3606.549305848102 s; 62 saved samples; validated result SHA-256 `23ca1050317fe899e43ce0c5ebbdf42dab3c5438d1d3e7dd1cb8676bffcb5b3e`.
- Corrected-source commit `f6dd301938fe6aa29986b5f1d2210d0d54a40b13` passed [Battery Actions run 38129252744](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252744), including both solver smoke and mixed preview. The mixed job used Blender 5.2.1 LTS and the registered asset. It produced a silent 24 s, 960×540, H.264, 30 fps, 720-frame preview; video SHA-256: `d1d0fdab89e3506986a602224faaacff1737f92cf9e9ff2a89d81ebb0eff0e4a`.
- Frame review of the first mixed render found stale Manim chart objects in the later summary beat. The scene now fades Manim objects during Blender-owned beats, creates a fresh title for each Manim beat, and holds the final state for one frame. The corrected source passed the mixed job in run 38129252744. Its artifact passed manifest, delivery, caption-timing, full-decode, frame-count, asset-load and provenance checks.
- Regression: 207 unit tests pass; Python `compileall`, the 39-entry asset registry, six catalog/generated asset checks, and both battery result validators pass.
- Other workflows for the corrected source also passed: [Education Renderer run 38129252723](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252723), [AI Trace run 38129252696](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252696), and [Engineering Simulation run 38129252770](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252770).
- Blender could not be launched from this WSL session, so the verified CI artifact is the evidence for the actual Blender 5.2.1 scene and asset load. The 18650 is a CC0 educational concept mesh, not Chen2020 cell geometry. TTS, 1080p and a narrated 60–90 second lesson are out of scope.

In corrected run 38129252744, Blender took 4430.12 s (about 73 min 50 s), Manim 10.62 s, and the workflow ran about 76 min 29 s. FFmpeg composition time was not separately recorded. Beat-aware sparse Blender rendering is a future optimization, not implemented here.

## Model boundary

The CC0 18650 asset is an educational concept mesh, not Chen2020 cell geometry. SPM output is a model calculation, not experimental data. Displayed SOC is Coulomb Counting over model discharge capacity, not measured SOC or BMS state. See [integration](PYBAMM_INTEGRATION.md), [educational QA](BATTERY_EDUCATIONAL_QA.md), and [provenance](SOLVER_PROVENANCE.md).
