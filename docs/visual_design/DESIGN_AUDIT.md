# Unified Visual Design Audit

## Scope and evidence

Reviewed the V14.4 design branch base (`b1e45be`) and the current shared guide, visual tokens, Director, Blender, Manim, Reviewer and Resolve skills, `studio_utils.py`, `scene_kit.py`, the Manim Kit, the Bearing/Gear/Battery scenes and the TEB reference. This is a source and local-render audit; no audience study or full-length normal-speed review is inferred from static frames.

## Strengths to preserve

- Existing Manim semantic colors and the dark palette already have a single token source.
- Bearing R6 has a glyph-checked cross-platform font resolver, clearer component visibility and a stated model boundary.
- Blender already has two useful production foundations: a light TEB-style studio kit and a dark technical scene kit.
- The project already distinguishes lighting, materials, object scale, style checks and rendered review rather than treating source cleanliness as final quality.
- Existing Manim and Blender animations use traces/timelines and maintain persistent scene objects in many representative scenes.

## Findings and priority

| Priority | Finding | Evidence and user impact | Compatibility / effort | Render evidence needed |
|---|---|---|---|---|
| P1 | Profile choice was implicit and renderer-linked in guidance. | `shared-style-guide.md` preferred a bright default while Manim's Kit and token palette were dark; Blender skills described light studio as the default. New scenes lacked a lesson-level choice, so mixed scenes could change look without a reason. | Resolved with optional `visual_profile` in Lesson Spec and renderer context; V9 beat fields remain unchanged and old specs default to `technical_dark`. | Unit/plan tests pass; Bearing rendered in both profiles. Full-length normal-speed human review remains open. |
| P1 | Renderer palettes/material defaults diverged. | `scene_kit.py` kept independent linear tuples; `studio_utils.py`, Bearing, Battery and Gear used their own world/text/semantic values. A token edit could not reliably reach all renderers. Blender's World node also ignored the legacy `world.color` assignment, and WSL did not pass the profile environment variable to Windows Blender. | Resolved for integrated lesson renders with token-backed material roles, a shared World-node helper, and an explicit Blender `--visual-profile` CLI argument. Asset-specific surfaces remain asset-owned. | Bearing Light/Dark stills and a Gear Light still were rendered and inspected. Battery render remains blocked by missing local PyBaMM. |
| P1 | Korean font behavior was not common to both renderers. | R6 font checking was scoped to Blender/Bearing; Manim Kit defaulted to a fixed family without checking the rendered text's glyph coverage. | Common Blender resolver, retained `BEARING_KOREAN_FONT` alias and a Manim family resolver. Low/medium. | Actual Korean labels in Blender and Manim on target environments. |
| P1 | QA mainly inspected source patterns. | `check_scene_style.py` detects source patterns and render settings, but cannot see contrast after color management, clipped labels, dark/frozen intervals or brightness jumps. Reviewer reports distinguish modalities but had no structured metric-candidate field. | Add token/font static validator and sampled grayscale candidate report; no automatic aesthetic PASS. Medium. | Candidate review at exact timestamps; motion/overlap/comprehension remain human checks. |
| P2 | Layout and motion advice was prose-only. | Repeated composition and pacing decisions could not use common bounds or timing ranges, while one fixed layout would also be too rigid. | Add a few normalized layout hints and advisory timing ranges; not forced. Low. | Check at 540p and delivery resolution for each selected layout. |
| P2 | Surface roles were not named across 3D examples. | Generic material values existed, but the shared system had no token-backed material role presets. Asset material accuracy and educational highlights could be confused. | Add metal/matte-metal/plastic/rubber/glass/structure/active/annotation roles; keep CAD/vendor asset materials untouched. Low. | Inspect silhouette, roughness/highlights, contact and semantic overlay separation. |

## Chosen direction

Extend `core/visual_primitives` as the source of appearance roles. Add a lesson-level profile carried by the existing renderer context and environment, so Blender and Manim see the same choice. Preserve existing schema IDs, existing V9 manifest required fields and the current default palette. Keep asset-specific physical materials local. Use separate static checks and sampled render candidates; the latter never classify intentional holds/dark canvases as confirmed errors.

Alternatives considered: a forced single palette would break useful TEB studio and technical-data looks; renderer-based defaults would reproduce the current inconsistency; a large design framework would duplicate existing kits. The selected additive profile approach keeps those alternatives out of the renderer boundary and is covered by compatibility tests.

## Risk and verification focus

- Color management and physical material response can make equal token RGB values appear different across renderers. Tokens are sRGB; Blender shader colors receive linearized values. Compare rendered output, not code values alone.
- Existing lessons without the new field remain Technical Dark. Explicit Studio Light changes canvas, some semantic luminance and lighting ratios, so each opted-in lesson still needs preview review.
- Font cmap coverage checks the requested Hangul characters, not shaping quality or the final rasterized bounding box.
- Grayscale frame heuristics can flag intentional pauses and dark backgrounds and can miss short events. Only targeted human frame/video review resolves them.
- 540p examples do not prove 1080p typography, audio/caption timing, learner comprehension or full-motion naturalness.

## Result

The baseline had good individual craft but no shared rule that reliably selected and propagated the style. The implementation adds this decision path and static/render observation tools. Render inspection also found and fixed two integration defects (World-node color application and WSL-to-Windows profile propagation). The local frame review is documented in `VISUAL_QA_REPORT.md`; full-speed motion/audio and learner comprehension are still ungraded.
