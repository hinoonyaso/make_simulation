# Unified Visual Design System — Visual QA Report

## Result summary

This report separates source checks, real render checks and human-review limits. No 10/10 overall score is claimed. The inspected still frames showed no P0/P1 blocker or high-severity visual defect; the 84-second videos were rendered and fully decoded, but not watched end-to-end at normal speed.

## Before / after evidence

| Sample | Before evidence | Updated render | Finding |
|---|---|---|---|
| Bearing 6204 | Local R5 preview frame at 20 s from `/home/sang/make_simulation/pilots/v13_education/output/lessons/bearing-v13-preview-r5/bearing_blender.mp4` | `pilots/v13_education/output/lessons/v145-bearing-design/bearing_studio_light_frame_0600.png` and `bearing_technical_dark_frame_0600.png` | Previous upper-right panel crossed into the bearing silhouette. New profile render keeps the label group to the right; light/dark backgrounds and semantic highlights differ as selected. Ball material was brightened in Studio Light to separate balls from the floor. Compared frames are 960×540. The before artifact is local-only and untracked. |
| Spur gears 20T:40T | Local V14.1 preview at 1 s from `/home/sang/make_simulation/pilots/v14_education/output/gear-v14.1-final-fixed/preview.mp4` | `pilots/v14_education/output/lessons/v145-gear-design/gears_preview.png` | Same registered asset and gear relationship. New Light profile reduces the older washed-out white gear surfaces and makes input/output semantic colors more distinct. Still frame only; no gear motion comparison was made. |
| Bearing Manim | Existing dark semantic palette and fixed family behavior | Both profile renders under `pilots/v13_education/output/lessons/v145-bearing-design/manim_{technical_dark,studio_light}/.../BearingLessonScene.mp4` | Korean text rendered in both profiles; semantic accent contrast is adapted per profile. Static frame at 12 s was inspected. |
| TEB reference | Existing locally rendered pilot at `/home/sang/make_simulation/pilots/01_teb_reference/output/pilot_teb_reference.mp4` | Existing reference only; no source or render changes | Inspected 2 s Blender still and 18 s Manim still to compare the bright 3D studio / dark information scene pairing. The source video remains in the original worktree and was read-only. |
| Battery 18650 | Existing report: `docs/v14.2/BATTERY_EDUCATIONAL_QA.md` records a past Blender 5.2.1 still and mixed preview CI run. | No new render | Local solver invocation returned `PyBaMM battery solver is unavailable; install with uv sync --group sim-battery`; no current battery still was produced. The prior CI evidence is not represented as a render from this branch. |

The new local output videos and stills are covered by the project's ignore rules and are not included in the PR. Their SHA-256 values at review time:

- Bearing Manim Technical Dark, 84 s: `68e27f4fbd3ab662cbe0d08f3478999c0c4f19556c03c6bd46f22f6e6eb77dd9`
- Bearing Manim Studio Light, 84 s: `1d06e09e2e6169de82644310c300840131d452368083ba92de03d9638e26d81c`
- Bearing Blender Technical Dark still, frame 600: `d5c2bbca93bb4f8b8b06a3496c1a274d5802eeb0a55d9b6652d0c9efc8769f95`
- Bearing Blender Studio Light still, frame 600: `05f8bb6a79c90cebf4a83905148afcdabfad33c30f3fece5de938d6031550f55`
- Gear Blender Studio Light still: `5928d273bf8a3b352a03b1ae5b65053a45033b3acc41f54cf2abe0e03450d3d1`

## Automated checks

| Check | Result |
|---|---|
| Full unittest suite | PASS — 232 tests |
| Python compileall | PASS — `core scripts tests assets/education pilots/v13_education pilots/v14_education` |
| Token schema / contrast | PASS — Studio Light 12.019:1 primary and 6.683:1 secondary; Technical Dark 17.620:1 primary and 6.191:1 secondary |
| Korean font coverage | PASS — Blender resolver found NanumGothic TTF; Manim family NanumGothic covers requested Hangul |
| Scene style | PASS — all six V13/V14 Blender and Manim scene files |
| Bearing Manim encode/decode | PASS — each profile 960×540, H.264, 30 fps, 2520 frames, 83.999 s; FFmpeg full decode passed |
| Render metrics | Technical sampling PASS; visual verdict remains `INCOMPLETE` by design. Dark-frame and brightness-jump candidates: none. Long identical-frame candidates at 0–8 s, 18–59 s, 60.25–68.25 s, 68.5–70.75 s, and 71–84 s correspond to the Manim scene intentionally holding its canvas while Blender beats play and holding the final summary; they are not classified automatically as defects. |
| Actual Blender | PASS — Blender 5.2.1 rendered and saved Bearing stills for both profiles and a Gear still for Studio Light; each inspected visually at 960×540. Windows Blender was invoked from WSL. |
| Battery actual Blender | NOT RUN — PyBaMM dependency unavailable locally, so no validated solver result could be supplied |
| TEB current-source rerender | NOT RUN — inspected the existing local reference MP4 only; no change made to that scene |
| Normal-speed video/audio review, 1080p render, learner comprehension | NOT RUN — the generated Manim output is silent; still inspection and full decode do not establish these results |

Commands used:

```bash
uv run python -m unittest discover -s tests -q
uv run python -m compileall -q core scripts tests assets/education pilots/v13_education pilots/v14_education
uv run python scripts/validate_visual_design.py --all-scenes
uv run python scripts/validate_visual_design.py --blender-text '한글 베어링 부품' --manim-text '한글 그래프 수식'
uv run python scripts/analyze_visual_render.py <rendered-preview.mp4> --report <visual-metrics.json>
```

## Render integration defects found and fixed

1. Setting `scene.world.color` did not change the rendered background for worlds using nodes. A shared `apply_world_profile()` now sets both the legacy value and the actual World Background shader color/strength.
2. WSL did not forward `EDU_VISUAL_PROFILE` to Windows Blender. The generic lesson runner now sends an explicit `--visual-profile` argument, accepted by all registered V13/V14 Blender lesson scenes.
3. Studio Light's bearing-ball color was too close to the background under the actual 540p render. A profile-specific neutral ball color increases separation without changing geometry or motion.
4. The first repeat-frame heuristic emitted one candidate per duplicate 4-fps sample, producing noisy reports. It now groups identical runs and reports only runs meeting a configurable minimum duration; the output remains candidate-only.

## Human review state and open risks

- Still review: PASS for the inspected Bearing/Manim and Gear images; no inspected frame had clipping, overlap, or illegible Korean text at 960×540.
- Motion continuity, camera feel, beat-to-narration synchronization, full-scene cross-renderer cut quality and audio: `INCOMPLETE`. Manim output was fully decoded but not watched at normal speed; no narration was generated.
- Battery scene and current TEB code were not rendered from this branch. Battery is blocked by missing optional PyBaMM; TEB's local original render was only used as a visual reference.
- Blender emits a Blender 5.2 deprecation warning for `Material.use_nodes` in Bearing's emission-material helper; it did not fail rendering, but should be migrated before Blender 6 compatibility is required.
- No GitHub Actions run or PR validation has been reported yet for this feature branch.
