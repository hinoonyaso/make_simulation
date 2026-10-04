---
name: blender-robotics-simulation-skill
version: 4.0
description: High-quality, low-token Blender spatial explanations for robotics. Minimal 3D visual language, Manim-compatible semantics, camera-first geometry, and evidence-safe trace playback.
---

# Blender Robotics Spatial V4

Use Blender for the **spatial intuition layer**, not as decoration.

## Non-negotiables

- First classify the output: `Explanation`, `Trace playback`, `Simulation`, or `Model execution`.
- Keyframed motion alone is not simulation.
- Frames, axes, units, geometry, transforms, and trace values must be correct.
- Use `templates/scene_kit.py`; do not rebuild camera rigs, semantic materials, coordinate frames, trajectories, or render profiles.
- Prefer abstract readable robot geometry over unnecessary photoreal detail.
- Keep the visual language compatible with Manim: neutral background, restrained materials, semantic overlays, clean silhouettes.
- Dense equations stay in Manim unless their 3D placement is itself the lesson.

## Default look

Minimal cinematic-technical 3D: matte surfaces, controlled highlights, soft key/fill/rim light, shallow visual hierarchy, small bevels, no clutter. EEVEE `FINAL` is default. Cycles `HERO` only when a short/still shot materially benefits.

## Camera grammar

- perspective wide: spatial context
- perspective medium/detail: mechanism
- orthographic: geometry that must not be distorted by perspective
- camera movement: only when viewpoint itself explains the concept
- object motion: for state/mechanism changes

Use target/look-at, never guessed Euler rotations.

## Minimal workflow

1. Define spatial question + evidence mode + persistent 3D objects; if a narration manifest exists, use its timing/cue fields as the timing source of truth.
2. Define coordinate frames/units before scene construction. Resolve a reusable component through `visual-asset-library-skill` only when the local procedural helpers are insufficient or cross-video reuse matters.
3. Load only one topic reference if useful.
4. Start with `scene_kit.bootstrap(style='minimal')`.
5. Build mechanism before decorative motion.
6. Render 3–4 representative review frames.
7. Fix silhouette, occlusion, axis direction, path/ray visibility, exposure, and material separation.
8. Hand review frames/preview to `render-reviewer-skill`; patch only owned issues.
9. Render `FINAL` or transparent PNG sequence after blocker/high review issues are cleared.

## On-demand references — do not preload all

- camera/light/material/compositing -> `references/production.md`
- simulation/trace/physics/claims -> `references/evidence.md`
- topic-specific hints -> only matching `references/topics/<topic>.md`

If helper behavior is unclear, inspect only `templates/scene_kit.py` first.

## Quality gate

The subject must be obvious in silhouette; 3D depth must add understanding; semantic overlays must remain readable; background/lighting must not compete with the mechanism; frames/axes must be correct; and the scene must not imply physics that was never simulated.
