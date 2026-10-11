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

The tracked gear asset and metadata sidecar are checked by file hash. The Manim scene reads tooth counts/module/center distance from that sidecar context, validates the ideal relation, and animates a schematic pair. It does not load the `.blend` mesh. The ratio and center distance are deterministic calculations, not solver output. Blender mesh use and a full 60–90 second gear lesson remain V14.1 work.

## Verification record

Local verification on the V14 branch:

- `python -m unittest discover -s tests -q`: **185 tests passed**.
- `python -m compileall -q core scripts tests pilots/v13_education pilots/v14_education`: passed.
- `python core/visual-assets/asset_registry.py validate`: 39 assets passed.
- `python scripts/acquire_education_assets.py --validate`: 39 registry entries, 6 catalog models, and all 6 generated asset hashes passed.
- Bearing and spur gear `--plan-only` runs: passed; both resolve to their registered renderers and assets.
- Spur gear Manim smoke output: `pilots/v14_education/output/spur-gears-smoke-final3/preview.mp4`, 960×540, H.264, 30 fps, 360 frames / 12.0 seconds, silent. `ffprobe -count_frames` matched the timeline's half-open range `[0, 360)`. This generated, ignored file is local and is not a public repository link.
- `validate_visual_manifest.py --require-media`: passed.
- `validate_delivery.py --min-width 960 --min-height 540 --fps 30 --timeline ... --caption-timing ... --full-decode`: passed; full decode succeeded.
- `check_scene_style.py pilots/v14_education/manim/spur_gears_scene.py`: passed.
- Workflow YAML syntax and `git diff --check`: passed.

The local Manim run emitted its existing optional SoX-not-found warning; the silent render completed and decoded successfully. GitHub Actions for this V14 branch has not run yet; its result must be recorded from the actual PR checks. TTS, 1080p production, and Blender gear mesh rendering are outside V14 scope. The generated MP4 is ignored by Git and exists only in the working environment.
