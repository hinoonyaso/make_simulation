# V14.3 Local Sparse Rendering

V14.3 adds a registry-selected sparse rendering strategy for the PyBaMM battery lesson. The shared V9 manifest, V12 timeline, solver output, asset identity, subtitles, and final delivery validation remain authoritative. Only the Blender work is reduced: explicit static beats render once; animated beats render their original timeline frame ranges.

## Current status

- Implemented on `v14.3-local-sparse-rendering`, based on main merge commit `9c8987d`.
- Sparse plan and FFmpeg composition fixture tests pass.
- Real Blender preview is **BLOCKED** in the current WSL session. No Linux `blender` executable is on PATH; the installed Windows Blender 5.2 executable fails to start with `UtilBindVsockAnyPort:309: socket failed 1`. NVIDIA access is blocked by the OS. No full preview or performance claim is made.
- GitHub Actions keeps the full Blender job behind `workflow_dispatch`; routine PR validation covers plan logic and a short FFmpeg fixture only.

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
