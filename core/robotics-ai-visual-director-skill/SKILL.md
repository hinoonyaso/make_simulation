---
name: robotics-ai-visual-director-skill
description: Low-overhead visual director for robotics/AI explainers using state-transition storytelling, shared computed traces, progressive disclosure, and strong screen composition.
metadata:
  version: "5.3-physics-evidence"
---

# Robotics / AI Visual Director

Own the question, story, narration timing, visual state transition, tool route, and evidence mode in one pass.

## Non-negotiables
- A shared trace does not guarantee shared timestamps. Match the displayed plan/map and robot pose to the intended source time; if showing a historical snapshot beside later playback, label the different times and narrate that relationship explicitly.
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
`text` is what TTS reads (spell acronyms phonetically, e.g. 티이비); `caption` is what viewers read (TEB). `min_sec` pads silence only for a named inspection, prediction, or real-time action. Do not use it to meet a runtime target; measured `sec` may include padding and is not spoken duration.
`trace` is required for `trace_playback`/`model_execution`. `audio` and measured `sec` are written by `core/narration/prepare_audio.py`; `media` is written by Manim/Blender after rendering.
Do not separately restate script + storyboard.

## Workflow
1. Central question + misconception/missing intuition.
2. Choose persistent visual objects.
3. If real computation matters, define the shared trace/config source.
4. Draft necessary beats around observation -> question/prediction -> mechanism/comparison -> consequence. Choose their count and duration from explanatory need and the requested runtime, not a fixed template.
5. Each beat states `object: old_state -> new_state` in concrete visual terms.
6. Assign Manim / Blender / Edit only where needed.
7. Run `templates/validate_visual_manifest.py` (also validates any referenced trace).
8. For narrated videos run `core/narration/prepare_audio.py tts <manifest>`; recorded audio replaces planned `sec`. Revisit beats it reports as >15% off plan.
9. Before costly rendering, check the central decision beat: can the viewer see the evidence for the choice, and do the named phrases match event order? Use existing `state_change` for the cause -> change -> consequence, and `focus` for the decisive visible evidence. Include phrase anchors in those fields when timing is critical; do not create a second beat list.
10. For a full narrated explainer, select the contiguous beat IDs carrying the hardest inference. Render a cheap moving excerpt with measured narration before full production; typically 15–25 seconds, adjusted to the inference. Keep those IDs and their ranges in the existing manifest, not a second storyboard. Review it using the discovery criteria in `references/director-qa.md`. Reuse an already reviewed equivalent excerpt when its story, timing and evidence have not changed.
11. Resolve central story/timing defects in that excerpt before costly full rendering. Technical preview availability alone is not approval. If motion/audio inspection is unavailable, report the missing checks and remaining production status; do not call it fully approved.
12. Handoff only the compact manifest + optional trace path + excerpt review status.

## On-demand references
Load at most one: storyboard / research-compression / visual-contract / director-qa / narration.
Load `narration.md` when drafting or revising `text`/`sec`/`sfx`/`bgm` for a narrated video.

## Quality gate
- The viewer can explain the central outcome from visible evidence, not just repeat that it changed. For a choice, compare the relevant alternatives or expose the decisive constraint; do not invent unavailable scores or rejected candidates.
- Change one explanatory factor at a time when the evidence permits. If playback couples several factors, show their actual order and avoid claiming an isolated causal experiment.
- A continuous story may use purposeful close-ups, cuts, or 3D-to-2D handoffs. Preserve identity and orientation; do not confuse continuity with one long moving camera shot.
- During a comparison, stabilize the viewpoint and suppress competing motion. Frame the deciding cell, contact, force, or relation rather than the whole room by habit.
- Each pause has something to inspect or predict. If the requested length exceeds supported content, deepen the explanation with supported evidence or report the constraint; do not silently pad.
- No decorative beat, fake simulation, duplicated planning, or slide replacement where a state transform would teach better.

## Physics and explanation together

For this user's robotics episodes with a physical motion/contact question, preserve the current discovery-first explanation and plan physics-backed Blender setup/consequence around it. The physical behavior must answer the same question; do not add a decorative 3D interlude. Route computation to a capable installed simulator before rendering, then hand the same run/trace to both renderers. Consult Blender's `core/blender-robotics-simulation-skill/references/evidence.md` when defining the physical experiment; it owns the run/evidence contract.

In the existing `state_change`/`focus`, identify the controlled input, physical response and decisive measurable relation, and specify source-time handoffs. Include a relevant physics portion in the critical excerpt. Distinguish planned/reference path from actual engine trajectory. Do not force an expected outcome or call pose playback a physical run. Preserve educational-model/Nav2 boundaries. If physical execution is unavailable, report that unmet portion explicitly rather than silently delivering a keyframed substitute.
