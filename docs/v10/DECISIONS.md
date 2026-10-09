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

**Decision:** use Manim for the 2D chunk, ranking and context transitions, then add a separate Three.js 3D PCA view for the embedding-space experiment. Defer Remotion.

**Evidence:** Manim is effective for the main data flow and exact score display. Three.js adds a genuine 3D spatial view of 384D data projected into 3D, which supports depth/orbit exploration. The real browser render produced 29 WebGL draw calls and an 8-second 1080p30 MP4 from the same trace.

**Tradeoff:** Three.js needs Node, browser and capture tooling; its 3D distances cannot stand in for original 384D retrieval. This is a short video-only experiment. Remotion would duplicate a fixed composition already produced by browser capture and FFmpeg.

## D4 — Inject converters into Asset Factory

**Decision:** implement safe local resolve/validate/cache/register/invalidate primitives, but require callers to provide converters.

**Evidence:** no stable converter API or installed toolchain is selected for the repository's range of URDF, Xacro, mesh, MJCF and Blender formats. An implicit conversion could silently lose joint hierarchy or physical meaning.

**Tradeoff:** conversion is not automatic and source/target semantic equivalence is not yet validated.

## D5 — Pin MuJoCo; keep the episode adapter scoped separately

**Decision:** pin the official Python bindings at 3.7.0 and implement a fixed-base H1 arm physics adapter with a reproducible trace and Manim playback. Keep the system-level GUI/Blender path separate.

**Evidence:** MuJoCo 3.7.0 runs the repository's H1-with-hand MJCF for 2 simulated seconds with PD torque commands. The V9 robotics trace validator passes; recorded hand poses match a separate FK pass; repeated runs match to 1e-12; the 2 ms/1 ms sensitivity difference peaks at 0.107 mm. The asset README records upstream provenance and BSD-3-Clause license.

**Tradeoff:** the fixed pelvis, ideal PD motor control and absent floor/contact objective limit the physical claim. Blender mesh rendering and hardware/controller fidelity remain unverified. The Manim scene is an explicit stylized replay of the actual trace.


## D7 — Use a deterministic Three.js capture for the 3D projection PoC

**Decision:** pin Three.js and Playwright in a pilot-local Node project; compute PCA from the saved vectors in Python; render fixed timestamps in headless Chromium; assemble frames with the repository's FFmpeg.

**Evidence:** the browser loads the locally generated projection tied to the AI trace hash, renders all 12 points and the actual top-three links, and reports 29 draw calls. `validate_delivery.py` passes the generated 1920×1080, 30 fps H.264 file.

**Tradeoff:** this produces a video-only 8-second component test, not a narrated episode or a substitute for the 34-second Manim explanation. Browser capture requires a user-level Playwright Chromium download and a host that permits Chromium to start. Remotion is held until a variable React timeline/composition is needed.
