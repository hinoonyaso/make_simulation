# V11.2 real YOLO image inference pilot

This pilot answers whether the object-detection example runs an actual model. It does: Ultralytics YOLO11n runs on an official bus sample image, and the resulting trace records the raw model tensor, confidence candidates, class-aware NMS comparisons, and the runtime's final detections. The Manim video visualizes those exact results in image coordinates.

The final rendered preview is in `output/yolo11n_inference_trace.mp4`. The visualization is a 2D image-detection trace. It does not infer depth, create a 3D scene, or run a physical robot simulation. It is not a Nav2/robot planner.

## Reproduce

The working-session assets used for this render were downloaded to `/tmp/v112_yolo` from the official sources below. They are intentionally not committed as generated model/image binaries. On a new machine, fetch them from those URLs, verify the hashes below, then run:

```bash
uv run --with ultralytics==8.3.0 python scripts/run_yolo_inference.py \
  --image /path/to/bus.jpg --model /path/to/yolo11n.pt \
  --out /tmp/yolo_trace.json --display-limit 12
YOLO_TRACE_PATH=/tmp/yolo_trace.json uv run manim -qh --fps 30 \
  --resolution 1920,1080 --media_dir /tmp/yolo_manim \
  pilots/v11_2_yolo/render_scene.py YoloInferenceScene
```

Input/model details from the actual run:

- Image: [Ultralytics bus.jpg](https://ultralytics.com/images/bus.jpg), 810×1080, SHA-256 `c02019c4979c191eb739ddd944445ef408dad5679acab6fd520ef9d434bfbc63`.
- Weights: [YOLO11n v8.3.0 asset](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt), SHA-256 `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Runtime: Ultralytics 8.3.0, CPU inference, 640-pixel inference size, confidence 0.25, IoU 0.45.
- Runtime detections: bus 0.940, person 0.888, person 0.878, person 0.856, person 0.622. Independently reconstructed NMS output was matched to Ultralytics final output before the trace was written.
- Raw predictions: 6,300; candidates recorded above display floor 0.05: 70; candidates above confidence threshold: 47; final detections after class-aware NMS: 5. Only up to 12 candidates are selected for overlays; inference and NMS use the full model tensor.

The Ultralytics code/model distribution is marked AGPL-3.0 by Ultralytics; check the [official license options](https://www.ultralytics.com/license) before redistributing a product that includes it. This pilot does not bundle the checkpoint or Ultralytics runtime.

## Implementation decision

The adapter hooks the real pre-NMS prediction tensor and predictor input shape, then reconstructs confidence filtering and class-aware NMS from those values. It verifies the result against the runtime's post-NMS boxes and fails closed on a mismatch. This keeps the trace tied to observed inference instead of using hand-authored candidate boxes. Model-space boxes are retained for NMS arithmetic; image-space boxes are derived using the captured letterbox dimensions for rendering.

The model and sample image stayed in `/tmp`; no user image, private dataset, map, or world was sent to a remote service. The Ultralytics package was supplied transiently with `uv run --with`, not added to project dependencies. A future kit candidate is an optional, version-pinned object-detection adapter with this pre-NMS capture and coordinate verification behavior; the shared kit has not been edited.
