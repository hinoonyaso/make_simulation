# Shared Robotics Education Video Style Guide

## 1. Content identity

Create **educational simulation videos for studying and teaching robotics software, robot perception, computer vision, and Edge AI**.

For this project's channel, prioritize **Physical AI papers → core algorithm → original mathematical/data-flow animation → computed 3D robot simulation → robot-system interpretation**. The viewer should be able to explain what computation caused the visible behavior. Use the channel/episode guidance in `robotics-curriculum.md` to scope each video.

The goal is not cinematic decoration. The goal is to make invisible computation, geometry, state change, and robot-system data flow visually understandable.

Learning progression:

`Level 1 Principles → Level 2 Papers → Level 3 Robot Simulation`

Use `robotics-curriculum.md` alongside this guide for level-specific experiment design, paper evidence and reusable module contracts. Inside each skill both files are under `references/`.

Level 3 teaching view:

`Camera → Perception → VLA → World Model → Planning → Control → Robot`

Show the implemented graph and the robot/environment → camera feedback loop. This learning sequence does not require every robot architecture to contain each module or use this exact serial execution order.

General system view:

`Sensor/Camera -> Perception -> AI Inference -> Localization -> Planning/Decision -> Control -> Robot`

Manipulation view:

`Camera -> Detection/Segmentation -> Depth -> 3D XYZ -> TF/Coordinate Transform -> Grasp Pose -> IK/MoveIt2 -> Robot Arm`

## 2. Target audience

Assume beginner-to-intermediate technical learners.

- Explain the intuition before dense formulas unless the formula itself is the topic.
- Avoid unexplained notation.
- Keep one scene focused on one learning point.
- Prefer a concrete example before abstraction.
- Always connect the concept to a real robotics use case when relevant.

## 3. Default video format

Unless explicitly requested otherwise:

- normal YouTube video, not Shorts
- 16:9 landscape
- 1920x1080
- 30 fps default
- 2-5 minutes for a single concept
- bright, clean educational style
- Korean narration
- Korean captions
- English technical terms may remain on screen where standard and clearer
- Shorts only when explicitly requested

Keep 2–5 minutes as the single-principle default. For a paper or integrated experiment, plan around the mechanism and evidence; roughly 5–8 minutes is a useful starting range when both 2D and 3D explanation need room. Split independent mechanisms into related episodes rather than accelerating dense formulas to meet a duration. User-specified duration takes precedence.

## 4. Common lesson structure

Use this sequence by default:

`Hook / Problem -> Input / Setup -> Core Mechanism -> Transformation / Process -> Output -> Robotics Application -> Recap`

For Physical AI paper videos, apply the curriculum's paper-to-experiment spine within this structure. Open with a concrete robot question or a brief result from the actual experiment, then unpack the computation that produced it. End with the system consequence and a visible limitation, not only an architecture recap.

Recommended opening pattern:

1. Show the practical problem first.
2. Explain why the current information is insufficient.
3. Introduce the mechanism that resolves it.
4. Show the transformed result.
5. Connect the result to robot behavior.

Example:

`Pixel coordinate -> Why robot cannot use it directly -> Add depth/intrinsics -> 3D point -> TF -> Robot can plan motion`

## 5. Visual language

### General palette

- background: warm/neutral bright gray or white
- primary text: dark gray, not pure black when avoidable
- muted/supporting text: medium gray
- input/token/selected object: orange or yellow
- perception/camera: cyan or blue
- AI/inference: purple
- planning/valid path: green
- error/loss/collision/warning: red
- neutral pipeline/data flow: gray

### Coordinate axes

Always use conventional axis colors in 3D spatial content:

- X = red
- Y = green
- Z = blue

Do not repurpose these colors for other meanings in the same 3D scene when that would create ambiguity.

### Motion rules

- Movement must explain state change or mechanism.
- Prefer continuity with Transform-like motion over unnecessary fade-out/fade-in resets.
- Do not use flashy effects that compete with the concept.
- Use highlighting to guide attention to the exact object being discussed.

### Mathematical visual storytelling

Use the user's 3Blue1Brown reference as a direction for visual reasoning: build intuition with a concrete case, transform familiar objects into mathematical representations, and let the viewer predict a change before revealing its computed result. Create original scenes and narration suited to this channel.

- Introduce a symbol at the moment its quantity becomes visible. Connect equation terms to the corresponding vectors, pixels, tokens or actions through consistent labels and highlighting.
- Show meaningful intermediate computation, not arrows that merely light up between opaque boxes. For high-dimensional values, label a displayed slice, projection or summary and explain what it represents.
- Preserve identity across Manim and Blender: the same sample/action, units, frame, timestamp and semantic label must remain recognizable. Use a match transition or a briefly linked view when moving from an equation to its robot consequence.
- Prefer one dominant visual with progressive reveals. Use multiple simultaneous panels only when comparison requires them; avoid a permanently crowded dashboard that makes the audience read equations, captions and plots at once.
- Distinguish predicted, selected and executed trajectories using labels and line treatment as well as color. Separate model integration time, prediction horizon and physical execution time when more than one clock exists.
- Leave enough time to inspect the pivotal transformation or comparison. Narration explains causality and consequences rather than reciting symbols.

## 6. Typography and labels

- On-screen technical labels: English is preferred for standard engineering terms.
- Narration and captions: Korean by default.
- Keep labels concise.
- Avoid long paragraphs inside the animation.
- One major title per scene.
- Use consistent terminology across all scenes.

Examples of terms that should stay consistent:

- Attention Score vs Attention Weight
- Path vs Trajectory
- Camera Frame vs Base Frame
- Mapping vs Localization
- Training vs Inference
- Model Compile/Optimization vs Runtime Inference

## 7. Narration and captions

Narration should explain **why -> what happens -> result**.

Preferred style:

- concise Korean explanatory sentences
- avoid reading every label on screen
- explain the change happening visually
- define a term only when it first becomes necessary

Captions should be shorter than narration.

Example:

Narration:
`카메라가 찾은 픽셀 좌표만으로는 로봇팔이 실제 공간의 위치를 알 수 없습니다.`

Caption:
`Pixel coordinate alone is not enough`

When narration timing exists, let narration drive scene pacing rather than inserting arbitrary long waits.

## 8. Technical correctness rules

Never blur these distinctions:

- coordinate frame vs coordinate value
- camera_link vs optical frame
- pixel coordinate vs metric 3D coordinate
- path vs trajectory
- localization vs mapping
- raw score vs normalized probability/weight
- training vs inference
- compilation/optimization vs runtime inference

For illustrative values:

- label them as `illustrative`
- do not imply they are exact outputs from a real model unless computed from real inputs

For formulas:

- show units when useful
- preserve coordinate conventions
- do not simplify away a step if doing so changes the meaning

## 9. Robotics-first relevance

Whenever possible, close the explanation by showing where the concept sits in the robot system.

Examples:

- Depth -> 3D XYZ -> TF2 -> Grasp Pose
- Odometry -> Localization -> Nav2
- ONNX -> TensorRT/NPU -> ROS2 inference node
- IK -> Motion Planning -> Controller -> Robot Arm

Avoid ending at an abstract mathematical result if there is a meaningful robotics consequence to show.

## 10. Recap standard

Every educational video should end with a compact recap.

Preferred form:

`Input -> Core mechanism -> Output -> Robot application`

Keep the recap visually simpler than the body of the video.

## 11. Manim-specific role

Use Manim primarily for:

- equations
- matrices
- tensors
- flow diagrams
- algorithm state changes
- plots and comparisons
- symbolic transformations
- narration-driven infographic scenes

Do not fake complex 3D spatial intuition if Blender would explain it substantially better.

## 12. Blender-specific role

Use Blender primarily for:

- 3D coordinate frames
- camera frustum and projection geometry
- robot arms and joint motion
- AMR motion
- obstacles and trajectories
- LiDAR rays
- 3D spatial relationships

Avoid dense formulas or long text inside Blender. Move those explanations to Manim when appropriate.

## 13. Quality checklist

Before final delivery, verify:

- Is the learning objective obvious?
- Can a beginner follow the visual sequence?
- Does every scene teach one clear thing?
- Are terminology and colors consistent?
- Are narration and visuals synchronized?
- Are formulas, frames, directions, and units correct?
- Are illustrative values labeled honestly?
- Is the robotics application shown where relevant?
- Is there a final recap?
- Is the default result appropriate for a 16:9 YouTube educational video?
- For a paper episode, can the viewer trace one input through the central algorithm to its computed robot consequence, and distinguish paper evidence from the local demonstration?
- Does the system interpretation identify the actual input/output contract and a practical limitation supported by the experiment or cited source?

## 14. Model-driven simulation requirements

Apply this section when the user asks for a simulation. For requests limited to conceptual explanation, diagrams remain appropriate and should be described as explanatory animations.

Before producing frames, identify:

- **State and inputs:** what changes, in which units, under which controlled conditions.
- **Forward model:** how state generates observable values or system responses.
- **Computation:** the algorithm or estimator that uses those observations.
- **Reference and metric:** what constitutes a correct output and how discrepancy is measured.
- **Limits:** idealizations, omitted effects, and whether data are synthetic or measured.

At least one changing input must cause a computed, visible response. When informative, compare a nominal run with a changed input, noise level, calibration, or failure condition. Derive displayed errors and graphs from that run; never invent a plausible curve or move an estimate onto the reference position by construction. If the forward and inverse models intentionally form an ideal round trip, explain why the baseline error is near zero and demonstrate a perturbation that breaks the agreement.

Use one time-indexed trace to drive scene state, sensor views, numerical readouts, plots and narration alignment. Export enough inputs, model settings, seeds, reference values and estimates to reproduce the result. Offline rendering of a computed trace is valid; avoid implying an interactive or live sensor acquisition when none exists.

Validate the numerical model before expensive rendering. Verify units and coordinate conventions, at least one analytically predictable case, the intended response to input changes, and synchronization of the displayed quantities. Video decoding checks do not substitute for model validation.

For Pixel + Depth → XYZ specifically, generate observations from moving scene geometry, then reconstruct using those observations. Show a camera view, depth evidence, surface-point estimate and an actual error comparison in a readable arrangement. Do not equate a visible surface hit with the object's center. In ideal geometry, near-zero error is an expected round-trip result, not proof of real-camera accuracy. Noise and wrong intrinsics should alter the measured estimate, not merely change a label.

These requirements govern the causal computation, not a mandatory visual template. Choose scene length, panel arrangement and model complexity to fit the requested lesson.

This document is the common visual, narrative, technical, and production standard for both the Manim and Blender robotics education skills.
