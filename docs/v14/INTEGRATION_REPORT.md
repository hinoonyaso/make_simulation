# V14 Integration Report

## Baseline findings

At V13.5, `scripts/produce_lesson.py::render` hard-coded `pilots/v13_education/blender/bearing_scene.py`, `pilots/v13_education/manim/bearing_scene.py`, and `BearingLessonScene`. `plan_lesson` checked that a Blueprint name existed but did not verify the topic/backend had an implementation. Lesson beats were also mutated while evidence fields were being attached.

## V14 implementation

- Added `core/education/renderer_registry.py` with an allow-listed topic, Scene/class, renderer modes, Blueprint support, Asset ID and validated metadata context.
- Routed renderer resolution through the planner and made unsupported topic/backend/Blueprint/asset conditions fail before rendering.
- Generalized `produce_lesson.py` scene selection, runtime preflight, composition, context handoff and renderer provenance while retaining old CLI options and V13 environment aliases.
- Registered the existing bearing scenes and smoke alias, then registered the 20T:40T spur gear Manim smoke and `edu.spur_gears_20_40.v1` asset.
- Preserved V9 manifest and V12 integer-frame timeline. Plan generation now copies beat rows rather than mutating the loaded Lesson Spec.

## Gear evidence boundary

The tracked gear asset and metadata sidecar are checked by file hash. The Manim scene reads tooth counts/module/center distance from that sidecar context, validates the ideal relation, and animates a schematic pair. It does not load the `.blend` mesh. The ratio, pitch point and tangent velocities are deterministic ideal kinematics, not solver output. Blender mesh use and a full 60–90 second gear lesson remain V14.1 work.

## Final review fixes

- Added `core/education/gear_kinematics.py` for the external pair's pitch radii, common pitch point, signed angular velocities, and no-slip tangent velocities. Scene guides point out the ideal pitch circles/P, opposite angular directions, and equal tangent velocity. Reverse input preserves the relation; zero speed yields no direction arrow.
- After narration mux and final delivery validation, the provenance `output`, SHA-256, media-validation status, frame range, and timeline hash now describe the same final video. Preview and final dimensions continue to be validated by the selected mode's requirements.
- Mock tests cover all four preview/TTS combinations, output existence, matching provenance/report paths and hashes, output dimensions, and a failed final-delivery validation remaining non-PASS.

## Verification record

Local verification on the V14 branch:

- `python -m unittest discover -s tests -v`: **189 tests passed** (185 existing plus 4 new).
- `python -m compileall -q core scripts tests pilots/v13_education pilots/v14_education`: passed.
- `python core/visual-assets/asset_registry.py validate`: 39 assets passed.
- `python scripts/acquire_education_assets.py --validate`: 39 registry entries, 6 catalog models, and all 6 generated asset hashes passed.
- Spur-gear geometry tests verified `Z₁=20`, `Z₂=40`, `ω₂/ω₁=-0.5`, shared pitch-point distances, equal tangent velocities, opposite angular signs, reversed input, and zero-speed handling.
- Bearing and spur gear `--plan-only` runs: passed; both resolve to their registered renderers and assets.
- Spur gear Manim smoke output: `pilots/v14_education/output/v14-finalfix-gear4/preview.mp4`, 960×540, H.264, 30 fps, 360 frames / 12.0 seconds, silent. `ffprobe -count_frames` matched the timeline's half-open range `[0, 360)`. Rendered frames were inspected for pitch-point/velocity readability and subtitle overlap. This generated, ignored file is local and is not a public repository link.
- `validate_visual_manifest.py --require-media`: passed.
- `validate_delivery.py --min-width 960 --min-height 540 --fps 30 --timeline ... --caption-timing ... --full-decode`: passed; full decode succeeded.
- `check_scene_style.py pilots/v14_education/manim/spur_gears_scene.py`: passed.
- Workflow YAML syntax and `git diff --check`: passed.

Hosted PR checks for commit `95dc1342f7d1423f141d9f7e792b9ab76f50a190`:

- [Education Renderer Smoke, run 38112112952](https://github.com/hinoonyaso/make_simulation/actions/runs/38112112952): **success**. Full unittest, asset/plan validation, both Manim renders, media validation and artifact upload completed.
- [AI Trace Reproducibility, run 38112113006](https://github.com/hinoonyaso/make_simulation/actions/runs/38112113006): **success**.
- Education smoke artifact `education-renderer-38112112952-1` was uploaded and is available from the workflow run's Artifacts section.

The local Manim run emitted its existing optional SoX-not-found warning; the silent render completed and decoded successfully. TTS, 1080p production, and Blender gear mesh rendering are outside this fix. The generated local MP4 is ignored by Git and is not a public repository link.
