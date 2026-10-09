# V10 implementation report

## Status

Phase 0 audit: **PASS** for the reviewed baseline and recorded constraints.

Phase 1 AI trace + RAG PoC: **PASS** for the local saved-run vertical slice and rendered media gates. This is a replay/adaptation of a real prior local run, not a fresh full pipeline invocation.

Phase 2 Asset Factory: **PARTIAL**. Safe local registry resolution, file hashing, cache reuse/invalidation, injected conversion and atomic registration work; format-aware robot model validation and network resolution are not implemented.

Phase 3 MuJoCo: **PARTIAL PASS**. MuJoCo 3.7.0 is pinned. A fixed-base Unitree H1 left-arm run uses closed-loop PD torque control, records 101 samples, checks actual hand body poses through a separate FK pass, compares repeated runs, and passes a 2 ms/1 ms timestep sensitivity check. Manim renders the recorded trace. Blender CLI remains unavailable, so the imported H1 mesh is not rendered. The elbow target tracking error peaks at 0.209 rad; the target and actual curves are both shown.

Phase 4 Three.js: **PARTIAL PASS**. A 3D PCA view of 11 actual chunk vectors plus the actual query renders in Playwright Chromium/WebGL; browser checks verify 12 points, 29 draw calls and actual top-three IDs. An independent 8-second 1080p30 MP4 passes full decode. Remotion is **DEFERRED** because this fixed composition has no React timeline requirement and Three.js + FFmpeg already produces the file.

Phase 5 integration: **PARTIAL / NOT_RUN**. No changes to Director/renderer skills, routing, manifest schema or cross-stage caching. Existing V9 is preserved while compatibility coverage is built around the additive trace.

## Stabilization follow-up (2026-10-09)

The previous Phase 5 status above is historical. The follow-up below implements a bounded RAG production path; it does not complete every V10 target.

| Area | Status | Evidence / limit |
|---|---|---|
| AI/Robotics manifest trace dispatch | Implemented; local tests pass | Missing, malformed, unreadable, non-object, unknown-schema, empty and incomplete inputs return clear errors. Robotics regression covered by unit test. |
| Generic RAG scene | Implemented; local tests pass | Chunk IDs/count, ranges, overlap, query/vector dimensions, metric direction and Top-K come from trace data. Datasets A/B/C/D run in unit tests. |
| Fresh Execute mode | Implemented and rendered | New Korean document/query used local TF-IDF lexical vectors and cosine similarity. This is not semantic embedding or LLM execution. |
| Director CLI | Implemented; mock routing tests pass | Supports `rag` only, rejects unsupported topics, and runs validation → preview → technical QA → final. |
| Optional Three.js | Integrated; local browser and MP4 capture passed | Same trace hash, query/chunk IDs, recorded scores and manifest timeline. Auto fallback to Manim is recorded; local fallback was covered through routing tests. |
| GitHub Actions | Workflow definitions updated | Push/PR fast checks and manual render workflow are configured. Remote GitHub Actions were not run in this task. |
| Final video | Rendered and full-decode validated | `pilots/v10_rag_poc/output/runs/rag-dbb54184b8/rag_video.mp4`, 34 s, 1920×1080, 30 fps, H.264, silent. |
| Reviewer inspection | Sampled final frames inspected | No blocker/high defect in the inspected frames. Full normal-speed playback, audio, narration timing and novice comprehension are incomplete/not applicable for this silent render. |

Commands and outcomes for this follow-up:

- `uv run python -m unittest discover -s tests -v`: **PASS**, 27 tests, including existing MuJoCo tests.
- `uv run python scripts/produce_ai_video.py --topic rag --trace pilots/v10_rag_poc/data/ai_trace.json --render manim --preview-only --silent --output-root /tmp/v10_rag_replay_check`: **PASS**, checked-in trace replayed to a 34-second manifest-timed preview and full-decode QA passed.
- `uv run python scripts/check_scene_style.py pilots/v10_rag_poc/rag_mechanism_scene.py`: **PASS**.
- `uv run python scripts/validate_ai_trace.py pilots/v10_rag_poc/output/runs/rag-dbb54184b8/ai_trace.json`: **PASS**, 4 operations / 81 intermediate values.
- `uv run python core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py pilots/v10_rag_poc/visual_manifest.json`: **PASS**.
- `uv run python scripts/validate_delivery.py pilots/v10_rag_poc/output/runs/rag-dbb54184b8/rag_video.mp4 --fps 30 --full-decode`: **PASS**, 1920×1080 H.264, 30 fps, no audio stream, full decode.
- Local `npm run test:browser` and configurable Three.js video capture: **PASS** in Chromium/WebGL, and MP4 capture completed. This is not a GitHub CI result.

The fresh trace has 27 chunks, 214 TF-IDF features, cosine similarity (higher is better), and Top-5 `chunk-004`, `chunk-021`, `chunk-011`, `chunk-022`, `chunk-025`. The Three.js presentation interval is 8.5–17 seconds from the V9 beat manifest. These values are copied from the actual execution trace; PCA coordinates are only a lossy display projection.

No production/render wall-time comparison or static-frame ratio comparison was made. No normal-speed full-video/audio review was performed. The replay and fresh execution commands ran from the current checkout; a separate clean Git clone was not created for this follow-up. Do not label these unperformed checks as PASS.

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
- MuJoCo-controlled robot-arm run/trace, FK check, repeatability, timestep sensitivity and Manim render: **PASS** (see `pilots/v10_mujoco_arm/README.md`). Three.js browser capture and video decode: **PASS**. The model has 3–4 self contacts; they are recorded but are not part of the lesson claim. Blender mesh render, Remotion, fresh RAG execution, full normal-speed listening and learner comprehension: **NOT_RUN**.

## Generated artifacts

- Video: `pilots/v10_rag_poc/output/rag_mechanism_poc.mp4`
- MuJoCo arm trace-driven video: `pilots/v10_mujoco_arm/output/mujoco_h1_arm.mp4` (9.8 sec, video-only)
- MuJoCo execution data: `pilots/v10_mujoco_arm/data/trace.json` and `numerical_validation.json`
- Three.js 3D RAG video: `pilots/v10_threejs_rag/output/threejs_rag_3d.mp4` (8 sec, video-only)
- Three.js projected points: `pilots/v10_threejs_rag/data/embedding_space_3d.json`
- Preview: `pilots/v10_rag_poc/output/rag_mechanism_poc_preview.mp4`
- Trace: `pilots/v10_rag_poc/data/ai_trace.json`
- Captions: `pilots/v10_rag_poc/output/caption_timing.json` and `subtitles.ko.srt`
- Provenance: source run path and SHA-256 are stored in the trace.
