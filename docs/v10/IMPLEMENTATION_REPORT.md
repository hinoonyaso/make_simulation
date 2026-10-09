# V10 implementation report

## Status

Phase 0 audit: **PASS** for the reviewed baseline and recorded constraints.

Phase 1 AI trace + RAG PoC: **PASS** for the local saved-run vertical slice and rendered media gates. This is a replay/adaptation of a real prior local run, not a fresh full pipeline invocation.

Phase 2 Asset Factory: **PARTIAL**. Safe local registry resolution, file hashing, cache reuse/invalidation, injected conversion and atomic registration work; format-aware robot model validation and network resolution are not implemented.

Phase 3 MuJoCo: **ENVIRONMENT PASS / ADAPTER NOT_RUN**. MuJoCo 3.7.0 is pinned, and the bundled Unitree H1 MJCF loaded and ran for 1,000 headless steps with finite joint state. No actuator control, V10 trace recorder, FK comparison or Blender playback was implemented. Blender CLI remains unavailable.

Phase 4 Three.js/Remotion: **DEFERRED**. No configured browser/video capture path; Manim is suitable for this 2D trace visualization.

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
- MuJoCo-controlled robot-arm run/trace, Blender render, Robot-arm scenario B, fresh RAG execution, full normal-speed listening, and learner comprehension: **NOT_RUN**. The separate headless engine smoke check passed.

## Generated artifacts

- Video: `pilots/v10_rag_poc/output/rag_mechanism_poc.mp4`
- Preview: `pilots/v10_rag_poc/output/rag_mechanism_poc_preview.mp4`
- Trace: `pilots/v10_rag_poc/data/ai_trace.json`
- Captions: `pilots/v10_rag_poc/output/caption_timing.json` and `subtitles.ko.srt`
- Provenance: source run path and SHA-256 are stored in the trace.
