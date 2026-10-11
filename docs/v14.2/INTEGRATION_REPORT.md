# V14.2 Integration Report

## Implemented

- Optional locked PyBaMM 26.10.0.0 dependency group and allow-listed SPM/Chen2020 CPU adapter with config/result schemas and validation.
- Separate solver CLI and renderer `--solver-result` input; plan-only does not execute the solver.
- V9 `battery-simulation-trace/v1` dispatch with result/config/CSV integrity checks.
- Battery lesson registration, CC0 18650 educational concept asset, Blender scene, and Manim voltage trace.
- 24-second / 720-frame mixed lesson and 6-second Manim-only solver smoke.
- Event-safe PyBaMM sample handling and runtime-discovered Blender Eevee/output enum handling.
- Blender-owned beat boundary cleanup in the Manim scene to prevent stale charts from leaking into a later Manim beat.

## Verification evidence

- Corrected-source commit `f6dd301938fe6aa29986b5f1d2210d0d54a40b13` passed Battery Actions [run 38129252744](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252744), including both solver smoke and mixed-preview jobs.
- The mixed artifact used Blender 5.2.1 LTS and asset `edu.mechanical_primitives.v1`; the asset report and renderer provenance agree on solver run `mixed-ci-38129252744-1`, 361 samples, 1800 s, and the CSV SHA-256.
- Corrected artifact video: 24.0 s, 960×540, H.264, 30 fps, 720 frames, silent; SHA-256 `d1d0fdab89e3506986a602224faaacff1737f92cf9e9ff2a89d81ebb0eff0e4a`. Manifest, delivery, caption timing and full decode passed.
- Frame review found a stale graph behind the final summary; the fix clears Manim state during Blender-owned beats and recreates the title for each Manim beat. Corrected-source artifact frames were reviewed at renderer boundaries; the overlap is gone and the final information frame is present. The video SHA-256 is recorded above.
- Actual normal and event-termination PyBaMM outputs both pass `validate_battery_result.py`. Event run: 7200 s requested, 3606.549305848102 s observed, 62 samples, result SHA-256 `23ca1050317fe899e43ce0c5ebbdf42dab3c5438d1d3e7dd1cb8676bffcb5b3e`.
- 207 unit tests, `compileall`, 39-entry asset registry, six education catalog/generated asset checks, style checks for both battery scenes, and `git diff --check`: PASS.
- Education Renderer [run 38129252723](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252723), AI Trace [run 38129252696](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252696), and Engineering Simulation [run 38129252770](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252770) passed.

## Render cost and remaining limits

Corrected CI run 38129252744 measured Blender at 4430.12 s (about 73 min 50 s) and Manim at 10.62 s. Total workflow elapsed time was about 76 min 29 s; FFmpeg composition time was not separately logged. Beat-aware sparse Blender rendering is a future optimization; this change does not redesign the renderer.

Blender could not be started in the local WSL session; corrected-source CI is the evidence for Blender 5.2.1 asset loading and scene output. The CC0 18650 mesh is educational geometry, not a Chen2020 cell model. TTS, 1080p output, normal-speed full-length audio review, and narrated final delivery were not requested or verified. PR #7 has not been merged to `main`.
