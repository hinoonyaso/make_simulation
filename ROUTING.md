# V9 Source-Informed Lite Routing

Do not preload the bundle. Route from the artifact that exists now.

## Full narrated educational video
`director -> shared data/trace when needed -> manim/blender -> preview -> reviewer(1 pass) -> targeted patch -> resolve -> youtube(optional)`

## Single-scene/task shortcut
- Manim-only request -> `manim` only
- Blender-only request -> `blender` only
- existing preview QA -> `reviewer` only
- existing approved media edit -> `resolve` only
- asset lookup -> `core/visual-assets/asset_registry.py`; no LLM agent
- trace/data validation -> `core/shared-data/validate_trace.py`; no LLM agent
- narration TTS / measured timing / captions -> `core/narration/prepare_audio.py`; no LLM agent
- review frame sampling -> `core/render-reviewer-skill/scripts/extract_review_frames.py`; no LLM agent

## Skip rules
- no preview -> no Reviewer
- no edit request/assets -> no Resolve
- no publishing request -> no YouTube
- principle/tutorial -> no Paper Research
- no material 3D depth value -> prefer Manim; do not add Blender for spectacle
- no quantitative/computational state -> do not create a trace file just for ceremony

## Production rule
A beat is a **state transition**, not a slide. Preserve the same object when its meaning persists. For computed/simulated topics, compute state first and let both renderers consume one shared trace/config. Use real domain computation instead of hand-drawn fake outputs when correctness matters.

## Quality route
Normal Manim/Blender use Sol/medium because quality is encoded in production primitives. Astra is escalation only for flagship or failed/high-severity visual work. Reviewer uses Sol/high because judging real pixels is higher leverage than extra planning agents.

## Context rule
Each worker reads its SKILL.md + at most one active topic/reference. Pass only compact beat manifest, trace/config path, file paths, and review patches. `SOURCE_PATTERNS.md` is provenance only and is never part of normal context.

## Single beat contract
`visual_manifest.json` from the Director is the only beat list. Narration fills `audio` + measured `sec`; Manim/Blender fill `media`; Resolve stages it. No stage keeps its own copy of beats.

## Deterministic gates
- beat manifest (+ referenced traces): `core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py <manifest> [--require-media]`
- shared trace: `core/shared-data/validate_trace.py`
- narration timing: `core/narration/prepare_audio.py tts|captions <manifest-or-storyboard>`
- Resolve staging: `core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py`
- final media: `scripts/validate_delivery.py <final> --require-audio --fps 30 --audio-manifest ... --caption-timing ... --full-decode`
- scene style (no slide resets, no Workbench/low-fps renders): `scripts/check_scene_style.py <scene files>`
- bundle wiring: `scripts/validate_codex_setup.py`

## Quality reference
`pilots/01_teb_reference` is the current bar: bright studio Blender (real TurtleBot3, EEVEE, 30 fps) for physical things, continuous data-driven Manim for computation, pixel-aligned crane-to-top handoff, narration-timed beats with sentence captions.
