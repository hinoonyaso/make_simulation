---
name: robotics-ai-visual-director-skill
description: Low-overhead visual director for robotics/AI explainers using state-transition storytelling, shared computed traces, progressive disclosure, and strong screen composition.
metadata:
  version: "5.12-guided-reasoning"
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

## AI execution topic routing (V10, additive to V9)
- For RAG, embeddings, retrieval, vector databases and attention, inspect the available `ai-mechanism-trace/v1` before drafting beats. If a validated trace exists, reuse it as the source of all IDs, vectors, scores, ranks and text. If computation is absent, create/record it before animation; never hand-author the result values.
- Keep the existing V9 manifest schema and `model_execution` evidence. The manifest validator selects the AI trace validator by its `schema`; robotics `robotics-visual-trace/v1` continues to use the robotics validator.
- Route computation to continuous Manim state transitions by default. Use the trace-matched Three.js view for embedding/similarity only when spatial structure helps the explanation. Maintain chunk/query IDs, recorded ranks/scores and the beat's presentation-time interval across renderer handoff. The lossy PCA display must never drive retrieval or replace 384D score values.
- A request for a RAG/AI simulation is not a slide-deck request: preserve the same document/query/chunk objects while they split, embed, compare and enter context. Do not resolve a missing AI route by selecting a generic presentation renderer.

### Executable RAG route
- For a requested RAG video, use `uv run python scripts/produce_ai_video.py --topic rag --trace <trace.json> --render auto --silent`; for a new input provide both `--document <file>` and `--question <text>`. The command writes one V9-compatible manifest, validates its trace, renders/decodes a preview, and only then renders the final video. `--durations` changes the four presentation beats in that manifest.
- The currently supported new execution is a local lexical pipeline: character windows → TF-IDF features → cosine ranking → context assembly. It has no semantic embedding model and does not generate an answer. State that in narration, captions and the evidence description. Do not call a lexical vector an embedding or infer an LLM answer.
- `--render auto` keeps Manim as the full mechanism scene and uses the trace-matched Three.js segment when actual vectors and its local runtime are available. PCA coordinates are lossy display data; ranking remains the recorded original score. On missing or failed browser tooling, the report must state Manim fallback and continue with the full timeline.
- Resolve a visual goal (`numerical_explanation`, `algorithm_flow`, `image_space`, `motion_3d`, `spatial_relationship`, `comparative_analysis`) before renderer selection. H1 motion requires the existing Blender mesh path when available; analytical H1 views use Manim. Never choose a 3D backend only because it is installed.
- Use the run's `mechanism-timeline/v1` as the single frame contract. Phase intervals are contiguous integer-frame ranges; source trace time and presentation time are separate. Do not rebuild phase timing independently inside a renderer.
- Before expensive rendering, inspect the selected backend with `scripts/inspect_capabilities.py --topic <topic> --preflight --visual-goal <goal>`. A process-level failure or missing model is BLOCKED; explicit Blender requests never silently fall back.
- When automatic fallback is allowed, report the selected backend, rejection reason, and lost visual evidence. Cache identity follows the backend that actually rendered.
- For V11 numerical mechanisms, inspect `core/mechanism/catalog.json` / `scripts/inspect_capabilities.py` and route ready adapters through `scripts/produce_video.py`. Available numerical routes include quantization, synthetic-candidate NMS, sampled MCU PID, and the single-head self-attention example. Generic `attention` is intentionally ambiguous; require a canonical choice such as `self_attention`.
- The V11 self-attention route records Q/K/V projection, QKᵀ, scaling, optional causal mask, softmax and weighted sum in one trace. It is an educational NumPy calculation, not trained Transformer/LLM execution. Synthetic NMS is not YOLO inference; reference quantization is not accelerator execution; PID is a numerical plant, not firmware or hardware.
- Refuse any planned/unavailable adapter by name. Never imply that capability registration means full production or model/robot execution. The common V11 CLI is a silent technical render; use the V9 narration/caption/reviewer/delivery stages separately and require their evidence before claiming L4.

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

## Make physical evidence carry the explanation

For planning/control lessons, use the same run to connect reference choice -> controller input -> physical response -> measured feedback. A selected path alone is not execution evidence. Put the decisive link and its source/phrase anchors in the existing `state_change` / `focus`; do not add a parallel shot list. If the trace supports only part of this chain, narrow the claim.

Keep the explanation the user has accepted; improve the view of the mechanism before adding narration or terminology. Read `references/director-qa.md` for physical emphasis and duration decisions. Choose a view where the relevant robot/clearance/component is readable, rather than keeping a whole-room view by habit. Include the hardest plan-to-response link in the critical excerpt, not only route selection.

For a recap, name what new comparison, measurement or limitation the viewer will inspect. Shorten repeated outcome narration before TTS when the preceding execution already established it. Runtime follows the requested range and the explanation; neither a longer video nor more cuts establishes quality.

## First-view understanding

For an introductory control lesson, make the reason understandable in ordinary language before showing degrees, signs or rad/s: the implemented target direction differs from the robot's current direction, so the controller chooses a corrective turn; physics determines the response. Show how that target is selected from the reference, rather than letting an arrow appear without a reason. Explain the actual controller rule, including relevant stop/saturation limits; do not imply that the obstacle alone commands a particular turn.

In existing `focus`, name the intended explanation and a plausible wrong interpretation to distinguish. Give the viewer the inputs before announcing the correcting command; when prediction helps, let the visible relation settle before revealing its answer. Plan a supported change-of-condition question when it helps diagnose understanding. Read `references/director-qa.md` for the first-view check. A technical review or informed agent answer is not evidence that a novice understood. Keep production moving if novice feedback is unavailable and report that learner evidence separately.

## Finish a defined quality target

For requested flagship refinement, use `references/director-qa.md` to select a small set of visible weaknesses from actual media and define their completion criteria in the existing episode README before changing the scene. Focus on the weakest necessary inference/shot rather than redesigning every beat. Keep the accepted explanation and evidence boundary; carry those targets through the existing `focus` and review report. Completed targets stay completed unless new media regresses them or the user changes the request. Production completion, craft completion and unavailable learner/playback evidence are separate outcomes.

## Connect discoveries across the episode

When improving narrative depth, read `references/director-qa.md` for the link between adjacent discoveries. The outcome of one inference should supply the evidence or question for the next. Preserve the accepted central explanation and requested runtime; deepen a supported relation before adding new topics, cuts or jargon. Treat narrative changes as candidates until a voiced excerpt demonstrates the benefit.

## Reference-level mechanism design

For requested reference-level craft, use `references/director-qa.md` to design one concrete example across physical parts, simplified relations and notation before specifying surface polish. Keep these correspondences in the existing manifest, not another beat list. Choose the deciding feature's readable bounds rather than imposing a fixed whole-subject area. A title naming a controller is insufficient evidence of its operation.

Mechanism and quantity-to-term repairs are specified in `references/director-qa.md`; define moving-part and moving-token evidence before production.

For viewer-reported difficulty, use `references/director-qa.md` to repair the missing causal link, define unfamiliar command terms and allocate local reading time from the actual responses. Preserve demonstrated strengths and the requested runtime; small-sample scores are diagnostic evidence.

For observed composition/geometric gaps, use `references/director-qa.md` to select task-led views and expose distance-to-angle reasoning before angular-speed notation. Preserve ideal-geometry versus measured-response boundaries.

For requested relation-level refinement, use `references/director-qa.md` to expose the intermediate equality, preserve connected parts, follow one recorded feedback example and show changed-condition geometry. Choose composition by task and assign fixed-pose surface candidates. Preserve accepted pace; when new notation introduces an unexplained relation, revise only the speech that needs to guide it. The same reference covers decisive command changes and source-state handoffs.
