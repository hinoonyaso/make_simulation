# Visual Design System

## Purpose and compatibility

`core/visual_primitives/design_tokens.json` is the shared source for renderer-neutral semantic colors, the two canvas profiles, typography guidance, normalized layout hints, advisory motion ranges and material roles. Its schema remains `visual-design-tokens/v1`; existing top-level Manim colors and values are preserved. Existing lesson specs default to `technical_dark` unless they explicitly set `visual_profile`.

The lesson flow is:

`LessonSpec.visual_profile → plan_lesson manifest/visual plan → renderer_context → EDU_VISUAL_PROFILE → Manim Kit / Blender scene`

The top-level manifest value is optional metadata. Existing beat fields and their meanings remain unchanged. The default must not be inferred from a selected renderer.

## Choose a profile

| Profile | Use when | Canvas roles |
|---|---|---|
| `studio_light` | Part shape, assembly, contact, footprint or space is the primary evidence and a neutral lit field separates it clearly. | Light neutral background/surface/floor, dark text, softened semantic accents for contrast. |
| `technical_dark` | Equation, algorithm, matrix, graph or dense data is the primary evidence and a dark field keeps attention on those relationships. | Existing dark background and text palette, restrained high-contrast semantic accents. |

These are starting recommendations. Either renderer may use either profile. Select from primary evidence, readability and continuity across adjacent scenes. If two styles meet, preserve object identity, meaning, units, source time and trace values. A background/color change alone is not an explanatory transition.

`recommend_visual_profile(visual_goal)` is advisory. Current goal hints include spatial geometry/robot motion/physical parts/assembly → `studio_light` and equation/algorithm/data flow/graph/matrix → `technical_dark`. The Director may override this based on actual contrast and composition.

## Shared color and material roles

- `profile_color(role, profile)` resolves profile-specific accessible semantic colors, then canvas roles, then shared semantic tokens.
- Semantic meanings: input/sensor, active/selected, result/output, error, learned/AI, warning, neutral structure, X red, Y green, Z blue. Color alone never distinguishes data.
- Canvas roles vary between profiles: background, surface, primary/secondary/muted text, border, divider, floor and neutral geometry.
- 3D material role values are guidance: metal, matte metal, plastic, rubber, glass, neutral structure, active component and annotation. Vendor/CAD materials and physically meaningful surfaces stay asset-owned.
- Blender values are converted from sRGB to scene-linear before assignment. Review AgX/color-managed renders for highlight clipping and actual text/shape contrast.

## Typography and Korean fonts

- `typography_1080p` gives a working hierarchy for title, section, label, caption, equation, number and annotation. `minimum_critical_preview_px` is checked at token level; the final rendered box still requires frame inspection.
- Blender: `discover_korean_font()` checks required Hangul glyphs and returns a file Blender can read. `EDU_KOREAN_FONT` is preferred; `BEARING_KOREAN_FONT` remains a compatible legacy alias. In WSL → Windows Blender, use a Windows-visible path or an accepted `/mnt/<drive>/...` path.
- Manim: `discover_manim_korean_font()` checks the installed family file for the actual Hangul text. Set `EDU_MANIM_FONT` to an installed family name when needed.
- Coverage does not prove shaping, kerning, text bounds or overlay safety. Inspect the produced frame at preview and delivery sizes.

## Layout hints

`layout.presets` stores normalized lower-left-origin rectangles in `[x0,y0,x1,y1]` form: `hero_focus`, `object_explanation`, `side_by_side`, `equation_geometry`, `graph_state`, `process_flow` and `recap`. `layout_region()` converts a region to pixels; Manim `place_in_layout()` fits a mobject inside a chosen region. `center=True` centers the fitted bounding box; `center=False` anchors the fitted bounding box's actual upper-left corner to the region's safe upper-left edge. Oversized mobjects scale proportionally to fit. Negative/non-finite margins and regions with no usable area raise `ValueError`. These rectangles are hints. Keep the attention target large and omit unused regions/cards.

Respect `safe_margin_fraction` and `caption_exclusion_fraction`; inspect the actual final subtitle composition because externally burned captions are not represented in a source scene's bounds.

## Motion hints

`motion_seconds` contains recommended min/max ranges for reveals, emphasis, transitions, labels, camera and holds. These never override measured narration or trace/timeline event times. A hold must expose an object/value/relation for a real inspection task. Use continuous state or identity-preserving transforms when the same idea persists; do not add motion for decoration.

## Renderer usage

- Manim Kit: `apply_theme(scene, background=None, *, profile=None)`, `palette_for_profile(profile)`, `txt(..., profile=...)`, `semantic_tex(..., profile=...)`, `coordinate_axes_2d(..., profile=...)`, and `place_in_layout(...)`. `apply_theme` keeps the legacy positional/keyword background argument and returns the same Scene; the selected V14.5 profile and palette are exposed as `scene.visual_profile` and `scene.palette`. Existing default `P` and Technical Dark values remain compatible.
- Blender: `scene_kit.bootstrap(..., visual_profile=...)` chooses token-backed semantic materials while preserving the legacy render-quality `profile` argument. `studio_utils.setup_studio(..., visual_profile=...)` applies the selected canvas; `apply_world_profile()` sets both the legacy world color and the rendered World shader node. Use `studio_lights(profile)` and `add_studio_floor(..., profile)` for matching setup. `visual_material()` applies shared material-role values.
- Production: `LessonSpec.visual_profile` is copied to the renderer contract and Manim environment. The generic lesson runner passes Blender the explicit `--visual-profile` CLI option because WSL does not reliably forward arbitrary Linux environment variables to Windows executables. Each registered Blender scene accepts the option; standalone scenes may still set `EDU_VISUAL_PROFILE` directly.

## Visual QA tools

```bash
uv run python scripts/validate_visual_design.py
uv run python scripts/validate_visual_design.py --all-scenes
uv run python scripts/validate_visual_design.py --blender-text '한글 베어링' --manim-text '한글 그래프'
uv run python scripts/analyze_visual_render.py path/to/preview.mp4 --report output/visual_metrics.json
```

`validate_visual_design.py` checks token schema, semantic roles and text contrast, optional installed font coverage and existing source-style rules. `analyze_visual_render.py` probes technical metadata and samples 64×36 grayscale frames at 4 fps for dark/freeze/brightness candidates. Candidate output is not a visual verdict. It does not measure text bounding boxes, detect semantic overlap, establish full decode, or replace Reviewer/human motion/audio/learning checks.
