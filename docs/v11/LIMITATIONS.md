# V11 limitations

- V11 CLI renders silent technical media; it does not automatically create measured TTS, captions, educational-review evidence, reviewer frame reports, or a complete V9 delivery package.
- Quantization is NumPy reference arithmetic. It does not execute packed low-bit kernels, accelerator inference, PTQ/QAT training, or model-quality measurement.
- The common `nms` topic still receives controlled synthetic candidate boxes. `object_detection` is a separate capability routed through the common CLI and runs only the verified YOLO11n image checkpoint; it does not replace or relabel synthetic NMS.
- MCU PID uses a simple first-order plant and quantized encoder model. It does not execute firmware, interrupt/peripheral simulation, or hardware measurement.
- The MuJoCo adapter wraps one fixed-base H1 arm experiment; it does not establish ROS2, general FK/IK, or hardware compatibility.
- RAG fresh execution remains lexical; semantic retrieval and answer generation are not provided by this adapter.
- Pinned HTTPS archive download/extraction primitives now require explicit host, size, SHA-256 and destination metadata; they reject path traversal, links, special files and oversized archives. No registered environment currently has the complete pinned metadata, so actual environment downloads remain blocked. URDF validation does not run xacro or a physics/render engine.
- Environment preflight/catalog exists, but no Clearpath/Gazebo, ManiSkill/SAPIEN or robosuite environment has passed load, physics/action, trace, collision or render tests on this host.
- The YOLO adapter requires an externally supplied image, verified checkpoint, and optional Ultralytics 8.3.0 runtime. It does not bundle weights or make Ultralytics a project dependency. The visualization is image-space only, with no depth estimate or physical robot simulation. Replay checks the source image hash and does not run inference.
- The common mechanism CLI produces silent technical renders. Narration, captions, educational reviewer, final delivery QA and L4 full production are not connected for these adapters.
- Run caching revalidates reported media hash, expected output path, codec/resolution/fps/duration and full decode; it does not verify learner comprehension, audio, or educational quality.
- The common H1 route can select Blender to replay the recorded MuJoCo trace using imported H1 meshes. It checks source model hash, joint order/limits and FK, interpolates recorded states, and does not step Blender physics.
- The existing V10 RAG renderer requires its four established beat stages; dynamic V11.2 storyboard planning does not alter that scene contract.
- Most catalog entries are routing/planning records, not executable implementations. Check the capability registry before claiming support.
- Current WSL session can launch Windows Blender only from an elevated process context: normal sandbox preflight fails with `UtilBindVsockAnyPort`, while elevated Blender 5.2.1 `--version` succeeds. H1 rendering is therefore host-context dependent; production correctly blocks when the process check fails.
- Loopback binding is part of Three.js preflight because Chromium loads a locally served trace projection. When the host forbids local binds, RAG uses Manim and reports loss of the 3D embedding projection.
- H1 Blender displays interpolated recorded MuJoCo states; the shared timeline changes playback mapping, not physics execution or the source simulation duration.
