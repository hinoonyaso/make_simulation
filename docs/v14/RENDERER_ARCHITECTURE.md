# V14 Renderer Architecture

## Decision

The production CLI stays generic and selects topic-specific code through a frozen Python allow-list (`EducationRenderer`). A Lesson Spec selects only a canonical registered topic and beat tools (`M`/`B`); it cannot supply Python module paths, Scene class names, or shell commands. The registry binds those trusted identifiers to repository-relative files and a catalog Asset ID.

This was chosen over adding `if topic == ...` blocks to `produce_lesson.py`, because the V13.5 CLI hard-coded the bearing Blender script, Manim script, and class. A plug-in import path from JSON was rejected because it would turn lesson data into executable code. The trade-off is that each new topic requires one explicit registry entry and its scenes; common composition and QA remain shared.

## Data flow

```text
education-lesson-spec/v1
  → LessonSpec/schema checks
  → Education Planner
  → Renderer Registry + asset/hash resolution
  → Blueprint/backend implementation preflight
  → required local runtime preflight
  → registered Blender and Manim Scenes
  → shared V12 integer-frame timeline composition
  → V9 manifest/media validation + caption and delivery QA
  → renderer provenance and production report
```

`renderer_registry.py` owns topic aliases, scene/class allow-list, supported renderer modes, Blueprint capabilities, Asset IDs, and optional trusted context builders. Blender-specific context and load-report requirements are declared per renderer (`blender_context_required`, `asset_load_report_required`), rather than inferred from topic in the shared CLI. Bearing keeps the legacy `--manifest`/`--timeline` interface; the gear scene opts into shared context and a strict asset-load report. `blueprint_registry.py` remains renderer-neutral and declares which backends can express each reusable visual concept. A Blueprint's existence is not enough: the selected topic must also declare a scene implementation for that backend.

Asset resolution reads `assets/education/catalog.json`, confines paths to the repository, checks the asset and JSON sidecar, and verifies the sidecar's `source_sha256`. The resulting context includes the actual catalog metadata for renderers that request it. Provenance marks `asset_loaded_by_renderer` true only when a renderer requiring evidence produced a validated load report; a legacy renderer without that report is not credited with an observed import.

The V9 `visual_manifest.json` remains the only beat/narration/media list. `core/mechanism/timeline.py` remains the frame-range source. Renderer outputs are cut using each beat's matching phase ID and half-open integer-frame range; the composition code does not build a second storyboard.

## Failure behavior

- Unknown topic, unsupported `tool`, missing Scene/class, unknown or unsupported Blueprint, asset mismatch, missing asset, or hash mismatch: fail as `BLOCKED` before rendering.
- Manim runtime missing: fail before run directory creation.
- Blender required but unavailable or failing: fail; do not substitute Manim.
- `--manim-only` with any Blender-required beat: fail before creating output.
- Plan-only: validate deterministic source contracts and assets, but never start a renderer, TTS service, or external command.
- Renderer and media validation failures propagate. Provenance marks media validation `PASS` only after the CLI delivery gate succeeds.
- After the final delivery gate, `renderer_provenance.json` stores the actual final media filename and SHA-256 together with the validated timeline hash and observed frame range. With TTS these all refer to `final.mp4`; a failed final delivery gate leaves provenance pending rather than claiming `PASS`.

## Spur-gear ideal pitch-point illustration

`core/education/gear_kinematics.py` derives pitch radii `rᵢ = mZᵢ/2`, the external center distance `r₁+r₂`, and the common pitch point. For angular velocities it applies `v = ω × r` at that common point. This gives `ω₂/ω₁ = -Z₁/Z₂`; both contact-point tangential velocity vectors are equal, including when the input rotates in reverse. A zero input returns zero velocity and no direction arrow.

The Manim scene marks that ideal pitch point, pitch circles, signed angular directions, and equal tangent velocity. This is a kinematic teaching diagram: the polygon teeth are not involute profiles and the scene calculates no actual tooth contact, force, friction, or solver result.

The ratio-only Manim scene uses ordinary text glyphs for ratio expressions and does not require a system LaTeX installation. `examples/education/gear_ratio_smoke.json` exercises a 5-second, 150-frame formula sequence in local and CI smoke rendering.

## Solver boundary

The optional `context_builder` is trusted deterministic domain arithmetic over validated asset metadata; it is not a physical Solver. A future Solver Adapter belongs before rendering and must supply validated outputs and evidence provenance. Renderer scenes must not invent or re-run solver values.
