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

## V10 AI execution topics
- Implemented RAG retrieval / embeddings explanation -> validate the saved `ai-mechanism-trace/v1` with `scripts/validate_ai_trace.py`; use it as the sole source for identifiers, vectors, scores and ranks. The execution CLI currently supports RAG only; standalone Attention or other AI mechanisms must be reported unsupported.
- Keep the V9 `visual_manifest.json` fields and `model_execution` evidence mode. Manifest validation dispatches by trace schema: robotics traces use `core/shared-data/validate_trace.py`; AI execution traces use `core/ai-mechanism/rag_trace.py`.
- Route computational explanation to continuous, trace-driven Manim state transitions. When embedding-space geometry materially helps, reuse the trace-matched Three.js segment for the embedding/similarity interval; PCA coordinates are illustrative, while displayed ranking and scores remain from the original vector dimensions.
- A request for an AI/RAG simulation must not fall back to a generic presentation/slide route. Use an existing validated trace when present; otherwise produce and validate a real AI execution trace before rendering. Do not invent timestamps or claim model latency from presentation time.
- For an executable local RAG production, invoke `uv run python scripts/produce_ai_video.py --topic rag --trace <trace.json> --render auto --silent`. For new inputs use `--document <utf8-file> --question <text> [--chunk-size N --overlap N --top-k K]`. The supported fresh-execution path is lexical TF-IDF plus cosine retrieval and context assembly; it has no semantic embedding model or answer-generation model. Its labels and evidence must say so. Other AI topics are rejected until implemented.
- The production CLI emits one V9-compatible `visual_manifest.json`, validates the AI trace, renders a preview and runs technical decode QA before final rendering. `auto` keeps Manim as the full mechanism renderer and inserts the Three.js vector segment only if recorded vectors and local browser dependencies are available; otherwise it records a Manim fallback.

## V11 mechanism capability routing
- Before selecting a renderer for a robotics/AI mechanism, query `uv run python scripts/inspect_capabilities.py` or `MechanismRegistry`. Resolve Korean and English aliases to a canonical topic, then check its support level and implementation status.
- For ready numerical adapters, use `uv run python scripts/produce_video.py --topic <canonical-or-unambiguous-alias> --preview`. The command executes the adapter, validates its domain trace, makes a visual plan, renders Manim and full-decodes the preview. An ambiguous alias (for example `attention`) must return candidates; select `self_attention`, `cross_attention` or `multi_head_attention` explicitly.
- `self_attention` is a NumPy single-head educational calculation: Q/K/V → QKᵀ → scaling → optional causal mask → softmax → weighted values. It is not trained Transformer or LLM inference. NMS is synthetic candidate arithmetic, not YOLO inference. Quantization is NumPy reference arithmetic, not an accelerator kernel. MCU PID is a numerical plant, not firmware or hardware execution.
- Ready means the declared adapter can execute its stated scope; it does not imply L4 full production. General narration, captions, reviewer and delivery workflow remain separate from the current silent technical renderer. A missing or planned adapter is refused by name rather than sent to RAG or a generic slide renderer.

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

## Explanation acceptance

Technical gates and educational review are separate. Director supplies visible cause -> decisive evidence -> consequence in the existing manifest; renderers make those relations readable and synchronize them to measured phrases. Reviewer inspects the central decision before/during/after, including motion/audio when available. Missing evidence for the central answer or misleading causal timing is high severity. An incomplete inspection is not PASS. Purposeful close-ups/cuts preserve continuity; padded runtime and a continuously moving camera do not establish explanation quality.

## Critical excerpt for full explainers

Before costly full rendering: Director selects the contiguous manifest beat IDs containing the hardest inference -> render a cheap moving excerpt with measured narration (usually 15–25 seconds, adjusted to context) -> inspect comprehension, motion and voice -> patch the central cause -> full production. Reuse an equivalent already approved excerpt. This adds no second beat list or mandatory extra agent. Single-scene shortcuts remain proportional to the request.

Reviewer reports comprehension, motion and audio status separately. For narrated lessons, unavailable listening/playback means incomplete educational acceptance even when frame/timing and deterministic gates pass. Recheck changed modalities after patches. No creator-parity claim follows from these gates.

## Physics-backed robotics route

User preference for robotics episodes: preserve the discovery explanation and add physically computed Blender setup/consequence when motion/contact is relevant. Route: Director physical question -> capable installed simulator/runner -> validated physical run + shared V9 projection -> Manim mechanism and Blender response from that same run -> critical excerpt -> reviewer (physics evidence + visual/audio) -> final assembly.

Rendering may use Blender while another engine computes dynamics. Keyframed poses and kinematic integration remain explicitly labeled alternatives, not silent substitutes for requested physics. Read Blender `core/blender-robotics-simulation-skill/references/evidence.md` for the run contract. Existing evidence enums and the single manifest remain unchanged. Physics validation is separate from schema/style/media gates; missing physical evidence leaves that requirement incomplete.
