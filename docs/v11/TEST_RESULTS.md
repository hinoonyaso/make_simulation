# V11.2 local validation results

## V11.4 local validation (2026-10-10)

| Check | Status | Evidence |
|---|---|---|
| Full regression suite | PASS | `uv run --offline python -m unittest discover -s tests -v` — 87 tests passed, including commit-only cache reuse. |
| Compile / diff whitespace | PASS | Changed Python packages and scenes compile; `git diff --check` clean. |
| Shared timeline and routing tests | PASS | Frame rounding, phase continuity, source mapping, invalid ranges, renderer choice/fallback, explicit Blender block, and renderer/timeline cache partition covered in `tests/test_v114_timeline_routing.py`. |
| Quantization Manim preview | PASS | `/tmp/v114-final-quant/quantization-1e64a469f70189111216/preview.mp4`; 432 frames, 14.4 s, 960×540, 30 fps, final full decode. |
| YOLO image-space preview | PASS | `/tmp/v114-final-yolo/object_detection-19ed95ad9457498f09dc/preview.mp4`; 468 frames; each of four phases uses 117 frames; 960×540, 30 fps, final full decode. |
| H1 comparative Manim preview | PASS | Explicit `comparative_analysis` selected Manim; 960×540, 30 fps, full decode. |
| H1 motion Blender preview | PASS | `/tmp/v114-final-h1/robot_kinematics-d8b94a256468edf69206/preview.mp4`; Auto selected Blender 5.2.1; 2.0 s MuJoCo source trace mapped across 11.7 s/351 presentation frames; H1 mesh, full model asset hash, and final full decode recorded. Executed in approved local context because normal WSL interop failed. |
| RAG Manim-only fallback preview | PASS | Four-phase timeline retained; 1,020 frames, 34 s, 960×540, full decode; feature loss recorded when ordinary local loopback capture was blocked. |
| RAG Manim + Three.js preview | PASS | `/tmp/v114-final-rag/rag-b3d854b04e3ffab771e3/preview.mp4`; exact embedding interval `[255, 510)` at 30 fps; 1,020 frames total; final full decode. Boundary stills 254/255 and 509/510 inspected. |
| YOLO and H1 sampled phase frames | PASS, scoped | YOLO stage boundaries and H1 mesh/trace display samples inspected. This is not whole-video or audio review. |
| Remote GitHub Actions | NOT_RUN | Workflow includes the V11.4 unit test command, but was not dispatched. |
| Audio/listening and learner comprehension | NOT_RUN | Renders are silent technical previews. |

Detailed artifact paths and environment caveats are in [V11.4 integration report](V11_4_INTEGRATION_REPORT.md).

Run from `/home/sang/make_simulation` on 2026-10-09. These are local results; GitHub Actions has not run.

| Check | Status | Evidence |
|---|---|---|
| Full unit/regression suite | PASS | `uv run python -m unittest discover -s tests -v` — 63 tests passed |
| Quantization one-sided/constant/INT4/INT8/per-channel regression | PASS | `tests.test_v11_mechanism`; affine reconstruction and tampered-code rejection |
| Korean aliases / ambiguity | PASS | Korean mappings resolve; generic `attention` prints 3 choices and does not choose one |
| NMS and PID stored trace integrity | PASS | tampered IoU and plant samples rejected; PID validates controller equation and encoder values |
| Self-Attention arithmetic and replay validation | PASS | Q/K/V, scaling, causal mask, row softmax and outputs; corrupted output rejected by both adapter and manifest validator |
| Environment preflight and safe archive pipeline | PASS | candidates stay not-ready; path traversal, symlink and expanded-size tests rejected; mocked HTTPS fetch verifies hash, atomic extraction and cache reuse |
| V10 AI trace and V9-compatible manifest | PASS | `scripts/validate_ai_trace.py .../ai_trace.json`; `validate_visual_manifest.py .../visual_manifest.json` |
| Manim style gate | PASS with warning | `uv run python scripts/check_scene_style.py core/mechanism/manim_scene.py` exits 0; heuristic warns `FadeOut x17 > continuity primitives x8`. |
| Python compile | PASS | `uv run python -m compileall -q core/mechanism scripts/produce_video.py tests` |
| Quantization weight+activation preview | PASS | `/tmp/v112_final_quant/quantization-d1f41af2fcfa0ae1af84/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| Quantization replay preview | PASS | `/tmp/v112_final_replay/quantization-30f9f5b4c743422a8c25/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| NMS confidence rejection preview | PASS | `/tmp/v112_final_nms/nms-8c6e0a6abd3992b855f1/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| NMS empty-candidate boundary preview | PASS | `/tmp/v112_empty_nms/nms-ad413e7b5e4f36ccc51c/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| MCU PID preview | PASS | `/tmp/v112_final_pid/mcu_pid-fc7888c8ba3db5d1b1ab/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| Self-Attention preview | PASS | `/tmp/v112_final_attention/self_attention-5ed4c97591784f60bcae/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| H1 legacy trace replay | PASS | `/tmp/v112_final_h1/robot_kinematics-994bc4b535bc3860066c/preview.mp4`, 960×540, H.264, 30fps, silent, full decode; 2D Manim trace view |
| H1 new MuJoCo trace preview | PASS | `/tmp/v112_h1_physics/robot_kinematics-7df1b8bda1b5a0ff641e/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| RAG saved-trace replay | PASS | `/tmp/v112_final_rag/rag-9e52e6eb83b7ad2c079f/preview.mp4`, 960×540, H.264, 30fps, silent, full decode |
| Sampled rendered-frame inspection | INCOMPLETE | Real extracted frames inspected for NMS, empty NMS, PID, Attention and Quantization; no blocker/high defect observed in those stills. Does not establish complete motion, audio or learner comprehension. |
| Cache reuse after full decode | PASS | Re-running the identical Quantization request reports `REUSED` for `/tmp/v112_final_quant/quantization-d1f41af2fcfa0ae1af84/preview.mp4`. |
| Workflow YAML parse | PASS | Both changed workflow files parsed with Ruby YAML; remote Actions execution was not performed. |
| Clearpath/Gazebo environment load | BLOCKED | `ros2` and `gz` are absent |
| ManiSkill/SAPIEN environment load/render | BLOCKED | `sapien` absent; project matrix lists WSL rendering unsupported; GPU access blocked |
| robosuite Lift load | BLOCKED | robosuite absent; `uv run --with robosuite==1.5.2 ...` failed on PyPI DNS before installation |
| Environment downloads/dependency closure | NOT_RUN | no source candidates yet satisfy revision/hash/size/model license gate |
| YOLO model inference | NOT_RUN | no detector adapter or pinned model; NMS preview remains synthetic |
| Narrated full production / delivery | NOT_RUN | common mechanism CLI remains silent technical render |
| Remote CI | NOT_RUN | workflow definitions updated but not triggered |

V11.2 run identity, cache/reuse, output preservation, legacy replay and storyboard tests are listed in [V11.2 implementation notes](V11_2_IMPLEMENTATION.md). Earlier V11.1 counts and artifact paths above that historical section are superseded by the V11.2 results in this table.

The active V9/V10 tests and checked-in trace checks passed. This suite result does not convert simulator, model, full production or whole-video review blockers into passes.

## V11.3 integration validation (2026-10-10)

Current evidence and exact media paths are consolidated in [V11.3 integration report](V11_3_INTEGRATION_REPORT.md). This section supersedes prior V11.2 status for the capabilities re-run below.

| Check | Status | Evidence |
|---|---|---|
| Baseline regression suite | PASS | Before edits, `uv run python -m unittest discover -s tests -v`: 66 passed. |
| Full regression suite | PASS | After V11.3 edits, same command: 79 passed. |
| Compile | PASS | `uv run python -m compileall -q core/mechanism scripts/produce_video.py tests pilots/v10_rag_poc pilots/v11_2_h1_blender pilots/v11_2_yolo`. |
| Phase contract / NMS zero-kept boundary | PASS | Unit tests verify ID mapping, omitted comparison phase and final zero state; real NMS preview full-decodes and displays 0/2 confidence pass, 0 kept. |
| RAG preview/final selection | PASS | Separate 960×540 Preview and 1920×1080 Final generated from the checked-in trace. Both full-decode; final path/hash/dimensions checked. |
| Quantization executable → replay | PASS | Both common-CLI renders full-decode at 960×540/30; replay uses generated trace. |
| PID / Self-Attention common render | PASS | Both fresh 960×540/30 renders full-decode. |
| H1 common Blender path | PASS | Blender 5.2.1 imported the existing H1 mesh and rendered the validated trace at 960×540/30; payload coordinate map/provenance and decode checked. |
| YOLO common adapter | PASS | Actual YOLO11n 8.3.0 inference plus replay each rendered 960×540/30 and full-decoded. |
| Cache reuse | PASS | Identical RAG final and NMS preview requests returned `REUSED`; cache contract tests also pass. |
| Scene style | PASS with warning | RAG, YOLO and Blender style checks pass. Common Manim style exits 0 but reports `FadeOut x17 > continuity primitives x8`; see render review. |
| Workflow YAML | PASS | Ruby YAML parser loaded `.github/workflows/ai-video-integration.yml`. |
| Remote GitHub Actions run | NOT_RUN | No `gh` CLI/remote dispatch tool or credentials available; changes remain local and unpushed. Workflow URL and instructions are in V11.3 report. |
| Full motion / audio / learner review | NOT_RUN | Sampled stills only; generated common-CLI media is silent. |

## V11.2 resumed Blender and YOLO follow-up (2026-10-09)

The rows above describe the earlier implementation pass and are superseded for these two capabilities by the follow-up below.

| Check | Status | Evidence |
|---|---|---|
| Installed Blender discovery / H1 mesh render | PASS | Windows Blender 5.2.1 at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; actual output `/tmp/v112_h1_blender/h1_trace_blender.mp4`, 1920×1080, 30fps, 2.03s; validated MuJoCo trace and imported H1 mesh rendered, full-decode and Blender style gate pass. Ordinary WSL interop invocation failed; installed executable succeeded through approved host execution. |
| Actual YOLO inference | PASS | Ultralytics 8.3.0 / official YOLO11n on official `bus.jpg`; 6,300 raw predictions, 70 trace candidates, 47 confidence passes, 5 final detections; reconstructed class-aware NMS matched runtime outputs. Checkpoint/image hashes and license are in `pilots/v11_2_yolo/README.md`. |
| YOLO preview | PASS | `pilots/v11_2_yolo/output/yolo11n_inference_trace.mp4`, 1920×1080, H.264, 30fps, 12.70s, silent; `scripts/validate_delivery.py --fps 30 --full-decode` passed. |
| Object-detection adapter tests | PASS | `uv run python -m unittest tests.test_object_detection_adapter -v` — 3 tests passed (class-aware overlap, display limit, malformed model-space box). |
| YOLO Manim scene-style check | PASS | `uv run python scripts/check_scene_style.py pilots/v11_2_yolo/render_scene.py` — no warnings. |
| Sampled YOLO final-frame review | PASS, scoped | Actual frames at 1, 3, 6, 9 and 11s inspected. Final review in `docs/v11/RENDER_REVIEW.md`; initial draft's off-image labels were corrected before final render. |
| Narrated full episode / TTS / sentence captions | NOT_RUN | The two new renders are short silent technical excerpts, not a complete education-video delivery. |

## V11.5 validation (2026-10-10)

Baseline 87 tests passed at `01c4a8f`; the modified local suite passes **114 tests**. Added evidence covers return motion/noise/spikes/units, playback speed and source endpoints, discrete PID boundary states, actual MuJoCo execution reuse, mocked YOLO inference call count, process-level reservations, corruption/incomplete rejection and render timeline tampering. Real YOLO and H1 repeated CLI invocations also report zero adapter calls on hits. Actual H1/PID/YOLO/RAG/Quantization media and exact performance observations are recorded in [V11.5 integration report](V11_5_INTEGRATION_REPORT.md). CI definitions and actual remote CI results are reported separately there.
