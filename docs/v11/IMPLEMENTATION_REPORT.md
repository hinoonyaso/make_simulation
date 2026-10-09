# V11.1 implementation report

> **V11.3 current status:** The integration work at baseline `6012fe4` and its local evidence are recorded in [V11.3 integration report](V11_3_INTEGRATION_REPORT.md). This file remains the historical V11.1 baseline; use the dated [test results](TEST_RESULTS.md) and [render review](RENDER_REVIEW.md) sections for current V11.3 state.

> **V11.2 follow-up:** run management, validated replay, trace-driven storyboards and visualization updates are recorded in [V11.2 implementation notes](V11_2_IMPLEMENTATION.md). The V11.1 report below is the prior baseline; its statements about fixed output paths/replay should be read as historical.

Baseline HEAD before edits: `36e8a85` (`Build V11 universal mechanism video pipeline`); branch `main`, matching `origin/main`. Existing untracked pilot content was preserved. No commit or push was made.

## Correctness and routing

- Fixed asymmetric affine quantization by including real zero in every calibration interval before deriving scale and zero point. Previously `[1, 2]` could collapse at a clipped zero point; positive-only and negative-only regression tests now verify code range, scale, zero point and dequantization. Added saturation metadata and deeper trace checks.
- Preserved Hangul in registry normalization; added explicit Korean aliases; exact canonical topics take priority; shared `attention` resolves as ambiguous with self/cross/multi-head candidates.
- The manifest trace dispatcher now calls topic-specific validators for ready `mechanism-envelope/v1` adapters. NMS recomputes confidence filtering, greedy order, every IoU and kept IDs. PID validates sample times, PID equation terms, saturation, first-order plant transitions, encoder count/speed and summary values.
- Added a NumPy single-head Self-Attention adapter and visual route for Q/K/V, QKᵀ, scaling, optional causal mask, softmax and weighted values. It is explicitly educational arithmetic; it does not run trained weights or an LLM.

## Visual work

- Quantization marker positions now follow calibrated real/code intervals. Removed zero-opacity initialization that hid later FadeIn objects.
- NMS reveals each recorded winner/candidate IoU decision through one changing label; final kept IDs are visible.
- PID response curves draw progressively over the sampled trace timeline.
- Attention score cells transform through scaled scores into row-normalized weights while retaining Q/K identity; output rows show V values.
- Four mechanism MP4 previews plus a positive-only asymmetric quantization regression preview were rendered and full-decoded; deterministic frame review found and fixed the NMS label overlap, quantization visibility, and slow unreadable attention text interpolation. The record is in [render review](RENDER_REVIEW.md). That sampled frame review does not certify full-speed pacing or learner comprehension.

## Environment and production boundaries

- Added a separate environment registry and preflight loader plus `manage_assets.py search --category environment`. Added a pinned HTTPS archive fetch/extract helper requiring an allowlisted host, source revision, declared size and SHA-256; it enforces a 100 MiB default limit, rejects unsafe archive paths/links/special files and never runs downloaded scripts. A mocked end-to-end download verifies hash checking, staging/atomic installation and verified-cache reuse; it does not claim an external source was downloaded.
- No environment archive is registered with enough provenance metadata to fetch. Clearpath Office, ManiSkill PickCube and robosuite Lift remain not downloaded and not READY. ROS 2/Gazebo/SAPIEN are absent; MuJoCo exists but robosuite does not. Installing robosuite failed because PyPI DNS was unavailable. No external asset was acquired.
- YOLO/object detection remains planned, separate from synthetic NMS. Narration, captions, reviewer automation and final delivery are still not connected to the common V11 CLI; it remains silent technical rendering and cannot claim L4.

## Basis and tradeoffs

Zero-inclusive affine calibration was chosen over clipping the zero point because the integer representation must preserve real zero and the full one-sided input range; the regression cases exercise both signs. Attention was implemented before YOLO because it requires no model download, can be verified from first principles and produces all requested intermediate tensors, while this runtime has no ONNX Runtime/vision dependency and no network access to acquire a model. The environment catalog deliberately records incomplete licensing and dependency closure instead of treating an SDF/task name as a reproducible environment. The Clearpath repository documents ROS 2 Jazzy/Gazebo Harmonic and its worlds; ManiSkill documents its Linux/WSL runtime support and separates framework licensing from third-party assets. Current research links are recorded in `docs/v11/environments/ENVIRONMENT_CATALOG.md`.

## Not complete

The V11.1 overall mission is **partially implemented, not complete**. The required two actual downloaded/loaded/running environments, robot-in-world preview, real YOLO inference, full narration/reviewer/delivery pipeline, complete robotics/other-domain validators, and actual whole-video motion playback review remain blocked or unimplemented. No CI workflow ran remotely in this turn. Reproduction commands and statuses are in [test results](TEST_RESULTS.md).
