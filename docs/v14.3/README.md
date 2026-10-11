# V14.3 Local Sparse Rendering

V14.3 adds a registry-selected sparse rendering strategy for the PyBaMM battery lesson. The shared V9 manifest, V12 timeline, solver output, asset identity, subtitles, and final delivery validation remain authoritative. Only the Blender work is reduced: explicit static beats render once; animated beats render their original timeline frame ranges.

## Current status

- Implemented on `v14.3-local-sparse-rendering`, based on main merge commit `9c8987d`.
- Sparse plan and FFmpeg composition fixture tests pass.
- Actual Blender 5.2.1 sparse preview **PASS**: 24 seconds, 960×540, 30 fps, 720 H.264 frames, silent, full decode PASS. Blender wrote 181 images (one still + 180 animation frames). Sandbox launch hit `UtilBindVsockAnyPort:309: socket failed 1`, while the approved out-of-sandbox local invocation succeeded. GPU access remains blocked/unverified.
- Output: `/tmp/v14.3-sparse-actual/v143-blender-final/preview.mp4`. A full normal-speed motion review is still pending; reviewed boundary/key frames are recorded in the QA report.
- GitHub Actions contains no Blender executable installation or Blender render job. PR validation retains solver, early-cutoff, sparse-plan, FFmpeg-fixture, and Manim smoke checks.

See [sparse rendering design](SPARSE_RENDERING.md), [local rendering guide](LOCAL_RENDER_GUIDE.md), [performance report](PERFORMANCE_REPORT.md), and [QA report](QA_REPORT.md).

## Try the battery strategy

Run a validated PyBaMM solver output first, then:

```bash
uv run python scripts/produce_lesson.py \
  --spec examples/education/battery_spm_smoke.json \
  --solver-result <validated-solver-result-directory> \
  --preview --render-strategy sparse
```

For other registered topics, the default remains `legacy_full`. The battery renderer defaults to `sparse`; use `--render-strategy legacy_full` to request its existing full Blender path explicitly.
