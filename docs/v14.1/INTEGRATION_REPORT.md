# V14.1 Integration Report

## Base and branch

V14 PR #5 (`2dcfafbd5c95a2b38ce609c5933f5dbfb1192a96`) was verified with successful Education Renderer Smoke run `38112231680` and AI Trace Reproducibility run `38112231682`, resolved review threads, and merged into `main` as Merge Commit `e6c12505f5bd052c9b14bb7f92a0b2ab0bbb9529`. This V14.1 branch was created from the V14 head because Git SSH fetch is unavailable in this WSL session; the V14 head is the merge commit's parent. Before opening a PR, push the branch and verify GitHub computes a V14.1-only diff against updated `main`.

## Implementation

- Registered `spur_gears` for both Manim and Blender without adding topic-specific CLI routing.
- Added the 80-second mixed lesson spec while preserving the original 12-second Manim smoke.
- Added pure shared frame planning for continuous one-turn/half-turn animation and tests for half-open frame boundaries.
- Added a Blender scene that opens the registered asset in memory, clears its embedded generator preview actions, validates geometry centers/hubs, creates temporary axis pivots, renders the full shared timeline, and writes asset-load evidence.
- Updated generic composition to pass the shared renderer context to Blender and reject a missing or mismatched asset report before asserting the Blender asset was loaded.
- Compatibility hardening declares Blender context/report requirements per registry entry. Bearing keeps its legacy Blender CLI and does not need a gear report; gear rendering still requires strict load evidence. The gear formula scene no longer uses `MathTex` and has a dedicated five-second Manim smoke.
- Extended CI plan validation for the full lesson; Blender is not installed or runnable in the current Linux CI workflow, so this does not replace local Blender integration evidence.

## Local mixed-renderer validation

- V14 PR base CI: both runs listed above succeeded before V14.1 changes.
- Updated PR CI: [AI trace reproducibility run 38115491923](https://github.com/hinoonyaso/make_simulation/actions/runs/38115491923) and [Education renderer smoke run 38115491945](https://github.com/hinoonyaso/make_simulation/actions/runs/38115491945): PASS. Both jobs completed successfully for commit `fefd763`.
- Actual mixed render: `pilots/v14_education/output/gear-v14.1-final-fixed/preview.mp4`, rendered on 2026-10-11 with Blender 5.2.1 LTS, Manim Community 0.21.0, and FFmpeg. The sandboxed command runner could not see WSL interop sockets, while the approved elevated runner could; `cmd.exe /c ver` and Windows Blender both ran. The earlier socket failure was a sandbox visibility issue, not an unavailable Blender installation. The complete 11 MB run directory is saved in the shared checkout and is ignored by Git.
- Delivery validation: PASS — H.264, 960×540, 30/1 fps, 2,400 frames, 80.0 seconds, 16 caption cues, full decode. Video SHA-256: `559c54ced14f973614ba6ef529446d5f8e79ca177c62509b76ec846311390cad`.
- Blender asset report: PASS — actual `.blend` loaded; all four registered mesh objects present; source asset hash matched; temporary pivots were checked over 18 sampled frames; maximum mesh-centroid error was `3.06e-8 m` against `0.001 m` tolerance; centers remained fixed; source `.blend` was not modified.
- Mixed visual review: Blender frames and the Manim pitch-point transition were inspected from the rendered MP4. The Manim navy background is intentional, not a black-video interval. Automated black/freeze review and uninterrupted full-length normal-speed viewing were not performed; the production report keeps those items pending.
- Scene style: PASS for `pilots/v14_education/blender/spur_gears_scene.py` and `pilots/v14_education/manim/spur_gears_scene.py`.
- Regression: PASS — all 195 unittest tests with the locked `sim-render`, `sim-math`, `sim-can`, and `sim-motor` groups installed. `compileall` over `core scripts tests assets/education`: PASS. Asset registry: PASS, 39 entries; education asset validation: PASS, 6 generated models.
- Delivery recheck: PASS with 960×540 preview thresholds, 30 fps, shared timeline and caption timing, and FFmpeg full decode. The default 1080p delivery threshold correctly rejects this preview-sized file.
- Black-frame scan: FFmpeg `blackdetect` reported no black intervals. `freezedetect` reports held portions in the storyboard, so this signal alone is not treated as a defect. Representative transition and motion frames were inspected; uninterrupted 80-second normal-speed playback review remains pending.
- TTS/Whisper and 1080p output were not requested and were not run. The output is a silent 960×540 review preview, not a narrated master.

## Compatibility hardening validation

For the compatibility follow-up, local checks passed: `tests.test_education_renderer_registry` (33 tests), full unittest discovery (200 tests), `compileall`, asset registry validation (39 entries), education asset validation (39 registry entries / 6 catalog models / 6 generated assets), plan-only for Bearing, full spur gears, and ratio smoke, and style checks for both Bearing and spur-gear Blender/Manim scenes. A real Blender 5.2.1 Bearing single-frame render completed at 960×540 without `--context`; a 12-second gear Manim smoke decoded successfully; the new ratio smoke rendered 150 frames (5 seconds) at 960×540/30 fps and passed manifest, timeline, caption timing, and full decode validation. Local output is saved under `pilots/v14_education/output/v14.1-compatibility-smokes/` in the shared checkout (ignored by Git).

The compatibility smoke is not a replacement for the existing 80-second mixed render. GitHub Actions for the follow-up commit must be recorded after the pushed commit's workflow runs finish; no remote result is implied by local validation.

This confirms the Blender + Manim mixed preview path locally. It does not validate full-motion playback end-to-end, narration, 1080p delivery, or gear contact mechanics.
