# V14.3 QA Report

| Check | Result | Evidence |
|---|---|---|
| Sparse plan, renderer capability, and 0-based to Blender frame mapping | PASS | `test_sparse_render_plan.py` plan and registry tests |
| Blender result report reconciles rendered image counts and timeline | PASS | `test_blender_report_must_match_plan_and_total_rendered_images` |
| Gap rejection, unsupported renderer/still capability, frame mapping | PASS | `test_gap_overlap_still_capability_and_unsupported_renderer_are_rejected` |
| FFmpeg sparse composition fixture and exact final count | PASS | 6-frame synthetic fixture decodes and probes as 6 frames |
| Sparse plan-only contract | PASS | `--plan-only` builds and validates the same sparse segments as rendering; valid plan writes `render_segments.json`; invalid `render_mode` exits before creating the run directory |
| Python compile and `git diff --check` | PASS | Local V14.3 worktree |
| Full repository regression suite | PASS | `uv run --locked python -m unittest discover -s tests -v`; 219 tests after V14.3 P2 regression coverage |
| Python compile | PASS | `uv run --locked python -m compileall -q core scripts tests` |
| Asset registry and education asset checks | PASS | 39 registry entries; 6 generated assets checked |
| Real PyBaMM Solver output and result validation | PASS | Run `v143-local-validation`, 361 samples, 1800 s |
| Actual PyBaMM early-cutoff event | PASS | Run `v143-final-early-cutoff`; voltage event at 3606.549306 s of 7200 s, 62 samples; result validation PASS |
| Manim-only battery preview | PASS | 960×540, 30 fps, 180 frames / 6 s, H.264, silent, full decode; `/tmp/v14.3-manim/manim-smoke/preview.mp4` |
| Blender execution in GitHub Actions | PASS | Inspected checked-in workflows: no Blender binary installation, Blender invocation, or Blender render job; battery workflow retains solver, FFmpeg fixture, and Manim checks |
| Latest GitHub Actions for review HEAD `4b588b5` | PASS | [Battery #26](https://github.com/hinoonyaso/make_simulation/actions/runs/38140991559), [Education #45](https://github.com/hinoonyaso/make_simulation/actions/runs/38140991485), and [AI Trace #106](https://github.com/hinoonyaso/make_simulation/actions/runs/38140991450) all completed successfully. Battery has `battery-simulation-smoke` only; no Blender job ran. |
| Actual Blender sparse preview, Eevee backend, rendered-frame count, final full decode | PASS | Blender 5.2.1 LTS / `BLENDER_EEVEE`; one still + 180 source images; final 960×540 H.264, 30 fps, 720 frames / 24 s, full decode PASS; `/tmp/v14.3-sparse-actual/v143-blender-final/preview.mp4` |
| Video metadata and delivery gate | PASS | SHA-256 `1d5091cd4b94d2c01f1612e0cdbf5d95eafb9ed4397d775f345401ae4d1f933a`; `ffprobe` and `validate_delivery.py` confirm 24.000 s, 960×540, H.264, 30 fps, 720 frames, SAR 1:1, 8 caption cues, no audio stream (expected), full decode |
| Solver provenance | PASS | `validate_battery_result.py`: run `v143-local-validation`, 361 samples, 1800 s, result SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`; manifest, renderer context, Blender report, and provenance use the same run and hash |
| Asset and timeline provenance | PASS | Loaded asset `edu.mechanical_primitives.v1`; asset SHA-256 matches Blender report; timeline validator passes and canonical timeline SHA matches render plan/provenance; 4 beats map to contiguous `[0,720)` frames |
| GitHub PR review state | PASS | PR #8 was open and mergeable at the latest status check; no review submissions, inline threads, or comments were returned. Human visual acceptance is recorded below. |
| GPU verification | BLOCKED, non-blocking | `nvidia-smi`: GPU access blocked by operating system; preview rendered with Blender EEVEE, but this does not establish GPU use |

## Visual review evidence

**Full-motion visual review: PASS (human review).** The user confirmed in this session that they watched the complete 24-second preview at normal 1× speed and that review passed. This status is based on the user's explicit review result, not on frame extraction or a playback process run by the agent. The reviewed artifact is `pilots/v14_education/output/lessons/v143-final-acceptance/preview.mp4`, SHA-256 `1d5091cd4b94d2c01f1612e0cdbf5d95eafb9ed4397d775f345401ae4d1f933a`.

The review materials were extracted from that exact MP4 without changing or re-rendering it: `review_BAT01.png` through `review_BAT04.png` and `review_BAT04_detail.png` (21 s). The preview is silent by design; narration review is not applicable. GPU use remains unverified and is not a merge blocker per the V14.3 acceptance instructions.

The earlier sampled-frame review caught clipped heading text; the heading y-position was moved into the camera safe area and the final preview was re-rendered. BAT03 intentionally isolates the solver-linked SOC gauge. The user has now accepted the complete motion review; no further visual code change was requested.

## Composition fix found by real render

The first real sparse composition failed because the Manim input reported an undefined sample aspect ratio while the Blender/PNG inputs used 1:1. Composition now normalizes each segment with FFmpeg `setsar=1`; the sparse fixture test uses a 2:1 Manim input and asserts the final output is 1:1. The focused sparse test suite passes.

The 24-second silent preview is rendered and delivery-validated. User full-length normal-speed motion review passed; the PR is Ready for Review and merge remains subject to explicit user approval. Narration is not part of this silent preview.

## Sparse plan-only review fix

PR #8 P2 review requested sparse segment validation before `PLAN_VALIDATED`. `build_validated_sparse_plan()` is now shared by plan-only preflight and actual rendering. Invalid sparse input such as `render_mode: "typo"` fails before output directory creation; valid sparse plan-only runs emit `render_segments.json` and identify it in `production_report.json`. After TTS changes the manifest/timeline, the same helper validates the final timeline again. `legacy_full` keeps its previous report shape and does not create a sparse segments file.

Regression coverage includes CLI end-to-end valid/invalid plan-only cases and the existing still capability, renderer allow-list, timeline gap/overlap, and source-frame mapping checks. Full suite: 219 tests PASS. No Blender, Manim, Solver, or TTS process is invoked by plan-only.
