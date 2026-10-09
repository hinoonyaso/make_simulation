# V10 implementation report

## Status

Phase 0 audit: **PASS** for the reviewed baseline and recorded constraints.

Phase 1 AI trace + RAG PoC: **PASS** for the local saved-run vertical slice and rendered media gates. This is a replay/adaptation of a real prior local run, not a fresh full pipeline invocation.

Phase 2 Asset Factory: **PARTIAL**. Safe local registry resolution, file hashing, cache reuse/invalidation, injected conversion and atomic registration work; format-aware robot model validation and network resolution are not implemented.

Phase 3 MuJoCo: **PARTIAL PASS**. MuJoCo 3.7.0 is pinned. A fixed-base Unitree H1 left-arm run uses closed-loop PD torque control, records 101 samples, checks actual hand body poses through a separate FK pass, compares repeated runs, and passes a 2 ms/1 ms timestep sensitivity check. Manim renders the recorded trace. Blender CLI remains unavailable, so the imported H1 mesh is not rendered. The elbow target tracking error peaks at 0.209 rad; the target and actual curves are both shown.

Phase 4 Three.js/Remotion: **DEFERRED**. Node.js is available, but no local browser/capture runtime is installed. Manim renders the current 2D trace relationship, so no alternative framework was added without a demonstrated benefit.

Phase 5 integration: **PARTIAL / NOT_RUN**. No changes to Director/renderer skills, routing, manifest schema or cross-stage caching. Existing V9 is preserved while compatibility coverage is built around the additive trace.

## Implementation

- Added `core/ai-mechanism/rag_trace.py` to adapt saved Naive RAG runs and validate the independent AI trace contract.
- Added deterministic reusable chunk, top-k and context helpers in `core/ai-mechanism/primitives.py`.
- Added `scripts/build_ai_rag_trace.py` and `scripts/validate_ai_trace.py`.
- Added `core/visual-assets/asset_factory.py` over the existing registry format.
- Added `pilots/v10_rag_poc/` with data trace, Manim scene, render assembly, selected existing narration/captions and a 34-second output.
- Added focused unit tests in `tests/test_ai_mechanism.py`.

## Validation results

- `uv run python -m unittest discover -s tests -v`: **PASS**, 9 tests.
- `uv run python scripts/build_ai_rag_trace.py`: **PASS**, 6 operations.
- `uv run python scripts/validate_ai_trace.py pilots/v10_rag_poc/data/ai_trace.json`: **PASS**, 6 operations and 34 intermediate values.
- `uv run python scripts/check_scene_style.py pilots/v10_rag_poc/rag_mechanism_scene.py`: **PASS**.
- `uv run python core/visual-assets/asset_registry.py validate`: **PASS**, 33 existing entries.
- `python scripts/validate_codex_setup.py`: **PASS**, 10 agent configs.
- `uv run python scripts/smoke_mujoco.py assets/unitree_h1/mjcf/h1.xml --steps 1000`: **PASS**, MuJoCo 3.7.0, 21 bodies, 20 joints, 19 actuators, 2.0 simulated seconds, finite joint state.
- `uv run python scripts/validate_delivery.py pilots/v10_rag_poc/output/rag_mechanism_poc.mp4 --require-audio --fps 30 --audio-manifest pilots/v10_rag_poc/output/audio_manifest.json --caption-timing pilots/v10_rag_poc/output/caption_timing.json --full-decode`: **PASS**, 1920×1080 H.264, 30fps, one audio stream, 34.00 sec, 11 captions, full decode.
- Representative final frames were extracted and reviewed. A card text overflow was found and fixed before the final render. Frame inspection does not establish normal-speed full-video pacing or educational comprehension.
- MuJoCo-controlled robot-arm run/trace, FK check, repeatability, timestep sensitivity and Manim render: **PASS** (see `pilots/v10_mujoco_arm/README.md`). The model has 3–4 self contacts; they are recorded but are not part of the lesson claim. Blender mesh render, Three.js/Remotion capture, fresh RAG execution, full normal-speed listening, and learner comprehension: **NOT_RUN**.

## Generated artifacts

- Video: `pilots/v10_rag_poc/output/rag_mechanism_poc.mp4`
- MuJoCo arm trace-driven video: `pilots/v10_mujoco_arm/output/mujoco_h1_arm.mp4` (9.8 sec, video-only)
- MuJoCo execution data: `pilots/v10_mujoco_arm/data/trace.json` and `numerical_validation.json`
- Preview: `pilots/v10_rag_poc/output/rag_mechanism_poc_preview.mp4`
- Trace: `pilots/v10_rag_poc/data/ai_trace.json`
- Captions: `pilots/v10_rag_poc/output/caption_timing.json` and `subtitles.ko.srt`
- Provenance: source run path and SHA-256 are stored in the trace.
