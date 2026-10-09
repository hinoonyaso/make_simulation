# V11 limitations

- V11 CLI renders silent technical media; it does not automatically create measured TTS, captions, educational-review evidence, reviewer frame reports, or a complete V9 delivery package.
- Quantization is NumPy reference arithmetic. It does not execute packed low-bit kernels, accelerator inference, PTQ/QAT training, or model-quality measurement.
- NMS receives controlled synthetic candidate boxes; there is no YOLO preprocessing or model execution.
- MCU PID uses a simple first-order plant and quantized encoder model. It does not execute firmware, interrupt/peripheral simulation, or hardware measurement.
- The MuJoCo adapter wraps one fixed-base H1 arm experiment; it does not establish ROS2, general FK/IK, or hardware compatibility.
- RAG fresh execution remains lexical; semantic retrieval and answer generation are not provided by this adapter.
- Pinned HTTPS archive download/extraction primitives now require explicit host, size, SHA-256 and destination metadata; they reject path traversal, links, special files and oversized archives. No registered environment currently has the complete pinned metadata, so actual environment downloads remain blocked. URDF validation does not run xacro or a physics/render engine.
- Environment preflight/catalog exists, but no Clearpath/Gazebo, ManiSkill/SAPIEN or robosuite environment has passed load, physics/action, trace, collision or render tests on this host.
- `object_detection` remains planned. The existing NMS adapter is synthetic candidate arithmetic and must not be reported as YOLO or image inference.
- The common mechanism CLI still produces silent technical renders. Narration, captions, educational reviewer, final delivery QA and L4 full production are not connected for these adapters.
- Most catalog entries are routing/planning records, not executable implementations. Check the capability registry before claiming support.
