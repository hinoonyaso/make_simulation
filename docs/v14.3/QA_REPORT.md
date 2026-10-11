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
| Actual PyBaMM early-cutoff event | PASS | Run `v143-final-early-cutoff`; voltage event at 3606.549306 s of 7200 s, 62 samples; result validation PASS |
| Manim-only battery preview | PASS | 960×540, 30 fps, 180 frames / 6 s, H.264, silent, full decode; `/tmp/v14.3-manim/manim-smoke/preview.mp4` |
| Blender execution in GitHub Actions | PASS | `battery-mixed-preview` job, Blender installation, and Blender render commands removed from the battery workflow; other workflow `run` blocks contain no Blender execution |
| GitHub Actions on `0dac8ef` | PASS | [Education #42](https://github.com/hinoonyaso/make_simulation/actions/runs/38139882362) and [Battery #23](https://github.com/hinoonyaso/make_simulation/actions/runs/38139882382) succeeded; Battery run has only `battery-simulation-smoke` (no mixed Blender job) |
| Actual Blender sparse preview, Eevee backend, rendered-frame count, final full decode | PASS | Blender 5.2.1 LTS / `BLENDER_EEVEE`; one still + 180 source images; final 960×540 H.264, 30 fps, 720 frames / 24 s, full decode PASS; `/tmp/v14.3-sparse-actual/v143-blender-final/preview.mp4` |
| GPU verification | BLOCKED | `nvidia-smi`: GPU access blocked by operating system |

## Actual frame review

Reviewed Blender source frames 1, 361, 450, and 540 plus final-video boundary samples around 0, 12, 15, 18, and 20–23.5 s. This caught clipped Blender heading text; the heading y-position was moved into the camera safe area and the final preview was re-rendered. The BAT03 visual intentionally isolates the solver-linked SOC gauge. Full-length normal-speed motion review and narration review remain pending; the preview is silent.

## Composition fix found by real render

The first real sparse composition failed because the Manim input reported an undefined sample aspect ratio while the Blender/PNG inputs used 1:1. Composition now normalizes each segment with FFmpeg `setsar=1`; the sparse fixture test uses a 2:1 Manim input and asserts the final output is 1:1. The focused sparse test suite passes.

The 24-second silent preview is rendered and delivery-validated. Keep the PR Draft pending full normal-speed motion review; narration is not part of this silent preview.
