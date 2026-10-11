# V14.3 QA Report

| Check | Result | Evidence |
|---|---|---|
| Sparse plan, renderer capability, and 0-based to Blender frame mapping | PASS | `test_sparse_render_plan.py` plan and registry tests |
| Blender result report reconciles rendered image counts and timeline | PASS | `test_blender_report_must_match_plan_and_total_rendered_images` |
| Gap rejection, unsupported renderer/still capability, frame mapping | PASS | `test_gap_overlap_still_capability_and_unsupported_renderer_are_rejected` |
| FFmpeg sparse composition fixture and exact final count | PASS | 6-frame synthetic fixture decodes and probes as 6 frames |
| Plan-only battery lesson, default strategy | PASS | `produce_lesson.py --plan-only` reports `render_strategy: sparse` and validates the existing asset |
| Python compile and `git diff --check` | PASS | Local V14.3 worktree |
| Full repository regression suite | PASS | `uv run --locked python -m unittest discover -s tests -v`; 216 tests |
| Python compile | PASS | `uv run --locked python -m compileall -q core scripts tests assets/education` |
| Asset registry and education asset checks | PASS | 39 registry entries; 6 generated assets checked |
| Real PyBaMM Solver output and result validation | PASS | Run `v143-local-validation`, 361 samples, 1800 s |
| Manim-only battery preview | PASS | 960×540, 30 fps, 180 frames / 6 s, H.264, silent, full decode; `/tmp/v14.3-manim/manim-smoke/preview.mp4` |
| Automatic full Blender render gate | PASS | `battery-mixed-preview` remains `if: github.event_name == 'workflow_dispatch'`; no automatic full Blender call added |
| Actual Blender sparse preview, Eevee backend, rendered-frame count, final full decode | BLOCKED | Windows Blender launch fails in WSL with `UtilBindVsockAnyPort`; no Linux Blender executable is available |
| GPU verification | BLOCKED | `nvidia-smi`: GPU access blocked by operating system |

No 24-second Blender render or final video is claimed as completed. The branch should remain Draft until a real local preview is rendered and validated.
