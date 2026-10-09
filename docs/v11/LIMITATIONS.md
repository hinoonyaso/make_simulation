# V11 limitations

- V11 CLI renders silent technical media; it does not automatically create measured TTS, captions, educational-review evidence, reviewer frame reports, or a complete V9 delivery package.
- Quantization is NumPy reference arithmetic. It does not execute packed low-bit kernels, accelerator inference, PTQ/QAT training, or model-quality measurement.
- The common `nms` topic still receives controlled synthetic candidate boxes. A separate optional `object_detection` pilot runs actual YOLO11n image inference; it is not routed through the common `produce_video.py` topic dispatcher.
- MCU PID uses a simple first-order plant and quantized encoder model. It does not execute firmware, interrupt/peripheral simulation, or hardware measurement.
- The MuJoCo adapter wraps one fixed-base H1 arm experiment; it does not establish ROS2, general FK/IK, or hardware compatibility.
- RAG fresh execution remains lexical; semantic retrieval and answer generation are not provided by this adapter.
- Pinned HTTPS archive download/extraction primitives now require explicit host, size, SHA-256 and destination metadata; they reject path traversal, links, special files and oversized archives. No registered environment currently has the complete pinned metadata, so actual environment downloads remain blocked. URDF validation does not run xacro or a physics/render engine.
- Environment preflight/catalog exists, but no Clearpath/Gazebo, ManiSkill/SAPIEN or robosuite environment has passed load, physics/action, trace, collision or render tests on this host.
- The YOLO pilot requires an externally supplied image, checkpoint, and optional Ultralytics runtime. Its checked example used a public sample image and a checkpoint downloaded to `/tmp`; it does not bundle weights or make Ultralytics a project dependency. The visualization is image-space only, with no depth estimate or physical robot simulation.
- The common mechanism CLI produces silent technical renders. Narration, captions, educational reviewer, final delivery QA and L4 full production are not connected for these adapters.
- Run caching revalidates technical media decode; it does not verify learner comprehension, audio, or educational quality.
- The common H1 mechanism route remains a Manim replay of the recorded MuJoCo trace. A separate Blender pilot imports the H1 mesh and replays the same trace in 3D; it interpolates recorded states and does not step Blender physics.
- The existing V10 RAG renderer requires its four established beat stages; dynamic V11.2 storyboard planning does not alter that scene contract.
- Most catalog entries are routing/planning records, not executable implementations. Check the capability registry before claiming support.
