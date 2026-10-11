# V14.3 Local Sparse Rendering

V14.3 adds a registry-selected sparse rendering strategy for the PyBaMM battery lesson. The shared V9 manifest, V12 timeline, solver output, asset identity, subtitles, and final delivery validation remain authoritative. Only the Blender work is reduced: explicit static beats render once; animated beats render their original timeline frame ranges.

## Current status

- Implemented on `v14.3-local-sparse-rendering`, based on main merge commit `9c8987d`.
- Sparse plan and FFmpeg composition fixture tests pass.
- Actual Blender 5.2.1 sparse preview **PASS**: 24 seconds, 960×540, 30 fps, 720 H.264 frames, silent, full decode PASS. Blender wrote 181 images (one still + 180 animation frames). Current SHA-256: `1d5091cd4b94d2c01f1612e0cdbf5d95eafb9ed4397d775f345401ae4d1f933a`. GPU use remains unverified.
- Review artifact: `pilots/v14_education/output/lessons/v143-final-acceptance/preview.mp4` (same validated SHA-256). The user watched the complete 24-second clip at normal 1× speed and confirmed review PASS. BAT01–BAT04 contact sheets and a BAT04 detail frame are in the same ignored output directory. PR #8 is Ready for Review; merge remains pending explicit user approval.
- Latest Actions for review HEAD `4b588b5`: [Battery #26](https://github.com/hinoonyaso/make_simulation/actions/runs/38140991559), [Education #45](https://github.com/hinoonyaso/make_simulation/actions/runs/38140991485), and [AI Trace #106](https://github.com/hinoonyaso/make_simulation/actions/runs/38140991450) all PASS. Checked-in workflows do not install or execute Blender.

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

Sparse `--plan-only` performs the same segment/frame-mapping validation as the renderer and writes `render_segments.json`. Invalid sparse plans fail before a run output directory is created. `legacy_full` retains its existing plan-only output contract.
