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

`ai-mechanism-trace/v1` has inputs, operations, state transitions, intermediate values, outputs, provenance and visualization metadata. Operation timing is nullable. Only a source-measured value is populated: the recorded LLM generation time. Chunking, embedding and retrieval runtimes were not recorded and remain null. Embedding vectors and distances are validated for finiteness and matching dimensions; retrieval ranks must be unique and ordered by the recorded squared-L2 score. Source chunk IDs are preserved through retrieval and context assembly.

This contract is additive. `core/shared-data/validate_trace.py` remains the validator for robotics traces.

## RAG primitives and renderer

`core/ai-mechanism/primitives.py` supplies deterministic chunk-window, top-k selection and context assembly helpers with explicit source IDs. The data adapter currently targets the existing `naive-rag-run/v1` record. The Manim PoC shows: (1) document-to-chunk state change, (2) PCA projection of actual embeddings, (3) actual squared-L2 ranking and top-three selection, and (4) those same IDs assembling context. The projection is for display only. The short scene uses real recorded values and retained IDs, not a box-arrow sequence.

Narration is cut from the previously approved Naive RAG episode. Captions are selected from the same episode's measured caption timing. No new speech payload was sent to a TTS service.

## Asset Factory

`core/visual-assets/asset_factory.py` wraps the existing JSON registry. It resolves paths within the project root, hashes files, validates optional declared hashes, reuses a content-addressed conversion cache, stages injected conversions safely, registers metadata atomically, and invalidates per-asset cache entries. It deliberately has no implicit downloader or guessed converter. Automatic `package://` resolution, Xacro expansion, joint/limit and mesh topology checks, format conversion implementations, remote source revision fetching and license policy enforcement remain future work.

## Deferred target modules

- MuJoCo environment is pinned at 3.7.0 and a headless Unitree H1 model smoke run is available through `scripts/smoke_mujoco.py`. The local adapter records joint/body state and emits a V9-compatible robotics trace projection; a fixed-base H1 arm PoC and Manim trace playback are implemented. Blender mesh replay, hardware/control-system fidelity and full manifest integration remain future work.
- Three.js/Remotion: optional rendering experiments behind adapters. Not added because the current 2D data story is covered by Manim; browser capture/video integration is not available for a measured comparison.
- Director integration, cross-stage cache keys, end-to-end manifest routing and reviewer skill updates: Phase 5 follow-up. Existing V9 behavior remains authoritative until compatibility tests exist.
