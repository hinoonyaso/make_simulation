# V11.4 Renderer Routing

## Decision inputs

`core/mechanism/renderer_routing.py` resolves the visual goal and evaluates the topic's evidence, renderer capability, local trace/model inputs and process-level runtime preflight. The decision is deterministic and is written to `production_report.json` with the rejected candidates and any feature loss.

| Topic and goal | Effective renderer | Evidence shown |
|---|---|---|
| Quantization, PID, attention, NMS | Manim | Values, equations and algorithm state |
| Object detection / image space | YOLO image-space Manim | Actual image coordinates, confidence and NMS output |
| H1 motion_3d | Blender H1 trace playback | Existing mesh posed from recorded MuJoCo states |
| H1 comparative analysis | Manim | Trace plots and numerical relationships |
| RAG spatial relationship | Manim + Three.js when available | Existing trace vectors projected for display; recorded ranking remains authoritative |
| RAG algorithm flow | Manim | Chunk, embedding, retrieval and context phases |

Runtime preflight checks a real `--version` process, not only executable discovery. H1 additionally checks its selected local MJCF file. `scripts/inspect_capabilities.py --topic robot_kinematics --preflight --visual-goal motion_3d` exposes the decision before a render. Supply `--model` to inspect a non-default local model.

An explicit Blender request fails closed. `motion_3d` also fails closed if Blender cannot satisfy the requested evidence. An automatic H1 `spatial_relationship` request may use Manim only when its report records the loss of mesh and spatial-motion evidence. RAG's automatic Three.js fallback is permitted because the Manim retrieval view retains the recorded score/rank explanation.

Run identity stores the requested renderer in the request, the effective renderer in the renderer field, plus the resolved goal, timeline digest, relevant code fingerprint, renderer version and local model hash. A fallback artifact must not be recorded as the requested backend's result.

This is trace playback, not a claim that Blender reruns MuJoCo physics. YOLO is image-space inference visualization, not depth or robot motion. Three.js PCA coordinates are display projections and do not calculate retrieval scores.
