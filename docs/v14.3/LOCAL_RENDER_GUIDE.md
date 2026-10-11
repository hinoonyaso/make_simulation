# Local Render Guide

Use Ubuntu 24.04 with Blender 5.2.x, FFmpeg, and the repository's locked Python environment. The sparse implementation is local-first; routine GitHub Actions must not render either a full or sparse Blender lesson.

```bash
uv sync --locked --group sim-battery --group sim-render
uv run python scripts/run_battery_simulation.py \
  --config examples/education/battery_spm_config.json \
  --output-dir pilots/v14_education/output/battery-solver-run
uv run python scripts/validate_battery_result.py pilots/v14_education/output/battery-solver-run
uv run python scripts/produce_lesson.py \
  --spec examples/education/battery_spm_smoke.json \
  --solver-result pilots/v14_education/output/battery-solver-run \
  --preview --render-strategy sparse \
  --output-root pilots/v14_education/output/lessons --run-id battery-sparse-preview
```

Set `BLENDER_BIN` if Blender is installed outside PATH. The renderer reports its Blender version and selected Eevee backend. GPU use is not assumed; verify it in the renderer/runtime and OS environment. Windows Blender invoked from WSL may be unavailable even when installed on the Windows mount. If startup fails, do not report a real render PASS; use unit and FFmpeg fixture checks and retry in native Linux or a functioning Blender shell.

Expected artifacts include `render_segments.json`, `blender_segments/battery_BAT01.png`, the BAT03 encoded segment and source sequence, `asset_load_report.json`, `renderer_provenance.json`, captions, and `preview.mp4`.
