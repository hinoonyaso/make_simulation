# V14 Generic Education Renderer

V14 adds an allow-listed Renderer Registry to the `education-lesson-spec/v1` flow. PR #5 was merged into `main` by Merge Commit `e6c12505f5bd052c9b14bb7f92a0b2ab0bbb9529`. The registry includes `ball_bearing` and the 20T:40T `spur_gears` topic. V14.1 mixed Blender/Manim production is being developed on `v14.1-gear-blender-education`; it is not yet a completed or reviewed Blender video.

## Commands

```bash
uv run python scripts/produce_lesson.py --spec examples/education/bearing.json --plan-only
uv run python scripts/produce_lesson.py --spec examples/education/spur_gears.json --plan-only
uv run python scripts/produce_lesson.py --spec examples/education/spur_gears.json --preview --manim-only
uv run python scripts/produce_lesson.py --spec examples/education/gear_ratio_smoke.json --preview --manim-only
uv run python scripts/produce_lesson.py --spec examples/education/spur_gears_full.json --plan-only
```

Planning validates the V9 manifest contract, the V12 integer-frame timeline, the topic-to-renderer allow-list, Blueprint/backend capability, the registered Scene and class, the education Asset Catalog entry and its SHA-256 sidecar. `--plan-only` does not call Blender, Manim, TTS or external services. Rendering probes the required local runtime before it creates output. A Blender beat cannot be silently converted to a Manim beat by `--manim-only`.

## Add a topic

1. Add or identify a redistributable education model in `assets/education/catalog.json`, including a tracked `.blend` file and matching metadata sidecar when the model is a Blender asset. The catalog ID and metadata source hash must agree.
2. Create a Manim scene file and a top-level `Scene` class. The scene reads `EDUCATION_MANIFEST_PATH`, `EDUCATION_TIMELINE_PATH`, and `EDUCATION_RENDER_CONTEXT_PATH`. Preserve the V9 beat list and V12 frame intervals.
3. If the topic has 3D beats, create a Blender script that accepts the common `--manifest`, `--timeline`, `--output`, width/height/fps and sample options. Declare any extra context or load-report contract in the renderer registry; the generic CLI passes `--context` and requires `asset_load_report.json` only for renderers that declare those requirements. The existing Bearing Blender scene uses the legacy interface.
4. Register a canonical topic, optional aliases, Scene file/class, asset ID, supported renderer modes, and per-renderer Blueprint implementations in `core/education/renderer_registry.py`. A trusted `context_builder` may derive non-solver results from validated asset metadata; Python paths and commands are never accepted from a Lesson Spec.
5. Add an `education-lesson-spec/v1` JSON file under `examples/education/`; include unique beat and phase IDs, duration, one supported renderer per beat, evidence type, and any relevant Blueprint.
6. Run plan-only first, then a short preview. Add topic-specific registry, failure, timing, and render tests. CI never requires Blender for the Manim-only gear smoke.

To add a future Blender Scene, register its in-repository path and `blender` mode; the common CLI chooses it from beat `tool: "B"` without topic-specific CLI changes. It will still need its own smoke and media validation before it can be called supported.

## Current support boundary

- `ball_bearing`: unchanged V13.5 Blender + Manim Scenes.
- `spur_gears`: 5-second ratio-calculation and 12-second Manim smokes and an 80-second mixed Blender/Manim lesson spec are registered. The 80-second path loads and animates the tracked CC0 20T:40T mesh in Blender and uses Manim for the pitch-point cause and calculation. The ratio smoke exercises the LaTeX-free formula sequence. The 80-second preview is complete only when Blender integration, composition and full decode have run successfully; see the V14.1 integration report for current run evidence.
- In the `opposite_direction` beat, dashed pitch circles identify the ideal common pitch point `P`; signed angular arrows show opposite rotation, and the tangent arrow shows the equal common velocity `vₜ₁ = vₜ₂`. The direction and speed come from `core/education/gear_kinematics.py`, including reverse and zero-speed handling.
- The 12-second Manim smoke validates the sidecar but does not import the mesh. The V14.1 Blender Scene loads the actual `.blend` at runtime, uses temporary axis pivots without saving the source file, and writes `asset_load_report.json`; `renderer_provenance.json` may say `asset_loaded_by_renderer: true` only after that report passes checks.
- The pitch-point and tangential velocity marks express ideal external-gear rolling kinematics only. The stylized Manim teeth are schematic, not involute geometry; tooth contact location, contact force, friction, slip, efficiency, stress, deformation, and backlash are not solved.
- Solver adapters are not implemented here. A future Solver must produce validated data; the renderer only presents the shared run/context. Blender availability and actual preview completion are environment-dependent and must be reported from observed runs.
