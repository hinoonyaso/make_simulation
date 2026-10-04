---
name: robotics-ai-visual-director-skill
version: 5.0-source-informed-lite
description: Low-overhead visual director for robotics/AI explainers using state-transition storytelling, shared computed traces, progressive disclosure, and strong screen composition.
---

# Robotics / AI Visual Director

Own the question, story, narration timing, visual state transition, tool route, and evidence mode in one pass.

## Non-negotiables
- One beat = one narration intent + one **state change** + one attention target.
- Preserve object identity across beats whenever its meaning persists.
- Question/phenomenon first; vocabulary and notation after the viewer has something concrete to name.
- Visual first, notation second. Equations should emerge from visible quantities.
- Primary object should usually occupy ~55–75% of useful frame at a key beat.
- No persistent dashboard chrome, scene badges, metadata cards, or tiny secondary text by default.
- Use Blender only when 3D/spatial intuition changes understanding; otherwise use Manim.
- For computed/simulated/model-driven topics, create/load **one shared trace/config** before animation; never let each renderer invent its own numbers.
- Dense relations (network edges, attention, point correspondences) start thresholded/top-k and expand only when needed.
- Evidence label must be explicit: illustration / toy simulation / trace playback / model execution / reported result.

## Compact manifest
Return one `visual_manifest.json` (shape: `templates/visual_manifest.json`). It is the single beat contract for every downstream stage; Resolve does not restate beats.
Beat fields: `id | text | caption | sec | min_sec | object | state_change | focus | tool(M/B/E) | evidence | trace | sfx | bgm | audio | media | media_in | media_out`.
`text` is what TTS reads (spell acronyms phonetically, e.g. 티이비); `caption` is what viewers read (TEB). `min_sec` pads silence when the visual needs longer than the line (e.g. a real-time drive).
`trace` is required for `trace_playback`/`model_execution`. `audio` and measured `sec` are written by `core/narration/prepare_audio.py`; `media` is written by Manim/Blender after rendering.
Do not separately restate script + storyboard.

## Workflow
1. Central question + misconception/missing intuition.
2. Choose persistent visual objects.
3. If real computation matters, define the shared trace/config source.
4. Draft only necessary beats, usually 6–12.
5. Each beat states `object: old_state -> new_state` in concrete visual terms.
6. Assign Manim / Blender / Edit only where needed.
7. Run `templates/validate_visual_manifest.py` (also validates any referenced trace).
8. For narrated videos run `core/narration/prepare_audio.py tts <manifest>`; recorded audio replaces planned `sec`. Revisit beats it reports as >15% off plan.
9. Handoff only the compact manifest + optional trace path.

## On-demand references
Load at most one: storyboard / research-compression / visual-contract / director-qa / narration.
Load `narration.md` when drafting or revising `text`/`sec`/`sfx`/`bgm` for a narrated video.

## Quality gate
No decorative beat, fake simulation, duplicated planning, or slide replacement where a state transform would teach better.
