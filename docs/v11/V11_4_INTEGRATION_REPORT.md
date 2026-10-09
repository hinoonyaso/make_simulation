# V11.4 Integration Report

## Scope

Implements explainable visual-goal routing and a shared integer-frame timeline across the existing Manim, YOLO image-space, H1 Blender trace, and V10 RAG/Three.js paths. No map/model downloads, TTS, caption implementation, or upload behavior is included.

## Baseline facts

- H1 `auto` previously chose Manim; Blender was explicit-only.
- YOLO validated phase names but did not consume each phase's declared time.
- H1 rendered the saved source trace without storyboard-time mapping.
- RAG used four V10 phases and inserted Three.js using accumulated floating-point seconds.
- Run identity already used render-input code fingerprint rather than commit revision; it lacked visual-goal/timeline/runtime/asset dimensions.

## Implemented

- Deterministic visual-goal routing and process-level runtime checks, with decision reason, rejected renderer and feature loss in the report.
- Integer-frame timeline builder, validator and source-time mapper.
- Timeline mappings for common Manim, YOLO, H1 export and RAG/Three.js interval.
- Timeline and renderer/asset dimensions added to run identity; local relevant-code fingerprints remain the source-change boundary.
- Capability preflight CLI, Director guidance, repo routing notes, docs and focused unit tests.

## Validation status (2026-10-10)

| Check | Result | Evidence |
|---|---|---|
| Full regression suite | PASS | `uv run --offline python -m unittest discover -s tests -v` — 87 passed, including commit-only cache reuse. |
| Compile and whitespace checks | PASS | `compileall` on changed Python modules and tests; `git diff --check`. |
| Quantization → Manim | PASS | `/tmp/v114-final-quant/quantization-1e64a469f70189111216/preview.mp4`; 432 frames, 14.4 s, 960×540, 30 fps; final delivery validation and full decode passed. Timeline identity/report hashes match. |
| H1 `comparative_analysis` → Manim | PASS | `/tmp/v114-h1-manim-runs/robot_kinematics-2134dc8873450d8c4aac/preview.mp4`; silent 960×540/30 full decode. |
| H1 `motion_3d` auto → Blender | PASS | `/tmp/v114-final-h1/robot_kinematics-d8b94a256468edf69206/preview.mp4`; Blender 5.2.1, existing H1 model bundle hash recorded, 351 frames, 11.7 s, 960×540/30; final delivery validation and full decode passed. Source trace spans 2.0 s and is mapped to the joint-motion phase as slow motion; setup and end analysis are holds. Timeline identity/report hashes match. |
| YOLO replay → image-space Manim | PASS | `/tmp/v114-final-yolo/object_detection-19ed95ad9457498f09dc/preview.mp4`; real YOLO11n trace replay, 468 frames across four 117-frame phases, 960×540/30; final delivery validation and full decode passed. Timeline identity/report hashes match. |
| RAG spatial auto → Manim + Three.js | PASS | `/tmp/v114-final-rag/rag-b3d854b04e3ffab771e3/preview.mp4`; 1,020 frames, 34 s, 960×540/30; final delivery validation and full decode passed. Three.js replaces exactly frames `[255, 510)` (8.5–17.0 s); segment manifest retains the trace/query/chunk IDs and ranking. Timeline identity/report hashes match. |
| Timeline splice frame review | PASS, scoped | Inspected output frames 254, 255, 509 and 510. The transitions occur at the declared half-open frame boundaries. |
| YOLO phase-boundary still review | PASS, scoped | Inspected frames 116/117, 233/234 and 350/351; stages progress candidates → confidence → IoU → final. |
| H1 sampled pose review | PASS, scoped | Inspected frames 116, 175, 234 and 350; mesh pose, trace cursor, source-time graph and 0.17× annotation are present. |
| Normal WSL Blender preflight | BLOCKED | Windows Blender is found, but an ordinary sandbox invocation fails with `UtilBindVsockAnyPort`. The actual H1 preview passed in the approved local execution context; no renderer fallback was used. |
| GitHub Actions | NOT_RUN | Workflow definitions were updated; no remote dispatch occurred. |
| Audio/listening and learner comprehension | NOT_RUN | V11 technical previews are silent, and sampled frame checks do not establish whole-video comprehension. |

Additional successful V11.4 Manim fallback artifact: `/tmp/v114-rag-common-runs-5/rag-5b59a67860d59ed6f9f3/preview.mp4`, 1,020 frames. Standard sandbox loopback capture was blocked, so the decision recorded the 3D projection feature loss. The elevated local RAG run demonstrated the complete Three.js path. Four final media reports were checked after the timeline-digest fix: each report timeline hash equals the corresponding run-identity timeline hash, and frame count matches the declared timeline total.

The videos and test outputs are local under `/tmp`; no GitHub Actions run or push was performed.
