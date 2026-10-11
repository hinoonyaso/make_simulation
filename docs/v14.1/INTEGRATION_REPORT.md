# V14.1 Integration Report

## Base and branch

V14 PR #5 (`2dcfafbd5c95a2b38ce609c5933f5dbfb1192a96`) was verified with successful Education Renderer Smoke run `38112231680` and AI Trace Reproducibility run `38112231682`, resolved review threads, and merged into `main` as Merge Commit `e6c12505f5bd052c9b14bb7f92a0b2ab0bbb9529`. This V14.1 branch was created from the V14 head because Git SSH fetch is unavailable in this WSL session; the V14 head is the merge commit's parent. Before opening a PR, push the branch and verify GitHub computes a V14.1-only diff against updated `main`.

## Implementation

- Registered `spur_gears` for both Manim and Blender without adding topic-specific CLI routing.
- Added the 80-second mixed lesson spec while preserving the original 12-second Manim smoke.
- Added pure shared frame planning for continuous one-turn/half-turn animation and tests for half-open frame boundaries.
- Added a Blender scene that opens the registered asset in memory, clears its embedded generator preview actions, validates geometry centers/hubs, creates temporary axis pivots, renders the full shared timeline, and writes asset-load evidence.
- Updated generic composition to pass the shared renderer context to Blender and reject a missing or mismatched asset report before asserting the Blender asset was loaded.
- Extended CI plan validation for the full lesson; Blender is not installed or runnable in the current Linux CI workflow, so this does not replace local Blender integration evidence.

## Validation evidence and blockers

- V14 PR base CI: both runs listed above succeeded before V14.1 changes.
- V14.1 plan-only for the full spec: PASS locally; 80 seconds, 30 fps, 2,400 frames, Blender+Manim modes, asset hash PASS, ideal ratio −0.5.
- Focused education renderer registry/keyframe tests: run locally; see final task report for exact count.
- Actual Windows Blender executable found at `/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe`, but launch from this WSL session fails with `UtilBindVsockAnyPort:309: socket failed 1`. Blender runtime version, asset load, Blender render, mixed composition, 80-second MP4, subtitles on the MP4, and full decode are therefore not yet verified in this session.
- TTS/Whisper and 1080p output are intentionally out of scope.

Do not report V14.1 as production-complete until the executable is run from an environment with working Blender access and all required video checks pass.
