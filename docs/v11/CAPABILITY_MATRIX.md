# Capability matrix

Levels: L1 explainable illustration; L2 validated trace replay; L3 executable calculation/model/physics; L4 full narrated and reviewed production.

| Topic | Level | Execution evidence | Current limit |
|---|---:|---|---|
| RAG | L3 | Existing lexical TF-IDF/cosine runner or saved V10 trace | Silent common CLI delegates to V10; no semantic model/answer LLM |
| Quantization | L3 | NumPy INT4/INT8 symmetric/asymmetric and per-tensor/per-channel arithmetic; weight-only and distinct weight+activation tensors | No accelerator kernel or model quality benchmark |
| NMS | L3 | Confidence filtering, IoU, greedy NMS over controlled synthetic boxes | No detector/image inference |
| Object detection (YOLO11n) | L3 | Common CLI runs the verified YOLO11n checkpoint on a local image, validates pre-NMS capture and class-aware NMS against runtime results, renders image-space boxes, and supports image-hash-checked replay | Optional Ultralytics 8.3.0; only the pinned checkpoint hash; image-space only, not depth/video tracking/robot simulation |
| Self-Attention | L3 | NumPy single-head Q/K/V projection, score, scaling, optional causal mask, softmax, weighted sum | No trained Transformer weights or large-model inference |
| MCU PID | L3 | Discrete sampled PID, encoder quantization, first-order motor model | No firmware, peripheral simulator, or physical board |
| H1 arm | L3 | Existing fixed-base MuJoCo experiment and trace; common CLI can replay it with Manim or Blender mesh rendering | One model/experiment; Blender interpolates validated recorded states and does not run physics |
| DWB/TEB/MPPI/A* | L2 for existing pilot traces | Existing topic trace/pilot only | No generic planner execution adapter |
| Other registry topics | L1/planned | Catalog entries support routing and honest refusal | No execution adapter unless listed above |

V11.3 adds RAG Preview/Final report selection and media checks, phase-ID matching, cache metadata/hash verification, common H1 Blender replay, and common YOLO11n execution/replay. No topic currently reaches L4 through the V11 CLI. Korean aliases are registered in `core/mechanism/catalog.json`; aliases shared across attention variants intentionally resolve as ambiguous. Environment candidates and load status are in `core/simulation/environments/registry.json`; no environment currently reaches READY. Consult the machine-readable mechanism registry for runtime fields and aliases.

V11.3 retains trace-backed quantization mapping, synthetic NMS, PID and attention views, and adds explicit phase IDs to common storyboard beats. H1 Blender uses the existing pilot mesh renderer through the common CLI. YOLO uses its existing image-space scene through the common CLI, with its stage sequence checked against manifest phase IDs. RAG continues to use the existing four-stage V10 scene contract. These are silent technical renders; narration/reviewer/delivery remains separate.

V11.4 resolves renderer selection from a declared/inferred visual goal and a process-level preflight. All implemented routes consume the common integer-frame timeline. H1 `motion_3d` requires successful Blender plus local model preflight; H1 numerical/comparative views use Manim. RAG spatial output can fall back to Manim when local Three.js, browser, or loopback capture is unavailable; the report records that projection feature loss.

## V11.5 accuracy updates

- `robot_kinematics`: full-trajectory auto routing, per-phase Blender hold/speed display, existing MuJoCo execution cache. Fixed-base H1 scope is unchanged.
- `mcu_pid`: frame-to-recorded-sample Manim updates, zero-order-held controller/encoder state and explicit replay; generator remains a first-order plant with constant setpoint.
- `object_detection`: validated execution cache skips repeated CPU YOLO11n inference; local image/verified checkpoint and the optional pinned runtime are still required.
- RAG/Quantization/Attention renderer capabilities are unchanged. No asset or simulator support levels were raised by this maintenance release.
