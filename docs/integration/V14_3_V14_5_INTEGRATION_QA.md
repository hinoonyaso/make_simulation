# V14.3–V14.5 Integration QA

## Scope and source revisions

This report covers an isolated validation branch. The original V13 worktree and feature branches were not edited, and no PR or `main` merge was performed.

| Ref | SHA |
|---|---|
| `origin/main` base | `9c8987dede01dd5cabd2d89edce67d0bdf7ee233` |
| V14.3 sparse rendering | `5a7e6c83f01e758f5561f7d5cab47ee0cec1ef7c` |
| V14.4 bearing visual excellence | `b1e45be371ccb5c601483d2360d4e2742b453b9e` |
| V14.5 unified visual design | `bf3614138bb551169dabee03f0fb49c31b9412b7` |
| V14.5 ancestry | V14.5 contains V14.4 at `b1e45be`; V14.4 was not merged a second time. |
| Integration merge commit | `eda74b2` (`origin/v14.5-unified-visual-design-system` merged after V14.3) |

The branch is `integration/v14.3-v14.5-validation`, created from `origin/main` in `/home/sang/make_simulation-integration`.

## Merge and implementation notes

The V14.5 merge had one content conflict: `pilots/v14_education/blender/battery_scene.py`. The resolution retained the V14.3 sparse plan and segment arguments, still rendering, legacy full rendering, and V14.5 visual profile selection, Studio Light / Technical Dark lighting, exposure `0.0`, gamma `1.0`, and battery label safe-area placement (`y=0.042`). Existing `renderer_registry.py` and `scripts/produce_lesson.py` merged automatically; both strategies and profile forwarding were checked in plan output and actual renders.

The first integrated renders exposed a Studio Light canvas mismatch at Blender/Manim beat boundaries: the Blender camera background sampled at RGB `(147, 151, 155)` while Manim used `(215, 220, 226)`. Battery scene setup now separates the camera ray background (profile color at strength `1.0`) from the existing world-light background (profile `world_strength`). This preserves the configured world illumination while aligning the visible canvas. The post-fix samples are Blender `(193, 194, 197)` and Manim `(215, 220, 226)`; Technical Dark samples are `(0, 4, 14)` and `(10, 13, 31)`. The residual color-managed difference is visible only as a small background shift; sampled brightness-jump candidates are now absent.

No renderer API or dependency was added. The change is local to the Battery scene; other shared studio scenes are unchanged.

## Solver provenance

A fresh CPU PyBaMM run used `examples/education/battery_spm_config.json` with PyBaMM `26.10.0.0` and `IDAKLUSolver`.

- Result: `PASS`, 361 samples, 0–1800 seconds, 5-second sample interval, normal final-time termination.
- Result SHA-256: `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`.
- `scripts/validate_battery_result.py /tmp/v143-v145-battery-solver`: `PASS`.
- Both profile renders consumed this same validated result SHA and run ID `v143-v145-integrated-pybamm`.

## Battery sparse planning and actual mixed previews

All preview media is silent by design. The shared timeline is 24 seconds, 30 fps, 720 frames. Each profile produced a real Blender + Manim mixed MP4 using Blender 5.2.1 LTS and Manim 0.21.0, at 960×540, H.264, with full decode and eight caption cues passing `validate_delivery.py`.

| Profile | Blender images | Blender time | Manim time | Segment encode | Composition | Video SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| Technical Dark | 1 still + 180 animation = 181 | 29.89 s | 8.47 s | 0.45 s | 1.39 s | `669b20b6e2d76eba936241d28f47ca595493e681b661f97ac8e122b7a1359fb8` |
| Studio Light | 1 still + 180 animation = 181 | 29.89 s | 8.69 s | 0.47 s | 1.46 s | `d42259957911d06be8f01d996b14cc4ac886668e156438bae6005a07ea9f25d2` |

The sparse plan maps BAT01 to one Blender still held for 180 output frames, BAT02 to 180 Manim frames, BAT03 to 180 Blender animation frames, and BAT04 to 180 Manim frames. This requests 181 Blender images versus 720 under a per-frame full-render plan: 74.9% fewer Blender images. It is an image-count reduction, not an elapsed-time speedup claim. The `legacy_full` Technical Dark plan-only contract also passed; a legacy full Blender video was not rendered, so no legacy render performance comparison is available.

Post-fix output paths:

- Technical Dark: `/tmp/v143-v145-integration-render-r2/battery-technical-dark/preview.mp4`
- Studio Light: `/tmp/v143-v145-integration-render-r2/battery-studio-light/preview.mp4`
- Matching production reports, render plans, captions, renderer provenance, and 4-fps visual candidate reports are beside each MP4.

`analyze_visual_render.py` sampled 96 frames per video. Neither render had dark/blank candidates or brightness-jump candidates. Technical Dark reported a 2.5-second repeated-frame candidate in the BAT01 static hold; this matches the planned still-image segment. Studio Light reported no repeated-frame candidate. These are automated candidates, not proof of motion quality.

A contact sheet of six representative frames per profile plus a 0.5-second voltage-beat contact sheet were visually inspected. The battery geometry, voltage curve and moving marker, SOC gauge, and model-limit summary were visible in those samples. Full 1× playback and learner comprehension were not reviewed in this validation, and the generated previews contain no narration audio. Therefore full-motion, audio, and educational human acceptance remain `INCOMPLETE`.

## Regression checks

| Check | Result | Evidence |
|---|---|---|
| Full unittest suite | PASS | `uv run --locked --no-sync python -m unittest discover -s tests -v`; 250 tests, including V12 and V13/V14 tests |
| Python compile | PASS | `python -m compileall -q core scripts tests assets/education` |
| Visual design and all six scenes | PASS | `scripts/validate_visual_design.py --all-scenes` |
| Visual asset registry | PASS | `core/visual-assets/asset_registry.py validate`; 39 assets |
| Education asset/catalog validation | PASS | `scripts/acquire_education_assets.py --validate`; 39 registry entries, 6 catalog models, 6 generated asset metadata checks |
| Battery Sparse Technical Dark plan | PASS | `PLAN_VALIDATED`, segment plan emitted |
| Battery Sparse Studio Light plan | PASS | `PLAN_VALIDATED`, segment plan emitted |
| Battery Legacy Full Technical Dark plan | PASS | `PLAN_VALIDATED`; no full legacy render performed |
| Bearing plan regression | PASS | `examples/education/bearing.json`, legacy default, asset and lesson plan validated |
| Gear plan regression | PASS | `examples/education/spur_gears.json`, legacy default, asset and lesson plan validated |
| Existing default-profile lesson plan | PASS | `examples/education/education_smoke.json` retained Technical Dark default |
| `apply_theme()` compatibility and timeline/manifest unit coverage | PASS | Included in 250-test suite |
| `git diff --check` | PASS | Integration worktree |
| AI Trace GitHub Actions | PASS | [Run #137](https://github.com/hinoonyaso/make_simulation/actions/runs/38734493644) completed successfully on integration SHA `c06dc917e13f22f82337cd825a9899bad8637407`. |
| Education Renderer / Battery GitHub Actions | NOT RUN | Education workflow supports manual dispatch but has no push trigger for this integration branch; the connected GitHub tools are read-only for Actions dispatch, and no authenticated `gh` CLI is installed. Local validation passed. |

The test environment emitted an existing optional SoX warning. Rendering, tests, and silent delivery validation succeeded without SoX. Blender 5.2.1 was installed and executed successfully using the approved unsandboxed WSL path. GPU use was not established.

## Remaining limitations and merge recommendation

- P1: none identified by the executed tests, mixed renders, and sampled-frame review.
- P2: no same-host legacy full Blender render timing was captured; only requested Blender image counts were compared. Studio Light still has a small color-managed canvas difference between Blender and Manim.
- P2: full 1× motion review, narration review, and learner comprehension remain incomplete; current previews are silent.
- AI Trace remote CI passed on integration SHA `c06dc917e13f22f82337cd825a9899bad8637407`; Education Renderer and Battery Actions remain `NOT RUN`. The report-only follow-up commit will trigger another AI Trace push run.

Recommended stacked PR sequence: merge PR #8 (V14.3) into `main`; then PR #9 (V14.4) into `main`; then retarget PR #10 from V14.4 to `main`, allow the base-change CI to complete, and review/merge V14.5. This integration branch is validation evidence only; it does not authorize any PR merge. Do not merge `main` as part of this task.

## Final integration recheck — 2026-10-15

The following recheck was performed against integration HEAD `c06dc917e13f22f82337cd825a9899bad8637407`. No production source changed during this recheck.

| Check | Result | Fresh evidence |
|---|---|---|
| Git remote/worktree | PASS | `git fetch origin --prune` succeeded; integration branch is clean and matches `origin/integration/v14.3-v14.5-validation` at `c06dc91`. The original `/home/sang/make_simulation` V13 worktree remains untouched (66 pre-existing modified/untracked paths). |
| Full unittest | PASS | 250 tests, 11.842 s, using the existing `/home/sang/make_simulation-v14.5/.venv` with `UV_PROJECT_ENVIRONMENT=...`; no test skips were introduced. An initial attempt selected an empty worktree-local `.venv` and failed imports; the complete rerun in the configured project environment passed. |
| Compile, visual style, assets | PASS | `compileall`; all six Blender/Manim scenes and design-token contrast; registry (39 assets) and education catalog validation (39 entries, 6 catalog models, 6 generated metadata checks). |
| Education Manim smoke | PASS | Fresh silent 4-second preview at `/tmp/v14-final-education-smoke/final-smoke/preview.mp4`; manifest, 960×540/30fps H.264, 120 frames, captions, timeline and full decode passed. |
| Gear Manim smoke | PASS | Fresh silent 12-second preview at `/tmp/v14-final-education-smoke/gear-final/preview.mp4`; manifest, calculated gear mapping, 960×540/30fps H.264, 360 frames and full decode passed. |
| Battery normal solver | PASS | Existing solver result revalidated: PyBaMM 26.10.0.0 / IDAKLUSolver, 361 samples, 1800 s, SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25`. |
| Battery early cutoff | PASS | Fresh local solver run ended on `event: Minimum voltage [V]` at 3606.549305848152 s, before its requested end; 62 samples and validated result SHA-256 `f2631a1c28111bf4e19af646a6c82978990f36e9025480ee107235b22d43c66a`. |
| Battery mixed preview delivery | PASS | Both existing MP4s were checked at preview floor 960×540, 30 fps, with timeline, caption timing and full decode. Each has 720 frames, 8 caption cues and no audio stream by design. The final-delivery validator's default 1080p floor was overridden explicitly for these preview artifacts. |
| Battery render provenance | PASS | Both profile reports identify the same validated solver result/run, battery asset SHA, sparse 1-still + 180-animation plan, 720-frame composition and Blender 5.2.1 LTS / Manim 0.21.0. Video hashes remain the values in the table above. |
| Visual metrics / sampled frames | PASS, sampled only | Fresh 96-frame metrics for each preview found no dark/blank or brightness-jump candidates. Technical Dark reported a repeated-frame candidate only in the intentional BAT01 still hold. Existing profile contact sheets were inspected; model, graph/marker, SOC gauge, and model-limit text are visible. This is not full-motion playback. |
| Remote Actions | AI Trace PASS; Education/Battery NOT RUN — PERMISSION BLOCKED | [AI Trace run #137](https://github.com/hinoonyaso/make_simulation/actions/runs/38734493644) succeeded for `c06dc91`. GitHub read access confirmed no Education or Battery run on this branch. `gh` is unavailable and the connected GitHub interface has GET/read operations but no workflow-dispatch operation, so no remote dispatch could be issued. The workflows were not modified. |
| `git diff --check` | PASS | Clean before this report-only update; rerun before commit. |

`FULL_MOTION_REVIEW=INCOMPLETE`. A human should watch both 24-second previews at 1×, focusing on BAT01→BAT02 near 6 s, BAT02→BAT03 near 12 s, and BAT03→BAT04 near 18 s; check for visible canvas jumps, clipped text, geometry occlusion, unexpected freezes, graph marker continuity and SOC motion. The videos are silent; narration QA is `NOT APPLICABLE` for these previews. Learner comprehension is untested.

Current readiness remains `CONDITIONAL`: no P0/P1 defect was found in the executed local checks or sampled visual review, but Education and Battery GitHub Actions were not run remotely and full-motion human review is incomplete. Current PR API state: #8 open/Ready/mergeable, #9 open/Draft/mergeable, #10 open/Draft/mergeable (stacked on V14.4). The integration-only `84ae4ff` change modifies only `pilots/v14_education/blender/battery_scene.py` to separate camera-ray background from world lighting. It is not present in PR #10's head. After the planned PR sequence, review the resulting `battery_scene.py` against this change and submit it as a deliberate follow-up change if still needed; do not assume the merge contains it or cherry-pick without inspecting the merged file. No PR or `main` changes were made.
