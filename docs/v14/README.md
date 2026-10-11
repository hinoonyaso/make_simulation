# V14 Generic Education Renderer

V14 adds an allow-listed Renderer Registry to the `education-lesson-spec/v1` flow. The V14 branch registers `ball_bearing` (with the existing smoke alias) and `spur_gears`. V13.5 is merged into `main` at `f53ee159`; V14 itself remains a branch/PR change until merged.

## Commands

```bash
uv run python scripts/produce_lesson.py --spec examples/education/bearing.json --plan-only
uv run python scripts/produce_lesson.py --spec examples/education/spur_gears.json --plan-only
uv run python scripts/produce_lesson.py --spec examples/education/spur_gears.json --preview --manim-only
```

Planning validates the V9 manifest contract, the V12 integer-frame timeline, the topic-to-renderer allow-list, Blueprint/backend capability, the registered Scene and class, the education Asset Catalog entry and its SHA-256 sidecar. `--plan-only` does not call Blender, Manim, TTS or external services. Rendering probes the required local runtime before it creates output. A Blender beat cannot be silently converted to a Manim beat by `--manim-only`.

## Add a topic

1. Add or identify a redistributable education model in `assets/education/catalog.json`, including a tracked `.blend` file and matching metadata sidecar when the model is a Blender asset. The catalog ID and metadata source hash must agree.
2. Create a Manim scene file and a top-level `Scene` class. The scene reads `EDUCATION_MANIFEST_PATH`, `EDUCATION_TIMELINE_PATH`, and `EDUCATION_RENDER_CONTEXT_PATH`. Preserve the V9 beat list and V12 frame intervals.
3. If the topic has 3D beats, create a Blender script that accepts the common `--manifest`, `--timeline`, `--output`, width/height/fps and sample options.
4. Register a canonical topic, optional aliases, Scene file/class, asset ID, supported renderer modes, and per-renderer Blueprint implementations in `core/education/renderer_registry.py`. A trusted `context_builder` may derive non-solver results from validated asset metadata; Python paths and commands are never accepted from a Lesson Spec.
5. Add an `education-lesson-spec/v1` JSON file under `examples/education/`; include unique beat and phase IDs, duration, one supported renderer per beat, evidence type, and any relevant Blueprint.
6. Run plan-only first, then a short preview. Add topic-specific registry, failure, timing, and render tests. CI never requires Blender for the Manim-only gear smoke.

To add a future Blender Scene, register its in-repository path and `blender` mode; the common CLI chooses it from beat `tool: "B"` without topic-specific CLI changes. It will still need its own smoke and media validation before it can be called supported.

## Current support boundary

- `ball_bearing`: unchanged V13.5 Blender + Manim Scenes.
- `spur_gears`: short Manim schematic, driven by the tracked 20T:40T asset's validated JSON sidecar. It derives `omega_2 / omega_1 = -Z_1/Z_2 = -0.5` and the 60 mm center distance. This is ideal kinematics, not a solver run.
- In the `opposite_direction` beat, dashed pitch circles identify the ideal common pitch point `P`; signed angular arrows show opposite rotation, and the tangent arrow shows the equal common velocity `vₜ₁ = vₜ₂`. The direction and speed come from `core/education/gear_kinematics.py`, including reverse and zero-speed handling.
- The gear `.blend` file is validated and mapped to the topic, but the Manim smoke does not import or animate that mesh. A Blender mesh render/animation is deferred to V14.1 and must not be claimed as completed.
- The pitch-point and tangential velocity marks express ideal external-gear rolling kinematics only. The stylized Manim teeth are schematic, not involute geometry; tooth contact location, contact force, friction, slip, efficiency, stress, deformation, and backlash are not solved.
- Solver adapters are not implemented here. A future Solver must produce validated data; the renderer only presents the shared run/context.
