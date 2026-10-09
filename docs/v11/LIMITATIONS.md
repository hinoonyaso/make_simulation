# V11 limitations

- V11 CLI renders silent technical media; it does not automatically create measured TTS, captions, educational-review evidence, reviewer frame reports, or a complete V9 delivery package.
- Quantization is NumPy reference arithmetic. It does not execute packed low-bit kernels, accelerator inference, PTQ/QAT training, or model-quality measurement.
- NMS receives controlled synthetic candidate boxes; there is no YOLO preprocessing or model execution.
- MCU PID uses a simple first-order plant and quantized encoder model. It does not execute firmware, interrupt/peripheral simulation, or hardware measurement.
- The MuJoCo adapter wraps one fixed-base H1 arm experiment; it does not establish ROS2, general FK/IK, or hardware compatibility.
- RAG fresh execution remains lexical; semantic retrieval and answer generation are not provided by this adapter.
- Asset fetch is local-only. Generic pinned remote archive download and URDF conversion are not implemented. URDF validation does not run xacro or a physics/render engine.
- Most catalog entries are routing/planning records, not executable implementations. Check the capability registry before claiming support.
