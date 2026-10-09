# V10 architecture (implemented slice and target)

## Data flow

```text
Topic / existing production manifest
        │
        ├── robotics topic → existing robotics trace → existing renderers
        │
        └── AI topic → algorithm execution record → AI trace adapter
                                      │
                              AI trace validator
                                      │
                    reusable deterministic RAG primitives
                                      │
                          Manim / optional Three.js
                                      │
                 technical QA + educational frame review
                                      │
                         audio/captions + delivery QA
```

Simulation and rendering remain separate. The RAG PoC adapts a recorded algorithm run; the scene reads only `ai_trace.json`. A display projection is explicitly marked lossy and never replaces the original retrieval scores. Presentation time is distinct from execution time.

## AI trace contract

`ai-mechanism-trace/v1` has inputs, operations, state transitions, intermediate values, outputs, provenance and visualization metadata. Operation timing is nullable. A saved model execution retains only source-measured times; the new local lexical execution measures its retrieval loop and labels the implementation. Vector dimensions are data-driven. Squared-L2 traces sort ascending; generic retrieval scores declare their metric and ascending/descending direction. Source chunk IDs are preserved through retrieval and context assembly.

This contract is additive. `core/shared-data/validate_trace.py` remains the validator for robotics traces.

## RAG primitives and renderer

`core/ai-mechanism/primitives.py` supplies deterministic chunk-window, top-k selection and context assembly helpers with explicit source IDs. `rag_visual_data.py` discovers actual chunk ranges, all overlaps, vectors, score direction and ranked IDs. The Manim scene consumes this trace-derived data and the V9 beat durations; it does not name specific chunk IDs or assume squared L2. Dense source ranges are sampled for legibility, with overlap IDs retained. The score and context views keep recorded identities and values.

Two data paths are implemented: replay a validated saved AI trace, or execute local character chunking → TF-IDF lexical feature generation → cosine similarity ranking → context assembly. The latter requires no model download or external service, and the trace/video disclose that these are lexical features, not semantic embeddings. It performs no answer generation. Other standalone AI topics are rejected until implemented.

`scripts/produce_ai_video.py --topic rag` connects the Director to trace validation, one V9-compatible beat manifest, Manim preview, decode QA and final render. `--render auto` adds the trace-matched Three.js segment if recorded vectors and local browser tooling are ready. Segment duration/position come from manifest beat 2. Cache reuse checks the trace hash, rendering code, locked browser dependencies and output settings. When Three.js fails, `renderer_selection.json` records the reason and retains a complete Manim path. TTS is not invoked automatically. Optional narration uses a full measured audio timeline rather than fixed beat IDs or audio windows.

## Asset Factory

`core/visual-assets/asset_factory.py` wraps the existing JSON registry. It resolves paths within the project root, hashes files, validates optional declared hashes, reuses a content-addressed conversion cache, stages injected conversions safely, registers metadata atomically, and invalidates per-asset cache entries. It deliberately has no implicit downloader or guessed converter. Automatic `package://` resolution, Xacro expansion, joint/limit and mesh topology checks, format conversion implementations, remote source revision fetching and license policy enforcement remain future work.

## Deferred target modules

- MuJoCo environment is pinned at 3.7.0 and a headless Unitree H1 model smoke run is available through `scripts/smoke_mujoco.py`. The local adapter records joint/body state and emits a V9-compatible robotics trace projection; a fixed-base H1 arm PoC and Manim trace playback are implemented. Blender mesh replay, hardware/control-system fidelity and full manifest integration remain future work.
- Three.js: an optional 3D PCA display consumes the same validated query/chunk vectors and recorded ranking. PCA is explicitly lossy; it does not choose retrieval results. The browser capture and timeline are runtime-configurable. Remotion remains deferred.
- Fresh local RAG execution is lexical only. Semantic embedding models and LLM answer generation remain future work; unsupported mechanisms are rejected rather than routed to this lexical path.
