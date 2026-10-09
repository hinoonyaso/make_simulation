# V11.3 integration report

Run date: 2026-10-10 (Asia/Seoul). Baseline commit: `6012fe4a532cb1e0dd7ab2399ba958a60a7ded62`. Changes are local and unpushed. Pre-existing untracked pilot assets were preserved.

## Result

V11.3 common CLI integration and local technical validation are complete for the existing Quantization, NMS, PID, Self-Attention, RAG, H1 Blender, and YOLO paths. This is not a narrated delivery or complete motion/educational acceptance: all generated common-CLI clips are silent; only selected real frames were inspected. GitHub Actions was updated but not run remotely.

## Implementation

- RAG now selects the child report's `preview` or `final` entry according to the request, rejects missing/failed media, validates actual dimensions, 30 fps and full decode, and verifies the copied output hash. A missing 1080p final cannot be reported as success.
- Storyboards declare phase IDs and the common Manim scene resolves transitions by ID. The contract rejects absent, duplicated, unmapped or unused phase mappings. NMS omits IoU comparison when the trace has no comparisons and still renders the zero-kept final state.
- Cache identity includes render-affecting source fingerprint, requested/effective renderer, settings, trace/config hashes, and RAG manifest. Reuse requires the report, expected in-run output path, media hash/metadata, dimensions, nominal fps, codec, duration/frame count and full decode to match.
- The common CLI invokes the existing H1 MuJoCo trace exporter and Blender mesh renderer for `robot_kinematics --robot unitree_h1 --render blender`. The exporter verifies qpos joint names/order and limits and records the MuJoCo-to-Blender frame/unit mapping; Blender rejects unsupported mapping. This is validated trace playback with interpolated states, not another physics simulation.
- `object_detection` is a distinct real YOLO11n adapter. Inference executes in an isolated process with pinned runtime/checkpoint identity; replay validates the source image hash. The existing image-space renderer uses the recorded boxes and the storyboard phase contract.
- The H1 overlay's muted text was darkened and moved above the graph column after sampled-frame review found low contrast and an overlap with the robot head.
- Manual GitHub Actions integration runs pinned unit tests and real preview renders for RAG, quantization, quantization replay, self-attention, NMS's all-rejected boundary and MuJoCo regression; videos are uploaded as workflow artifacts.

## Executed evidence

| Path | Run ID / renderer | Media | Technical result |
|---|---|---|---|
| `/tmp/v113-quant-final/quantization-85f5b18257f83cb71618/preview.mp4` | `quantization-85f5b18257f83cb71618` / Manim | 960×540, H.264, nominal 30 fps, 14.4 s, 432 frames | Full decode PASS |
| `/tmp/v113-quant-replay/quantization-4161b183556c757f436b/preview.mp4` | `quantization-4161b183556c757f436b` / Manim replay | 960×540, H.264, 30 fps, 14.4 s, 432 frames | Full decode PASS; same trace values |
| `/tmp/v113-nms-effective/nms-470397987f6715467a1b/preview.mp4` | `nms-470397987f6715467a1b` / Manim | 960×540, H.264, 30 fps, 12.5 s, 375 frames | Full decode PASS; final frame says confidence pass 0/2 and kept 0 |
| `/tmp/v113-pid-final/mcu_pid-899701d6b2a40f041119/preview.mp4` | `mcu_pid-899701d6b2a40f041119` / Manim | 960×540, H.264, 30 fps, 14.0 s, 420 frames | Full decode PASS |
| `/tmp/v113-attention-final/self_attention-a54c84b7137f81de28e0/preview.mp4` | `self_attention-a54c84b7137f81de28e0` / Manim | 960×540, H.264, 30 fps, 27.165 s, 815 frames | Full decode PASS |
| `/tmp/v113-rag-repro/final-check/rag_render/rag-4a6652b4f8/rag_video_preview.mp4` | `final-check` / Manim | 960×540, H.264, 30 fps | Full decode PASS |
| `/tmp/v113-rag-repro/final-check/final.mp4` | `final-check` / Manim | 1920×1080, H.264, nominal 30 fps, 34.194 s, 1026 frames | Full decode PASS; SHA-256 checked; repeat request returned `REUSED` |
| `/tmp/v113-h1-final-reviewed/robot_kinematics-35bb08f72e2d62785581/preview.mp4` | `robot_kinematics-35bb08f72e2d62785581` / Blender 5.2.1 H1 mesh trace playback | 960×540, H.264, 30 fps, 2.033 s, 61 frames | Coordinate mapping, provenance and full decode PASS |
| `/tmp/v113-yolo-phase-current/object_detection-25e363bf3652e28f087a/preview.mp4` | `object_detection-25e363bf3652e28f087a` / Ultralytics YOLO11n 8.3.0 + Manim image-space | 960×540, H.264, 30 fps, 12.7 s, 381 frames | Fresh inference and full decode PASS; 6,300 raw, 70 trace candidates, 47 confidence passes, 5 final detections |
| `/tmp/v113-yolo-phase-replay/object_detection-7e49d2e39d21a5a86ace/preview.mp4` | `object_detection-7e49d2e39d21a5a86ace` / Manim replay | 960×540, H.264, 30 fps, 12.7 s, 381 frames | Replay and full decode PASS |

RAG's independent preview and final files were separately generated and validated. The preview is under `final-check/rag_render/rag-4a6652b4f8/rag_video_preview.mp4`; the final is the run-root `final.mp4`. A second identical RAG final request returned `REUSED`. NMS's identical repeat request also returned `REUSED`.

## Verification

- Baseline suite before edits: 66 tests passed.
- Final suite: `uv run python -m unittest discover -s tests -v` — 79 tests passed.
- Compile: `uv run python -m compileall -q core/mechanism scripts/produce_video.py tests pilots/v10_rag_poc pilots/v11_2_h1_blender pilots/v11_2_yolo` — PASS.
- Scene style: RAG, YOLO and Blender files PASS. Common Manim scene exits successfully with heuristic warning `FadeOut x17 > continuity primitives x8`.
- Workflow YAML parse — PASS. `git diff --check` — PASS.
- Replay/cache: quantization replay PASS; YOLO replay PASS; identical RAG and NMS runs were reused only after cache validation.
- Sampled real frames reviewed: RAG at 8, 17, 25, 33 seconds; NMS final state; YOLO suppression state; H1 after overlay correction. No blocker/high issue was visible in these inspected stills.

## Not run / limitations

- Remote GitHub Actions: **NOT_RUN**. No remote run/dispatch credential or `gh` CLI is available here, and the working tree has not been pushed. Run the manual workflow at `https://github.com/hinoonyaso/make_simulation/actions/workflows/ai-video-integration.yml` after the changes are pushed through the user's normal process.
- Continuous normal-speed motion review, audio review, novice comprehension and complete educational acceptance: **NOT_RUN**. The current clips are silent technical previews/renders.
- H1 is a 2.033-second excerpt and replays MuJoCo-generated states; it does not integrate physics in Blender.
- Local shell warns that SoX is absent; it does not block silent Manim renders. Blender 5.2.1 emits `Material.use_nodes` deprecation warnings and STL duplicate-triangle import warnings; render and decode passed.
- No push, commit, subtitle/TTS edit, upload, new environment download or pilot deletion was performed.
