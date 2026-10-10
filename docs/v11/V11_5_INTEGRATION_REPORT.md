# V11.5 integration report

Date: 2026-10-10 (KST). Baseline local/remote HEAD was `01c4a8f489e49ab05d2528a4d7433b3fcef85f0a`. New source work is restricted to motion/timeline/cache/render reliability, tests, CI and the requested docs. Existing model assets, old episode sources, original traces, voice/subtitle implementation and unrelated untracked pilots were preserved. No assets were downloaded.

## Implementation and decisions

- Full-trajectory H1 motion evidence replaces endpoint equality; noise/spike/units/wrapped-coordinate policy is in [motion validation](V11_5_MOTION_VALIDATION.md).
- H1 exports per-phase speed/state, and Blender displays hold or 0.51× for the tested motion. An initial label/graph-title overlap found in sampled pixels was corrected and rerendered. The reference hand path no longer grows independently during holds.
- PID render callbacks select one actual discrete sample from the integer-frame timeline; controller values, motor and encoder markers and counters stay synchronized. Both rendered durations use exactly the same source trace.
- Heavy YOLO/H1 execution cache runs before adapters. Atomic complete records, Linux process reservations, corruption/incomplete rejection and force-preserved siblings are implemented. Existing media caching also checks the saved timeline. Cache design/identity/CLI semantics: [cache contract](V11_5_EXECUTION_CACHE.md).
- Changed modules: `core/mechanism/{joint_motion,pid_playback,execution_cache,timeline,renderer_routing,run_management,renderer,manim_scene}.py`; H1/YOLO adapters, existing H1 export/render, MuJoCo runner timing, common and YOLO CLIs. Added frame inspection and technical media gate CLIs, 27 regression tests, and updated both workflows.

## Tests and technical evidence

| Check | Result | Evidence |
|---|---|---|
| Baseline suite | PASS | 87 tests, before edits. |
| Final local suite | PASS | `uv run --offline python -m unittest discover -s tests -v`: 114 tests. |
| Clean tracked-source snapshot suite | PASS | `git archive` of the staged source tree, no local untracked pilots/outputs; 114 tests, same installed project interpreter. This is independent source reconstruction, not a fresh dependency installation. |
| Clean-source real render | PASS | `/tmp/v115-clean-render/quantization-fe0134eec7880f3f5069/preview.mp4`; 432 frames, 960×540/30, full decode. |
| Numerical/frame accuracy | PASS | Return motion/noise/spike/unit/shape/time checks; 0.5×/0.25×/1×/hold/reverse replay; source bounds and last frames; PID PWM/encoder/sample/setpoint/saturation/fps/duration boundaries. |
| Execution reservation/reuse | PASS | Actual MuJoCo adapter spy executes once then zero; YOLO adapter spy skips second inference; two processes reserve one execution; corrupt/incomplete/domain-invalid cache rejection and forced preservation. Real CLI timings below also observe zero calls. |
| PID renderer update evidence | PASS | All 422 and 540 render-update states match the independent frame/sample mapper; identical trace content across video durations. |
| H1 exporter evidence | PASS | All 351 exported frames match phase/source/speed; existing MJCF hash, joint order/limit/FK validation passed. |
| Actual media integration | PASS | Five topics, plus a second PID duration; H.264, 960×540, 30fps, trace/timeline hash agreement, exact frame counts and full decode. Paths below. |
| Scene style | PASS with warning | Blender/YOLO/RAG pass. Common Manim heuristic warns `FadeOut x17 > continuity primitives x3`; PID now uses UpdateFromAlphaFunc, which the heuristic does not count. No whole-video visual pass inferred. |
| Sampled pixel review | PASS, scoped | H1 116/117/175/233/234/350: hold → 0.51× → hold and mesh/graph poses; PID boundary/response samples; YOLO phase transitions; RAG splice frames 254/255/509/510. |
| Whole-video motion playback | NOT_RUN | Numerical updates and sampled pixels only; no claim of continuous perceptual review. |
| Audio/subtitle QA | NOT_APPLICABLE | Explicitly excluded by the V11.5 request. |
| Remote CPU GitHub Actions | PENDING_PUSH | Workflow now discovers every test, including previously omitted YOLO/RAG-selection tests. Update after actual push/run. |
| Remote manual render integration | NOT_RUN | No local GH CLI/API token or connector workflow-dispatch method. Existing manual policy retained. Exact dispatch: `gh workflow run ai-video-integration.yml --repo hinoonyaso/make_simulation --ref main`; then `gh run list --workflow ai-video-integration.yml --repo hinoonyaso/make_simulation`. |

Manual render CI now checks PID render-update states and common trace/timeline/media gates, retaining Quantization/Attention/NMS/replay and RAG rendering. Both PID and RAG MP4s are included in upload artifacts. H1 host Blender and optional YOLO inference were exercised locally; provisioning those remote jobs remains separate.

## Same-host timing observations

Seconds from monotonic timers, one invocation per scenario, same input/settings/runtime. Cold below means computation and rendering executed (forced independent execution preserves the existing cache), **not** cleared OS/disk/library caches. Other local renders were sometimes active; these are observations rather than statistically controlled speedup claims.

| Topic / case | Execute calls | Execution cache | Render cache | Execution stage | Preflight | Render lookup/decode | Render | Total |
|---|---:|---|---|---:|---:|---:|---:|---:|
| yolo / cold | 1 | FORCED | MISS | 3.0173 | 0.7503 | 0.0003 | 6.4294 | 10.2351 |
| yolo / warm | 0 | HIT | MISS | 0.0216 | 1.0604 | 0.0003 | 6.9270 | 8.0201 |
| yolo / hit | 0 | HIT | HIT | 0.0222 | 0.9174 | 0.4968 | 0.0000 | 1.4468 |
| h1 / cold | 1 | FORCED | MISS | 0.6939 | 0.2006 | 0.0003 | 128.6683 | 129.6767 |
| h1 / warm | 0 | HIT | MISS | 0.0908 | 0.1607 | 0.0002 | 126.7918 | 127.1218 |
| h1 / hit | 0 | HIT | HIT | 0.0991 | 0.1881 | 0.3280 | 0.0000 | 0.6815 |

| Topic / case | Adapter execute | Model load/compile | Input identity/hash | Trace validation | Cache lookup |
|---|---:|---:|---:|---:|---:|
| yolo / cold | 2.97482 | 0.02701 | 0.01404 | 0.00130 | 0.01927 |
| yolo / warm | 0.00000 | 0.00000 | 0.01909 | 0.00194 | 0.00044 |
| yolo / hit | 0.00000 | 0.00000 | 0.01834 | 0.00305 | 0.00063 |
| h1 / cold | 0.53687 | 0.22060 | 0.05991 | 0.02234 | 0.02003 |
| h1 / warm | 0.00000 | 0.00000 | 0.06591 | 0.02135 | 0.00342 |
| h1 / hit | 0.00000 | 0.00000 | 0.07397 | 0.02164 | 0.00334 |

Cold adapter times include runtime imports and trace construction; YOLO `model_loading_sec` specifically measures the YOLO constructor. Execution cache hits still hash/validate and preflight. H1 rerender time dominates even when physics is skipped. Per-invocation original JSON evidence is under `output/v115_validation/runs/invocations/`.

## Media and hashes

Paths below are relative to `output/v115_validation/runs/` in this workspace (the existing root `output` symlink resolves under `topics/01_robot_manipulator/output`). Only new V11.5 directories were created. These generated artifacts are ignored by Git.

- `robot_kinematics-e3a17bf64b665fd4bdb2/preview.mp4`: 351 frames, 11.700000 s, 960×540, H.264/nominal 30fps, full decode PASS. Timeline SHA-256 `5eee0bfb6d2c365ae8a1a9c4895a69f97d580103ed2e4654d554afff329fa4cc`; trace file SHA-256 `39e1024d7e8d57943c177fee9a4260fbb1e4976fe7a5c32d238b8a6a35c5a500`.
- `mcu_pid-7149e1d9fc7c4d917eda/preview.mp4`: 422 frames, 14.066667 s, 960×540, H.264/nominal 30fps, full decode PASS. Timeline SHA-256 `bbd1f0589e33b134ada86c313c37cc6302a04ea04f94f42c1d3e3b75648a9a71`; trace file SHA-256 `db8f0e0869d7e567e5d4a3a7ce6200689a5267b940300a0147d7bc95ae7784e8`.
- `mcu_pid-c3dc79d9841cd83b5946/preview.mp4`: 540 frames, 18.000000 s, 960×540, H.264/nominal 30fps, full decode PASS. Timeline SHA-256 `99497cdb835982022cc97ac9b1c1cd42ea392346ef6f2bb00d50d393c23be32c`; trace file SHA-256 `db8f0e0869d7e567e5d4a3a7ce6200689a5267b940300a0147d7bc95ae7784e8`.
- `object_detection-9b9e3fdb9e9e74e87520/preview.mp4`: 468 frames, 15.598047 s, 960×540, H.264/nominal 30fps, full decode PASS. Timeline SHA-256 `2068ab01174246f33815cf107681ffdab144a6180e28fa88258d28b0437359a9`; trace file SHA-256 `676791526eda4a221dfaa332bf833a11eb1adaba0d679853b38a9673e503d3f3`.
- `rag-82aba90540b4e8bc886c/preview.mp4`: 1020 frames, 34.000000 s, 960×540, H.264/nominal 30fps, full decode PASS. Timeline SHA-256 `6bcd80fba2b56487d4a4564e87d5ea0ced09f3c831bb3024adc0a1bc7c127369`; trace file SHA-256 `659912abf75f2cd606b5d603efb9043796aa1abdf4272e9a82c8a0f9fde74921`.
- `quantization-d64601903fc2c6dcb11d/preview.mp4`: 432 frames, 14.400000 s, 960×540, H.264/nominal 30fps, full decode PASS. Timeline SHA-256 `c2ae92e216a15c0c9b9851d29589620e0ed60745a573746bae1bd47c8f603a67`; trace file SHA-256 `75de5e54a2b14fe4c09ca885d59ce5b10e807199eddbb554a9ff3224b910dca1`.

PID short timeline: hold [0,141), response [141,282), replay [282,422). Long timeline: hold [0,171), response [171,362), replay [362,540). The long render uses the existing duration-allocation option at 18 seconds for this technical experiment; no narration was generated or measured. H1: hold [0,117), motion [117,234), hold [234,351). RAG retains Three.js at [255,510), 1,020 total frames, original trace/ranking and query/chunk IDs.

## Remaining conditions

- P0: no unresolved failure in the implemented/tested motion, phase speed, PID state mapping or execution-cache scenarios.
- P1 environment: manual remote render CI is NOT_RUN without workflow-dispatch authentication. Windows Blender and local Chromium rendering required the approved host process context; an ordinary restricted WSL subprocess can still be blocked. Runtime failures remain explicit.
- P2 scope: whole-video perceptual playback was not performed. Motion thresholds are configurable only through the documented metadata/type policy and are not validated against arbitrary real sensors. Native Windows/network filesystem execution locking is not supported by this test evidence. No new world/model/controller/speech capability is implied.
