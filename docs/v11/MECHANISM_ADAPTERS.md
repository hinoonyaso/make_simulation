# Mechanism adapters

`core/mechanism/protocol.py` defines the light adapter contract: `describe_capability`, `prepare`, `execute`, `validate`, `build_visual_plan`, and `render`. `MechanismRegistry` loads catalog metadata first and imports a selected adapter on demand.

New adapters are Quantization (NumPy affine reference arithmetic; weight-only or separate weight+activation inputs), NMS (actual greedy IoU over synthetic candidates), MCU PID (sampled controller plus numerical motor/encoder model), and Self-Attention (single-head Q/K/V arithmetic with optional causal mask). Existing RAG and MuJoCo H1 are wrapped, not rewritten. Every generated trace carries its execution type, provenance, software version, hardware boundary, and limitations. Quantization/NMS/PID/attention trace replay also runs the matching domain validator.

For weight plus activation arithmetic, provide `scope: "weight_and_activation"`, `weights`, and `activations` in the JSON passed to `--config`. Each tensor is quantized and validated separately; the video reports separate reconstruction errors. It remains a reference arithmetic demo, not an exported model or accelerator execution.

Typical commands:

```bash
uv run python scripts/inspect_capabilities.py --topic quantization
uv run python scripts/produce_video.py --topic quantization --preview
uv run python scripts/produce_video.py --topic nms --preview
uv run python scripts/produce_video.py --topic mcu_pid --preview
uv run python scripts/produce_video.py --topic 자기주의 --preview
uv run python scripts/produce_video.py --topic robot_kinematics --robot unitree_h1 --preview
```

Use explicit `self_attention`/`자기주의`; generic `attention` is ambiguous across self/cross/multi-head attention. Outputs are silent technical previews by default. `--preview` is 960×540 at 30 fps. Default output is 1920×1080 at 30 fps; a final render is not equivalent to a narrated/reviewed V9 delivery. The common scene uses sequential NMS comparisons, progressive PID trace drawing, and QKᵀ→scaled→softmax matrix transitions.
