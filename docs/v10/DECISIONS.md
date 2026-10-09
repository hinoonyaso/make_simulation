# V10 decisions

## D1 — Keep AI and robotics traces separate

**Decision:** add `ai-mechanism-trace/v1` with its own validator and adapter.

**Evidence:** the current shared validator expects robotics state and geometry. RAG has operation/data/provenance concepts that do not map truthfully to those fields. The new trace passes checks for dimensions, ranks, source references and timing semantics while the robotics validator is unchanged.

**Tradeoff:** consumers that want both domains need an explicit adapter at their boundary rather than one universal schema.

## D2 — Adapt the recorded local RAG run

**Decision:** use the existing Naive RAG execution output, including real E5 vectors, FAISS distance ranks, context and answer.

**Evidence:** the source run contains all required values and stable chunk IDs. Its retrieval is squared-L2 over recorded normalized vectors; the display uses its saved PCA coordinates. No scores or ranks are recomputed for animation.

**Tradeoff:** this reproduces a prior run, not a fresh model execution. Chunking, embedding and retrieval wall-clock times were not captured and are null. Only the recorded LLM generation time is reported.

## D3 — Manim for this RAG slice

**Decision:** use Manim for the 2D chunk, ranking and context transitions; keep Three.js and Remotion optional.

**Evidence:** the key state changes and ranked values are two-dimensional and the local project already has a tested Manim environment. Three.js would add a browser capture dependency without addressing a demonstrated need in this example. Remotion would overlap the existing composition pipeline before a measurable advantage is established.

**Tradeoff:** no 3D embedding-space or cross-renderer benchmark is included.

## D4 — Inject converters into Asset Factory

**Decision:** implement safe local resolve/validate/cache/register/invalidate primitives, but require callers to provide converters.

**Evidence:** no stable converter API or installed toolchain is selected for the repository's range of URDF, Xacro, mesh, MJCF and Blender formats. An implicit conversion could silently lose joint hierarchy or physical meaning.

**Tradeoff:** conversion is not automatic and source/target semantic equivalence is not yet validated.

## D5 — Pin MuJoCo; keep the episode adapter scoped separately

**Decision:** pin the official Python bindings at 3.7.0 and keep a small headless model-load/step smoke command. Defer the robotics episode adapter until control input, state recording and trace validation are implemented.

**Evidence:** MuJoCo 3.7.0 loads the repository's Unitree H1 MJCF and advances 1,000 fixed steps (2 simulated seconds) with finite `qpos`/`qvel`. The asset README records the upstream source and BSD-3-Clause license. No actuator command was applied in this smoke run.

**Tradeoff:** the runtime is ready for adapter work, but Robot-arm scenario B and a trace-backed physical animation remain NOT_RUN. The H1 smoke run confirms engine/model compatibility only; it does not verify dynamic fidelity or a controller.
