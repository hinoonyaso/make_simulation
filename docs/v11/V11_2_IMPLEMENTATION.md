# V11.2 implementation notes

## Baseline and scope

- Repository baseline was HEAD `86a1115227f76c9847967dca0168013398ab5cf0`, branch `main` synchronized with `origin/main` at task start.
- The V11.1 baseline ran 48 local tests. The previous `ai-trace.yml` selected `test_ai_*.py` and `test_v11_mechanism.py` but omitted `test_mujoco_simulation.py` (2 tests), explaining the 46-vs-48 difference.
- Existing pilot media, traces, and user-owned untracked files were left untouched. New renders, image and model assets were written under `/tmp`. No world/map was downloaded. Ultralytics 8.3.0 was supplied transiently with `uv run --with`; project dependencies were not changed. No push was made.

## Run management and replay

`core/mechanism/run_management.py` forms IDs from topic, normalized request/config, trace, renderer mode, adapter contract, code revision/fingerprint, and model asset information embedded in the trace. The run directory stores `request.json`, `config.json`, `trace.json` (or `ai_trace.json` for RAG), `visual_plan.json`, `visual_manifest.json`, media and `production_report.json`. Same-identity completed media is reused only after another 30 fps full-decode check. A failed or colliding run is preserved and refused. `--force` creates a timestamped sibling; it does not overwrite a prior run.

Replay checks the expected schema and mechanism identity, then calls the registered domain validator before visualization. Existing V9 robotics traces identify their model through `model.asset_id`; V10 RAG traces identify their family through `system.family`. These contracts allow older traces without a top-level topic field to be validated without rewriting their source. Quantization traces from the earlier V11 envelope may omit `scope` and clipping metadata; codes, scale, zero point, reconstruction and absolute error are still checked. New traces continue to validate clipping metadata when it is present.

## Dynamic storyboard and visuals

The fixed `BEAT_COPY` table was removed from the common CLI. `core/mechanism/storyboard.py` derives phases from domain trace operations and state: quantization uses three or four beats depending on activation data; NMS shows candidate, confidence-filter, IoU-comparison and result states; Attention uses five states from Q/K/V projection through weighted output, with masking called out when present. PID and H1 use their recorded time/state stages. Beat duration is marked as an estimate unless a measured total narration duration is provided. Supplying `--narration-duration` distributes that measured duration over the selected phrases; it does not create audio.

The Manim scene now labels integer codes, shows separate activation values in weight-plus-activation mode, fades confidence-rejected NMS candidates before IoU comparisons, and synchronizes moving markers on the PID encoder and PWM curves. Attention begins with the actual token and projected Q/K/V vectors before transforming score matrices. Existing H1 replay remains a stylized Manim graph from the stored MuJoCo run.

## CI and capability boundaries

`ai-trace.yml` now includes the MuJoCo regression tests and V11.2 run/storyboard tests, making its test selection match the complete local suite. The manual render workflow uses a configurable Manim executable (`V11_MANIM_BIN=manim`), renders Attention and Quantization, replays a newly generated trace, full-decodes through the CLI, and uploads preview artifacts. The workflow file was not run on GitHub during this task.

The Windows host has Blender 5.2.1 at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`. WSL interop launch failed through the ordinary shell route, but the installed executable ran via the session's approved host execution route. The actual 1920×1080, 30 fps H1 mesh render is `/tmp/v112_h1_blender/h1_trace_blender.mp4`; source trace validation, MuJoCo mesh export, Blender render, full decode, and scene-style check passed. The rendered motion is recorded MuJoCo `qpos` interpolation; Blender did not run physics again. Details: [H1 Blender pilot](../../pilots/v11_2_h1_blender/README.md).

YOLO was run against the official YOLO11n checkpoint and official Ultralytics bus sample, both downloaded to `/tmp` and hash-recorded. The adapter captured the actual pre-NMS tensor, reconstructed the class-aware NMS trace, and verified all five final boxes against Ultralytics output. The run had 6,300 raw predictions, 70 candidates above a 0.05 trace display floor, 47 above confidence 0.25, and 5 final detections. The 12-candidate teaching overlay is capped independently from the full inference. The final 12.70-second 1920×1080, 30 fps Manim preview is copied to `pilots/v11_2_yolo/output/yolo11n_inference_trace.mp4`; delivery full-decode passed. The scene is explicitly a 2D image-space detection trace, not depth reconstruction or robot simulation. Ultralytics was transient, not made a mandatory project dependency. Its model/runtime license is recorded in the [YOLO pilot README](../../pilots/v11_2_yolo/README.md).

The common CLI still emits silent technical media. `core/narration/prepare_audio.py`, Whisper caption timing, render Reviewer and delivery tools remain available as separate V9 stages, but the common V11.2 CLI does not orchestrate them into a verified full-production result. No TTS request was sent to an external service. Narration, sentence captions in the MP4, reviewer report, final narrated render, and L4 are therefore **NOT_RUN / not integrated**.

YOLO is **NOT_RUN**. There is no ready object-detection adapter or locally pinned detector model/runtime; `nms` remains synthetic candidate arithmetic and is not labeled inference.

## Validation record

Validation was run locally from the repository root on 2026-10-09.

- Full unit suite: **PASS**, 66 tests (`uv run python -m unittest discover -s tests -v`). This includes schema/domain tampering, run identity partitioning, reuse/output preservation, legacy replay, storyboard, and object-detection adapter tests.
- Compile check: **PASS**, `uv run python -m compileall -q core/mechanism scripts/produce_video.py tests`.
- `git diff --check`: **PASS**.
- Workflow YAML parse: **PASS**, both changed workflow files parsed with Ruby YAML. GitHub Actions itself was not triggered.
- Manim style checker for the new YOLO scene: **PASS** (no warning). The common mechanism scene still has its historical heuristic warning, `FadeOut x17 > continuity primitives x8`.
- Actual 960×540, 30fps H.264 silent previews, visual manifest checks and full decodes: Quantization weight+activation `/tmp/v112_final_quant/quantization-d1f41af2fcfa0ae1af84/preview.mp4`; Quantization replay `/tmp/v112_final_replay/quantization-30f9f5b4c743422a8c25/preview.mp4`; NMS confidence rejection `/tmp/v112_final_nms/nms-8c6e0a6abd3992b855f1/preview.mp4`; empty NMS `/tmp/v112_empty_nms/nms-ad413e7b5e4f36ccc51c/preview.mp4`; PID `/tmp/v112_final_pid/mcu_pid-fc7888c8ba3db5d1b1ab/preview.mp4`; Attention `/tmp/v112_final_attention/self_attention-5ed4c97591784f60bcae/preview.mp4`; legacy H1 trace replay `/tmp/v112_final_h1/robot_kinematics-994bc4b535bc3860066c/preview.mp4`; new MuJoCo trace preview `/tmp/v112_h1_physics/robot_kinematics-7df1b8bda1b5a0ff641e/preview.mp4`; RAG trace replay `/tmp/v112_final_rag/rag-9e52e6eb83b7ad2c079f/preview.mp4`.
- Cache reuse: **PASS**; repeating an identical quantization request reused its prior media after full decode.
- H1 Blender render style: **PASS**, `uv run python scripts/check_scene_style.py pilots/v11_2_h1_blender/render_trace.py`.
- YOLO model trace and inference/runtime agreement: **PASS**; `/tmp/v112_yolo/trace.json`, 6,300 raw model predictions and 5 runtime-matched final detections. The adapter-specific tests pass (3 tests).
- YOLO preview: **PASS**, 1920×1080 H.264, 30 fps, 12.70 seconds, silent, full decode. Actual frames at 3, 6, 10 and 12 seconds were inspected after the final render; see [render review](RENDER_REVIEW.md).
- Render Reviewer sampled-frame pass: **INCOMPLETE**. Extracted and inspected actual stills: NMS 8s, empty NMS 5s, PID 8s and 12s, Attention 2s/16s/25s, Quantization 18s. No blocker/high issue was visible in those inspected frames. This does not establish comprehension from a first-view unvoiced excerpt, motion continuity/pacing, audio quality, or learner understanding. Findings and the review scope are recorded in [sampled render review](RENDER_REVIEW.md); extracted images remain in `/tmp/v112_review_*`.
- GitHub Actions remote run: **NOT_RUN**.
- Full narrated production/audio-caption sync and end-to-end Reviewer orchestration: **NOT_RUN / not integrated**.
- Blender render was completed on the installed Windows host executable through the approved host execution route. Ordinary WSL interop invocation remains an environment inconvenience; it is not an installation blocker.
- Full narrated episode, TTS, sentence-timed captions, reviewer workflow orchestration, and YouTube-ready delivery: **NOT_RUN / not integrated**. The YOLO and H1 outputs are silent technical excerpts, not final education episodes.

## Decision and trade-off

Run identity uses deterministic content hashes and immutable output directories rather than mutating the old fixed per-topic output paths. This preserves prior outputs and makes renderer/config changes explicit. A failed run can leave an incomplete directory; it is intentionally not silently deleted or reused, and the user can select a fresh run ID/output root. The fingerprint includes shared adapter sources, so a relevant code update creates a new identity rather than reusing stale media. Legacy traces are validated from their recorded schema/model data instead of migrating or changing existing pilot artifacts.
