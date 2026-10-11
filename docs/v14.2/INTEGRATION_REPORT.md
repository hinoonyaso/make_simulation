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

- Battery Actions [run 38122266473](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266473): both solver smoke and mixed-preview jobs succeeded on the pre-cleanup source at `02a1a57e01e927c6956aafc82eb30b48d2811f5c`.
- The mixed artifact used Blender 5.2.1 LTS and asset `edu.mechanical_primitives.v1`; the asset report and renderer provenance agree on solver run `mixed-ci-38122266473-1`, 361 samples, 1800 s, and the CSV SHA-256.
- Artifact video: 24.0 s, 960×540, H.264, 30 fps, 720 frames, silent; CI SHA-256 `61dd936667f7d56764519f52dfe4a2b1fbd32d8afc209cd02aa1a8da60972037`. Full decode and caption timing passed.
- Frame review found a stale graph behind the final summary. After the Manim scene cleanup, a local rerender/recomposition using the CI Blender segment produced SHA-256 `05823bffa2d7a939731cc75ab152dace82cab107f4cc86910f185b67cb0f1af8`; it passes `validate_visual_manifest.py --require-media`, `validate_delivery.py --fps 30 --timeline ... --caption-timing ... --full-decode`, and visual sampling at renderer boundaries. The corrected source still needs its own remote CI run.
- Actual normal and event-termination PyBaMM outputs both pass `validate_battery_result.py`. Event run: 7200 s requested, 3606.549305848152 s observed, 62 samples, result SHA-256 `f2631a1c28111bf4e19af646a6c82978990f36e9025480ee107235b22d43c66a`.
- 207 unit tests, `compileall`, 39-entry asset registry, six education catalog/generated asset checks, style checks for both battery scenes, and `git diff --check`: PASS.
- Education Renderer [run 38122266490](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266490), AI Trace [run 38122266514](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266514), and Engineering Simulation [run 38122266495](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266495) passed.

## Render cost and remaining limits

The successful CI run measured Blender at 4965.80 s (about 82 min 46 s) and Manim at 12.66 s. Total workflow elapsed time was about 84 min 39 s; FFmpeg composition time was not separately logged. Beat-aware sparse Blender rendering is a future optimization; this change does not redesign the renderer.

Blender could not be started in the local WSL session. The successful CI artifact proves Blender 5.2.1 asset loading and scene output for the prior source. The locally corrected composite reused that Blender segment; the corrected source needs a fresh CI run. TTS, 1080p output, normal-speed full-length audio review, and narrated final delivery were not requested or verified. V14.2 is not merged to `main`; PR #7 remains Draft until the corrected-source checks pass.
