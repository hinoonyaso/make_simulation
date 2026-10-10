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
| Remote CPU GitHub Actions | PASS | Implementation commit `c208f0e3f0dd5f237d547800f4d10d2a12840f45`; [run 38020559616](https://github.com/hinoonyaso/make_simulation/actions/runs/38020559616). Job `114120410443` logs: **114 tests in 4.036 s, OK**. All trace/manifest/capability/syntax/projection steps succeeded. |
| Remote manual render integration | PASS after final hardening | User dispatched [run 38023581895](https://github.com/hinoonyaso/make_simulation/actions/runs/38023581895), tested code `c0c8a94`. Both jobs and artifact uploads passed; downloaded ZIPs and six MP4s independently checked below. |

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
- P1 environment: manual remote render CI was subsequently completed through user dispatch; see final hardening evidence below. Windows Blender and local Chromium rendering required the approved host process context; an ordinary restricted WSL subprocess can still be blocked. Runtime failures remain explicit.
- P2 scope: whole-video perceptual playback was not performed. Motion thresholds are configurable only through the documented metadata/type policy and are not validated against arbitrary real sensors. Native Windows/network filesystem execution locking is not supported by this test evidence. No new world/model/controller/speech capability is implied.

Implementation commit `c208f0e` was pushed normally to `origin/main`. The unchanged-code post-commit YOLO invocation reused both caches (0 adapter calls; 1.3521 s total), confirming commit metadata does not invalidate the verified render. The following documentation-only commit records the completed remote result; its implementation is identical.

## Final hardening (2026-10-10)

Baseline `029f74f`: 114 tests passed before edits. Six added test methods reproduced two assertion failures (stored bounds overwritten by external bounds; PID `-1e-10` selecting index `-1`) and two malformed-range `IndexError` subcases before production changes.

- `timeline.py` validates and retains stored and external ranges independently; both phase endpoints must satisfy both. Only validated range pairs are compared. Existing schema, hash, replay and hold policies remain.
- `pid_playback.py` rejects nonfinite/out-of-range source time, clamps tolerated endpoint drift (1e-9 seconds) before bisect, and bounds sample indices on both sides. Existing 1e-12 sample-boundary rounding and zero-order hold remain. Debug source time retains the original mapping so drift stays observable.
- Added tests cover unequal ranges, reverse replay, hold, malformed/nonfinite bounds, nonfinite phase times, PID exact and ±1e-10 endpoints, out-of-tolerance/nonfinite mapping and empty samples. Existing tests retain PWM/encoder transitions and real PID/H1 timelines.
- After fixes: focused accuracy/routing suite **28 PASS**; full suite **120 PASS** (3.473 s); compileall and `git diff --check` PASS.
- Manual workflow audit: Python 3.12, Manim 0.21.0, MuJoCo 3.7.0, FFmpeg, Cairo/Pango, Nanum, V11_MANIM_BIN, Node 22/Playwright and manual trigger retained. Common previews remain 960×540/30. Added replay/NMS technical gates, JSON validation evidence to artifacts and missing-artifact failure policy. No heavy CI added.
- Initial remote manual render status: **NOT_RUN pending authenticated dispatch** (subsequently resolved below). This session has no `gh` CLI, no configured GH_TOKEN/GITHUB_TOKEN, and no connector workflow-dispatch method. No credentials were searched for. SSH push authorization does not provide Actions API dispatch authentication. Once the fix is pushed, use the workflow page's **Run workflow → main**, or `gh workflow run ai-video-integration.yml --repo hinoonyaso/make_simulation --ref main`. Record the resulting SHA, run/jobs/artifacts before marking remote acceptance criteria 6–8 complete.

At the initial hardening checkpoint, independent runner MP4 creation/decode/artifact verification was pending; it is now completed as recorded below. No unresolved failure in the tested local boundary fixes. Whole-video visual/audio review remains outside this technical hardening scope.

Local post-fix PID runtime: `/tmp/v115-hardening-renders/mcu_pid-f062df224e9f4b273e27/preview.mp4`, H.264 960×540/30, 422 frames, 14.066667 s. Full decode and all 422 render-update/sample states PASS (`/tmp/v115-hardening-pid-frames.json`). Final local rerun: 120 tests / 4.332 s / OK. Added stored-range NaN/Inf subcases. Workflow gate output is redirected before printing, so a failed validator cannot be masked by a successful `tee` under the runner's default `bash -e`.

First remote manual attempt: [38023126232](https://github.com/hinoonyaso/make_simulation/actions/runs/38023126232), SHA `a653dddcc7b02cf9d1fb16eee65903907a40a89a`. Three.js job `114128208003` PASS (12 points; actual 384D top3 C08,C11,C07). Manim job `114128208108` FAIL during evidence collection; 120 tests (4.115 s), six MP4 renders/decodes and PID frame mapping had passed, but artifact upload was skipped. This run is not a successful render-integration acceptance.

Confirmed failure: FFmpeg inherited stdin from the shell's report-list `while read` loop and consumed leading path characters; `/tmp/...` became `mp/...`. Reproduced locally with two valid PID reports (second became `tmp/...`). Disconnecting validator stdin using `</dev/null` made both reports validate successfully. The workflow also redirects output before printing rather than piping to `tee`, preserving failure propagation with default `bash -e`. A fresh run on the corrected commit is required; rerunning the old SHA would retain the defect.


### Successful independent runner verification

- Workflow: `.github/workflows/ai-video-integration.yml`, manual user dispatch.
- Tested implementation SHA: `c0c8a944f5274497e0310a4b33fc4032f85e2cd0`.
- Run: [38023581895](https://github.com/hinoonyaso/make_simulation/actions/runs/38023581895).
- `manim-preview`, job `114129583512`: **PASS**; 120 tests in 3.397 s; all six renders, full decodes, five mechanism trace/timeline/media gates and 422 PID render-update/sample comparisons passed.
- `threejs-browser`, job `114129583365`: **PASS**. Browser smoke test executes separately from the RAG Manim preview; this CI does not claim a newly rendered Three.js splice.
- Normal CPU workflow: [38023548431](https://github.com/hinoonyaso/make_simulation/actions/runs/38023548431), same implementation, **PASS**.

Both uploaded artifacts were downloaded, ZIP integrity checked, extracted and independently inspected. Their downloaded byte hashes exactly match the GitHub artifact digest:

| Artifact | ID | Bytes | SHA-256 |
|---|---:|---:|---|
| v11-mechanism-previews | 11659786029 | 1116307 | `80c56a7f4c03de1696b6d11fa4fbb7a6ba98c60909211d5eee316afbe54b7d42` |
| v115-rag-preview | 11659651214 | 669660 | `79b8ff2b94e7010c357dadd0aeb9f7b862e71ce5c8892ae0486a76fd0913a251` |

Downloaded evidence root: `output/v115_final_hardening/remote_38023581895/`. ZIPs and extracted source evidence are preserved. Validation relocates report paths only in a temporary copy; original remote reports, traces and timelines are unchanged. Results are in `artifact_verification.json` within that root.

All six MP4s are H.264, 960×540, nominal **30/1 fps**, silent, with local full decode PASS after download:

| File (relative to evidence root) | Frames | Measured duration (s) | Decode / timeline frame count |
|---|---:|---:|---|
| `11659786029/quantization.mp4` | 432 | 14.400000 | PASS |
| `11659786029/self_attention.mp4` | 816 | 27.198698 | PASS |
| `11659786029/pid.mp4` | 422 | 14.066667 | PASS |
| `11659786029/quantization_replay.mp4` | 432 | 14.400000 | PASS |
| `11659786029/nms_all_confidence_rejected.mp4` | 377 | 12.566667 | PASS |
| `11659651214/rag_video_preview.mp4` | 1020 | 33.996745 | PASS |

Attention/RAG muxed duration is 1.302/3.255 ms below the nominal frame-count duration; reported average frame rates are 30.001436/30.002873. Nominal stream rate is exactly 30/1, frame counts are exact, and existing FPS/duration gates pass. No frames or timing metadata were rewritten to force success.

For all five common mechanism MP4s: saved media hash, trace domain equations, canonical trace hash, timeline hash/phase IDs, exact frame count and renderer identity were rechecked from downloaded evidence. Quantization replay preserves the same trace hash and timeline as its execution. All 422 downloaded PID update states match the mapper. RAG downloaded timeline hash/frame count and full decode also pass.

Sampled actual pixels: NMS final frame visibly reads `최종 유지: 0개`, matching `candidate_ids: []`; PID frames 0/140/141/281/282/421 show hold → source progression → explicit replay, with correct first/last sample counters. This is sampled technical inspection, not whole-video perceptual playback.

Warnings: action dependencies emit Node `punycode`/`url.parse()` deprecation notices; the hosted runner warns that the retained checkout/setup/upload actions target Node 20 and are forced to run on Node 24. Manim reports that a newer release is available. These are non-failing dependency/version notices, not missing-font, render, decode or frame-validation failures. No dependency upgrade was added to this narrow hardening task.

Final acceptance: **P0 boundary fixes and remote render/decode/artifact criteria PASS**. The first remote failure remains documented with its reproduced cause and fix. No unresolved P0/P1 failure in this requested scope. P2 maintenance: action runtime deprecation warnings; migrate supported action versions in a separate dependency-maintenance change. Full perceptual playback, narration and subtitle QA were not performed and are not claimed. The final follow-up commit records evidence only; the remotely tested code remains `c0c8a94`.
