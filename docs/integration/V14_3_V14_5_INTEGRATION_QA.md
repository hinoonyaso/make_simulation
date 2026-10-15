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

A contact sheet of six representative frames per profile plus a 0.5-second voltage-beat contact sheet were visually inspected. The battery geometry, voltage curve and moving marker, SOC gauge, and model-limit summary were visible in those samples. At this initial sampled-review stage, full 1× playback and learner comprehension had not been reviewed. The later full-motion human review is recorded in **Final release-gate confirmation** below. The generated previews contain no narration audio.

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
| AI Trace GitHub Actions | PASS | [Run #139](https://github.com/hinoonyaso/make_simulation/actions/runs/38742184692) completed successfully on final-gate SHA `6a6cc9a8e2a53bc84527d58462da3916acba5fd9`; a later commit only updates this report's run record. |
| Education Renderer / Battery GitHub Actions | PASS (recorded in final gate confirmation below) | The initial local recheck predated manual dispatch; see the final confirmation for the successful runs on the integration SHA. |

The test environment emitted an existing optional SoX warning. Rendering, tests, and silent delivery validation succeeded without SoX. Blender 5.2.1 was installed and executed successfully using the approved unsandboxed WSL path. GPU use was not established.

## Remaining limitations and merge recommendation

- P1: none identified by the executed tests, mixed renders, and sampled-frame review.
- P2: no same-host legacy full Blender render timing was captured; only requested Blender image counts were compared. Studio Light still has a small color-managed canvas difference between Blender and Manim.
- Narration QA is not applicable to the silent previews; learner comprehension remains untested.
- The initial gate snapshot below was superseded by the final manual Actions runs and user-confirmed full-motion review recorded at the end of this report.

Recommended stacked PR sequence: merge PR #8 (V14.3) into `main`; then PR #9 (V14.4) into `main`; then retarget PR #10 from V14.4 to `main`, allow the base-change CI to complete, and review/merge V14.5. This integration branch is validation evidence only; it does not authorize any PR merge. Do not merge `main` as part of this task.

## Final integration recheck — 2026-10-15

The local code/runtime checks below were performed against the source tree at `c06dc917e13f22f82337cd825a9899bad8637407`; only this QA document changed in `f54d352079661f65a67d13b5efcfef40454bb244`. This final gate recheck is recorded on `f54d352079661f65a67d13b5efcfef40454bb244`.

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
| Remote Actions | AI Trace PASS; Education/Battery pending at this snapshot | [AI Trace run #139](https://github.com/hinoonyaso/make_simulation/actions/runs/38742184692) succeeded on `6a6cc9a`. The Education and Battery runs were started after this snapshot; their final results are recorded below. |
| `git diff --check` | PASS | Rechecked after this report update, before commit. |

`FULL_MOTION_REVIEW=PASS` as of 2026-10-15: the user watched both 24-second previews at 1× and confirmed they were acceptable. This completes the full-motion review; learner comprehension remains untested. The previews are silent, so narration QA is `NOT APPLICABLE`. Sampled transition details and the remaining non-severe Studio Light color-managed shift are documented above.

## Final release-gate confirmation — 2026-10-15

Both manually dispatched workflows ran on the required integration ref and exact validation SHA `cb63734cf5def80cb9ffbaa1a67d73805a5de208`:

| Workflow | Result | Run |
|---|---|---|
| Education renderer smoke | PASS; CPU regression, asset/catalog and plan validation, Manim and gear previews, caption/timeline checks and full media decode all succeeded. | [Run #61](https://github.com/hinoonyaso/make_simulation/actions/runs/38746503964) |
| PyBaMM battery education smoke | PASS; real SPM solve, early-cutoff event, solver/result validation, sparse plan, Manim preview, provenance and media validation all succeeded. | [Run #31](https://github.com/hinoonyaso/make_simulation/actions/runs/38746531603) |
| AI Trace reproducibility | PASS on the same SHA. | [Run #140](https://github.com/hinoonyaso/make_simulation/actions/runs/38742551424) |

The user confirmed full 1× playback acceptance of both Battery previews. Their verified media hashes remain Technical Dark `669b20b6e2d76eba936241d28f47ca595493e681b661f97ac8e122b7a1359fb8` and Studio Light `d42259957911d06be8f01d996b14cc4ac886668e156438bae6005a07ea9f25d2`. No rerender was needed.

**Release gate: READY FOR SEQUENTIAL PR PREPARATION.** GitHub currently reports PR #8 open/Ready for Review/mergeable on `main`; PR #9 open/Draft/mergeable on `main`; PR #10 open/Draft/mergeable on `v14.4-bearing-visual-excellence`. No PR or `main` was changed or merged. Preserve the order #8 → #9 → #10; after #9 merges, recheck #10's base and diff and retarget to `main` if appropriate, then wait for fresh CI.

The integration-only `84ae4ff` camera-background fix remains absent from the current PR #8, #9, and #10 heads. After the PR sequence, compare the merged Battery scene with `84ae4ff`; if the helper and its `setup_scene()` call are still absent, create a minimal follow-up PR containing only that change and rerun both profile transition checks. Do not cherry-pick the integration merge or modify the existing PRs for this gate. Learner comprehension and narrated/audio acceptance are outside these silent preview checks and remain untested/not applicable, respectively.

## Post-gate PR #8 merge check — 2026-10-15

After the release-gate confirmation above, the user approved and PR #8 was merged into `main` using a merge commit. Main is now `e64d848a6945c1e60efc329bd714b40b473eca0e` ([merge commit](https://github.com/hinoonyaso/make_simulation/commit/e64d848a6945c1e60efc329bd714b40b473eca0e)). Post-merge [Education Renderer run #62](https://github.com/hinoonyaso/make_simulation/actions/runs/38748341541) and [AI Trace run #141](https://github.com/hinoonyaso/make_simulation/actions/runs/38748341519) both passed on that SHA. Battery workflow was not dispatched on the merge commit; its latest successful integration-ref run is #31 above, on `cb63734`.

PR #9 is now Ready for Review, based on `main`, and GitHub reports it mergeable. Comparing its head to the new main shows two PR commits and eight changed files. The user watched the 84-second R6 preview at 1× and confirmed PASS; the PR description now records that result. The preview is available locally at `/home/sang/make_simulation-r6/pilots/v13_education/output/r6_visual_qa/r6-final/preview.mp4` (960×540, 30 fps, H.264; SHA-256 `c44219f83365482ef12e0223994b59c0022ff849a83e8c59655d9480109bd457`). Education Renderer [run #63](https://github.com/hinoonyaso/make_simulation/actions/runs/38748909304) passed on the current PR head `b1e45be`. The earlier successful head checks also passed; no new PR commit was added. 1080p rendering and narrated audio QA remain pending.

PR #10 remains Draft and based on `v14.4-bearing-visual-excellence`; recheck and retarget its base only after PR #9 is merged. The integration-only `84ae4ff` camera-background fix is still absent from current `main`; handle it as the minimal follow-up PR described above if it remains applicable after the sequence.
