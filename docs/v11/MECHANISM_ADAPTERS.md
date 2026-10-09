# Mechanism adapters

`core/mechanism/protocol.py` defines the light adapter contract: `describe_capability`, `prepare`, `execute`, `validate`, `build_visual_plan`, and `render`. `MechanismRegistry` loads catalog metadata first and imports a selected adapter on demand.

New adapters are Quantization (NumPy reference arithmetic; weight-only or separate weight+activation inputs), NMS (actual greedy IoU over synthetic candidates), and MCU PID (sampled controller plus numerical motor/encoder model). Existing RAG and MuJoCo H1 are wrapped, not rewritten. Every generated trace carries its execution type, provenance, software version, hardware boundary, and limitations.

For weight plus activation arithmetic, provide `scope: "weight_and_activation"`, `weights`, and `activations` in the JSON passed to `--config`. Each tensor is quantized and validated separately; the video reports separate reconstruction errors. It remains a reference arithmetic demo, not an exported model or accelerator execution.

Typical commands:

```bash
uv run python scripts/inspect_capabilities.py --topic quantization
uv run python scripts/produce_video.py --topic quantization --preview
uv run python scripts/produce_video.py --topic nms --preview
uv run python scripts/produce_video.py --topic mcu_pid --preview
uv run python scripts/produce_video.py --topic robot_kinematics --robot unitree_h1 --preview
```

Outputs are silent technical previews by default. `--preview` is 960×540 at 30 fps. Default output is 1920×1080 at 30 fps; a final render is not equivalent to a narrated/reviewed V9 delivery.
