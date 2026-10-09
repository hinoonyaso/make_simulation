# Capability matrix

Levels: L1 explainable illustration; L2 validated trace replay; L3 executable calculation/model/physics; L4 full narrated and reviewed production.

| Topic | Level | Execution evidence | Current limit |
|---|---:|---|---|
| RAG | L3 | Existing lexical TF-IDF/cosine runner or saved V10 trace | Silent common CLI delegates to V10; no semantic model/answer LLM |
| Quantization | L3 | NumPy INT4/INT8 symmetric/asymmetric and per-tensor/per-channel arithmetic; weight-only and distinct weight+activation tensors | No accelerator kernel or model quality benchmark |
| NMS | L3 | Confidence filtering, IoU, greedy NMS over controlled synthetic boxes | No detector/image inference |
| YOLO image-detection pilot | L3 | Optional Ultralytics YOLO11n CPU inference on an image; trace records raw predictions, confidence candidates, class-aware NMS, and runtime-matched final boxes | Separate pilot CLI, not the common topic dispatcher; image-space only, not depth or robot simulation; checkpoint/runtime supplied separately |
| Self-Attention | L3 | NumPy single-head Q/K/V projection, score, scaling, optional causal mask, softmax, weighted sum | No trained Transformer weights or large-model inference |
| MCU PID | L3 | Discrete sampled PID, encoder quantization, first-order motor model | No firmware, peripheral simulator, or physical board |
| H1 arm | L3 | Existing fixed-base MuJoCo experiment and validated robotics trace | One model/experiment; silent technical render |
| DWB/TEB/MPPI/A* | L2 for existing pilot traces | Existing topic trace/pilot only | No generic planner execution adapter |
| Other registry topics | L1/planned | Catalog entries support routing and honest refusal | No execution adapter unless listed above |

V11.2 adds run-isolated output and validated trace replay for the ready numerical adapters, existing H1 robotics trace, and RAG. No topic currently reaches L4 through the V11 CLI. Korean aliases are registered in `core/mechanism/catalog.json`; aliases shared across attention variants intentionally resolve as ambiguous. Environment candidates and load status are in `core/simulation/environments/registry.json`; no environment currently reaches READY. Consult the machine-readable mechanism registry for runtime fields and aliases.

V11.2 visual steps include trace-backed quantization code mapping, confidence-filter state plus sequential IoU comparisons for synthetic NMS, a synchronized PID cursor, and visible Q/K/V projection. The common H1 route remains Manim trace replay; the separate Blender 5.2 pilot successfully renders imported H1 meshes from that same trace through the approved host execution route. An optional YOLO11n pilot successfully runs real image inference and visualizes confidence filtering/NMS. Neither pilot is yet connected to the common topic dispatcher or complete narrated-delivery path. RAG continues to use the existing four-stage V10 scene contract.
