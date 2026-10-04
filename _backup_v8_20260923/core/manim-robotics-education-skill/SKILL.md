---
name: manim-robotics-education-skill
version: 4.0
description: High-quality, low-token Manim robotics/AI explainers built around continuous visual reasoning, progressive disclosure, math-to-visual derivation, and narration-synchronized motion.
---

# Manim Robotics Education V4

Use Manim CE for the **reasoning layer** of robotics/AI videos.

## Non-negotiables

- One narration beat -> one dominant visual change -> one attention target.
- Preserve object identity. Prefer `Transform`, `TransformMatchingTex`, `TransformFromCopy`, trackers, and updaters over slide replacement.
- Show intuition before notation when possible; let equations emerge from visible geometry/data.
- Progressive disclosure: introduce only the information needed now.
- Never invent numeric evidence. Mark illustration/toy simulation/model execution/paper result correctly.
- Use `templates/manim_kit.py`; do not recreate palette, emphasis, frame-safe layout, semantic equation coloring, or common visual primitives.
- Use Blender only when 3D depth or spatial relations materially affect understanding.

## Default visual language

Default is a restrained dark-neutral canvas with bright readable geometry and a small semantic palette. Avoid dashboard/card-heavy UI unless the concept is actually a system architecture. Do not imitate another creator's exact palette, typography, timing, or signature compositions.

## Animation grammar

- state/meaning changes -> `Transform` / `ReplacementTransform`
- shared symbols across equations -> `TransformMatchingTex`
- visible geometry becoming notation -> `TransformFromCopy`
- continuously changing quantities -> `ValueTracker` + updater/`always_redraw`
- viewpoint change -> camera move
- new supporting context -> subtle `FadeIn`

Avoid repeated full-scene FadeOut/FadeIn transitions.

## Minimal workflow

1. Read the active beat(s); if a narration manifest exists, use its timing/cue fields as the timing source of truth.
2. Load only one matching topic reference if useful. Resolve a reusable component through `visual-asset-library-skill` only when local helpers are insufficient or cross-video reuse matters.
3. Build the densest reasoning scene first.
4. Verify equation/geometry identity and variable colors.
5. Add transitions that preserve objects between beats.
6. Preview intro, derivation, densest frame, robot consequence, recap.
7. Produce a preview first and hand actual frames/video to `render-reviewer-skill`; patch only owned issues.
8. Final render after blocker/high review issues are cleared.

## On-demand references — do not preload all

- continuity, progressive disclosure, camera, math-to-visual -> `references/production.md`
- metrics/simulation/paper claims -> `references/evidence.md`
- topic-specific hints -> only matching `references/topics/<topic>.md`

If helper behavior is unclear, inspect only `templates/manim_kit.py`.

## Quality gate

A final scene passes only if the viewer can tell what to look at immediately, important objects remain recognizable across transformations, symbols map to visible quantities, motion does not compete with narration, equations/frames/units are correct, and the final robot consequence is explicit.
