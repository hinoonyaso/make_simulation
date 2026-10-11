# V14.2 PyBaMM Battery Simulation Integration

V14.2 adds an optional, reproducible PyBaMM SPM discharge path to the education lesson pipeline. It keeps solver execution separate from planning and rendering.

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

Planning alone uses `--plan-only` and never executes PyBaMM. Computed rendering requires a validated result directory. The dedicated workflow is [V14.2 Battery Simulation](../../.github/workflows/v14.2-battery.yml).

## Current verification snapshot

- PyBaMM 26.10.0.0, CPU, SPM / Chen2020, 1C, initial SOC 1.0, requested 1800 s.
- Local solver run: PASS; 361 samples at 5 s, terminal time 1800 s, IDAKLUSolver execution 0.1183 s. Result SHA-256: `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`.
- A real early-cutoff run now exercises the Chen2020 lower-voltage event: 7200 s requested, event at 3606.549305848152 s, 62 saved samples at 60 s plus the exact event endpoint. PyBaMM termination is `event: Minimum voltage [V]`; result validation and file hashes pass. The calculated SOC endpoint is retained as −0.00181925 rather than clamped.
- Manim actual-solver-data smoke: PASS, 960×540, 30 fps, 180 frames, H.264, full decode. It is a 6-second Manim-only smoke, not the 24-second mixed preview.
- Unit regression: 207 tests PASS; compileall, 39-entry asset registry, 6 education catalog models/generated asset files and lesson planning PASS.
- Blender API selection now uses the engine identifiers exposed by the runtime and prefers `BLENDER_EEVEE` (the 5.2 API identifier), with `BLENDER_EEVEE_NEXT` fallback. The battery `produce_lesson.py --blender-still-frame 1` path writes the normal validated solver context, loads the registered Blender asset, and renders a still without requiring Manim. The pinned official Blender 5.2.1 Actions job then attempts the 24-second mixed preview.
- Local Blender asset load and 24-second mixed render: BLOCKED. Blender 5.2.1 exists under `/mnt/c`, but this WSL session cannot launch either `cmd.exe` or Blender (`UtilBindVsockAnyPort:309: socket failed 1`). No Blender load/render success is claimed. The new CI job is intended to supply an independent Linux Blender runtime; until it completes, P1 remains unverified.
- TTS, 1080p and a 60–90 second narrated lesson: not in scope.

The generated 6-second local preview is outside Git at `/tmp/v14.2-preview-final/battery-manim-final/preview.mp4`.

## Model boundary

The CC0 18650 asset is an educational concept mesh and is not asserted to match the Chen2020 cell geometry. SPM output is a model calculation, not experimental data. Estimated SOC is Coulomb Counting over model discharge capacity, not a measured SOC or BMS estimate. See [integration](PYBAMM_INTEGRATION.md), [educational QA](BATTERY_EDUCATIONAL_QA.md), and [provenance](SOLVER_PROVENANCE.md).
