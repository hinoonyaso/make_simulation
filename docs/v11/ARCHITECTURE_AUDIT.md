# V11 architecture audit

Audit baseline: `2cd158e` (`main`, pushed to `origin/main`). Local status also contains unrelated untracked pilot material under `pilots/05_moving_obstacle`, `pilots/07_naive_rag`, and `pilots/08_advanced_rag`; this work must leave those files untouched.

## Existing implementation

| Area | Verified implementation | Boundary |
|---|---|---|
| V9 production | One `visual_manifest.json` contract, Director/Manim/Blender skills, narration preparation, caption/audio timing, Resolve staging, style/delivery validators, and reviewer workflow. | Topic scenes and pilot renderers are still largely selected by repository routing; there is no universal topic adapter registry. |
| AI mechanism | `ai-mechanism-trace/v1`, validation, RAG primitives, saved-trace replay and local TF-IDF/cosine execution, Manim scene, optional trace-matched Three.js projection. | RAG only is executable through the V10 production CLI. The lexical path is not semantic retrieval and does not execute an answer model. |
| Robotics simulation | `core/robotics-simulation/mujoco_adapter.py` runs a fixed-base Unitree H1 arm with PD torque control, writes a V9-compatible robotics trace, validates FK and joint limits; `pilots/v10_mujoco_arm` replays it with Manim. | One constrained model/experiment, no general simulation adapter API; no hardware or ROS2 runtime claim. |
| Visual assets | `core/visual-assets/registry.json` contains 33 entries. `AssetFactory` provides project-contained path resolution, hashing, local validation, converter injection, cache, registration and invalidation. | `validate_asset` currently establishes file presence/hash, not URDF semantics or mesh references. Cache identity omits converter identity/version/configuration. No general safe remote fetch or format-aware conversion is implemented. |
| Official robot assets | ROBOTIS OpenMANIPULATOR-X, TurtleBot3, Unitree H1 and Franka FR3 files already exist in `assets/` and have pinned upstream commits/licenses in registry/README metadata. OpenMANIPULATOR-X is 13 files, 4.47 MB; its Apache-2.0 license is present locally. | These are existing vendored assets; this audit did not redownload them. Mesh/URDF linkage had not been covered by a validator. No claim of ROS2, MuJoCo, or Blender compatibility follows from file presence. |
| Existing educational pilots | TEB/DWB/A*/costmap, obstacle avoidance, Naive/Advanced RAG, QLoRA and other topics have reusable manifests, traces, media or scene techniques. | Existing episode scripts are not automatically generic execution adapters. Preserve topic outputs and reuse core primitives instead of moving episode directories. |

## Current capability levels

Use these meanings consistently: **L1 Explainable** (illustration, no execution evidence), **L2 Trace Replay** (recorded and validated source data), **L3 Executable Simulation** (new deterministic/model/physics computation), **L4 Full Production** (execution or validated trace through visual/audio/review/delivery pipeline). L4 describes a topic path, not a claim of semantic or hardware fidelity.

| Domain / representative topic | Current level | Evidence / limitation |
|---|---:|---|
| RAG lexical | L4 for silent technical production; L3 execution | V10 CLI supports fresh TF-IDF/cosine execution and checked trace replay through preview/final technical QA; narration is optional and must be supplied/measured. |
| Saved model RAG trace | L2 | Existing E5/FAISS trace can be replayed; its missing operation durations remain unknown. |
| DWB, TEB, A*, costmap episodes | L2 per saved pilot; L1 outside those traces | V9 episodes and traces exist. They do not implement general Nav2 planner execution. |
| MuJoCo H1 arm | L3 | Real MuJoCo run and FK checks; rendered as a video-only Manim technical PoC, not L4 narrated production. |
| QLoRA / attention / quantization | L1 unless an episode-specific recorded artifact is supplied | Explanatory skill/pilot material exists; no shared numerical adapter in baseline. |
| Vision / YOLO / NMS | L1 | No general detector inference or NMS trace adapter found in baseline. |
| MCU / PID | L1 | No firmware or motor-control simulation runner found in baseline. |
| VLA, TensorRT, SLAM and remaining listed systems | Planned / unsupported for executable request | No evidence in shared runtime that would justify READY or L2+ status. |

Capability status must be queried from a versioned registry. Skill guidance, mesh presence, and topic names are not evidence of execution support.

## Reuse and compatibility constraints

- Retain `robotics-visual-trace/v1`, `ai-mechanism-trace/v1`, the V9 manifest fields, M/B/E renderer meanings, existing pilot paths, and the current `AssetFactory` entry format.
- Additive common mechanism envelopes must keep domain payloads separate; do not coerce robot states into AI vectors or vice versa.
- Keep repository imports compatible with Python 3.12 and the existing `uv` environment. NumPy is already available through the render dependency set; do not add an ML framework for toy numerical adapters.
- Existing asset conversion requires an injected converter. Remote archives must be pinned, hash-verified, path-safe and never execute upstream code.
- Robotics trace coordinates, units, timestamps and evidence level must survive renderer handoff. The H1 run is fixed-base and not hardware evidence.
- The V10 RAG renderer currently requires four beats and rejects context Top-K above five; generalization should surface limits rather than silently truncate evidence.

## Stability issues confirmed in code

1. Three.js projection divides by total PCA variance without handling a zero-variance matrix.
2. V10 scene timing helpers impose a minimum animation duration; very short positive manifest beats can overrun.
3. `AssetFactory._cache_key` includes source/revision/target and a factory constant, but not the actual converter version or configuration.
4. Asset validation hashes files but does not parse URDF references or verify `package://` mesh resolution.
5. Renderer selection records a summary but does not provide a structured per-stage attempt/fallback history.
6. V10's four-beat renderer and Top-K<=5 guard are implicit compatibility limits for a universal CLI.

The V10 manifest validator already reports malformed/missing/unknown trace errors, and the current CLI already rejects unsupported AI topics. These do not need duplicate fixes.

## Recommended implementation order

1. Add regression tests and fix PCA zero variance, short-beat bounds, converter cache identity, trace/manifest reference checks and renderer attempt reporting.
2. Add a lightweight capability catalog, adapter Protocol/registry, and `inspect_capabilities.py`; register all requested topic families, but mark unimplemented execution as planned/unsupported.
3. Adapt the existing RAG execution path without moving its code; add one new numerical AI adapter (quantization), one vision or MCU adapter (NMS and/or PID), and register the existing MuJoCo runner through the same adapter interface.
4. Validate the already vendored official OpenMANIPULATOR-X URDF and meshes, record aggregate source hash and validation evidence. Reuse it rather than duplicate downloads.
5. Add a common CLI that executes only registered executable adapters and delegates rendering to their existing or explicitly implemented renderer. Do not map unsupported topics to RAG or generic success.
6. Add fast CI for capability/catalog/adapter/assets and keep render/browser integration manual. Run the manual workflow only when GitHub credentials/network permit; local results must stay labeled local.
7. Record status and evidence in the requested V11 documents; preserve V10 reports as historical.

## Regression risks

- Changing the `AssetFactory` converter callback signature could break its current callers; preserve the 3-argument callable and add cache metadata/configuration as explicit optional arguments.
- Introducing a universal trace schema could break V9 validators; use an additive common envelope with domain-specific validators.
- Importing every adapter eagerly could make basic capability inspection require MuJoCo/Manim/Torch. Registry metadata should be import-light and adapters loaded only on selection.
- Rewriting pilot directories or shared renderer skills could alter published episode behavior. Keep the implementation additive and test the existing robotics trace route.
- Installing ROS2/Blender/system packages or downloading models may be blocked and should not be confused with code-level validation.
