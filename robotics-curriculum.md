# Robotics curriculum: principles → papers → robot simulation

## Routing and scope

Use this curriculum to plan educational videos and reusable experiments. Keep two production skills: Manim explains computation; Blender supplies spatial scenes, geometric observations and robot visualization. Levels describe learning depth, not separate rendering tools or compulsory prerequisites. A request for one topic does not authorize producing the whole course.

Select the requested level before the storyboard. For an unspecified level, use Level 1 for a mechanism, Level 2 for a named paper, and Level 3 for an integrated robot task. Reuse available prerequisites; explain missing essentials briefly rather than blocking production until all earlier videos exist. Read only the relevant level below plus the handoff section.

## Channel promise and episode design

Channel promise: **“그래서 그 논문 안에서 실제로 무슨 일이 벌어지는지 눈으로 보여준다.”** Specialize this project's default videos in Physical AI papers and original 2D/3D computational demonstrations, interpreted from a robot software/system perspective. Treat perceived gaps in Korean channels as the user's positioning hypothesis, not a verified market fact. Do not claim uniqueness or make competitor comparisons without separate research.

For a paper episode, use this editorial spine:

`Paper's question → Core algorithm → Equations / data-flow animation → Computed 3D robot experiment → Robot-system interpretation`

Choose one mechanism that changes an observable robot outcome. Follow the same concrete example, sample/action ID and experiment through equations and 3D views. A paper figure can establish context and attribution; the main explanation should unfold the computation in original visuals. Avoid spending most of the episode summarizing sections or showing unrelated robot demo footage.

Before the storyboard, record a compact episode brief in the existing lesson/storyboard metadata:

- viewer question and the one mechanism the viewer should understand;
- paper claim/source, evidence mode and simplifications where applicable;
- hero experiment: input intervention → algorithm response → visible consequence;
- which equation/variable becomes which robot quantity, and which trace IDs connect the views;
- system takeaway: required input, produced output, execution timing, and one practical constraint or failure;
- related prerequisite/next episode, if one is planned. Each episode must still answer its own question.

A Level 1 episode can focus on Manim and show a short system connection. Level 2 normally combines Manim and Blender for this channel when a spatial experiment explains the chosen contribution. Level 3 demonstrates the integrated loop. Do not force a robot arm onto a purely symbolic lesson or invent a paper implementation to fill this structure. If the full model is unavailable, make the central mechanism runnable as a clearly labeled toy experiment and narrow the claims accordingly.

### Proposed episode briefs, subject to source verification

These briefs guide future requested videos; they do not request immediate production or establish facts about named papers.

| Episode | Visual question and experiment | Connection / evidence boundary |
| --- | --- | --- |
| Flow Matching이 뭐길래 로봇이 움직이는가? | Noise → velocity field → ODE integration → action samples; vary conditioning or solver settings in a defined toy model | Distinguish flow integration time from action-sequence time and robot execution time. A curve in action space is not automatically an end-effector path; define the decoder/executor before displaying robot motion. |
| π₀ 논문을 3D로 이해하기 | Verify the selected paper/version, then trace an observation and language input through the relevant model components to an action chunk and robot execution | Use the proposed Camera + Language → VLM → Action Expert → Flow Matching → Robot Arm outline only where verified; add required state inputs. Reuse the earlier toy mechanism without presenting it as π₀ inference. |
| World Model은 왜 필요한가? | State + action → predicted future; execute the same action in the reference environment and reveal prediction error | Explain what consumes the prediction. Predicting a future does not by itself imply planning, policy training or improved task success. |
| RISE: 로봇이 현실이 아니라 머릿속에서 연습한다 | First resolve the exact paper. If it actually supports imagined rollouts, show the implemented prediction/training/selection process | The title and branching-future scene are provisional. If the paper uses another mechanism, revise both. Do not conflate offline imagined training, online planning and policy inference. |

For a branching-futures experiment, label current observed state, model-predicted rollouts, candidate scores, selected action and subsequently observed execution separately. Generate each candidate from its own actions and the stated prediction model. Compute the ranking from a defined objective; reveal success/failure from the relevant evaluation rather than drawing two failures and one success by script. A planner must not rank with hidden future ground truth unless an explicitly disclosed oracle baseline is being shown. Distinguish prediction error from planning error.

## Level 1 — Principles

Goal: a learner can predict what changes when an input changes. Follow concrete problem → minimal mathematical model → computed experiment → failure condition → module interface.

The course contains two prerequisite branches. Their order is pedagogical, not a claim that every topic depends on the preceding one:

- Geometry and control: Depth → XYZ → TF2 → IK.
- Learned models: Attention → Diffusion → Flow Matching → World Model.

| Topic | Computed experiment | Useful evidence / next interface |
| --- | --- | --- |
| Depth → XYZ | Scene intersections produce pixel/depth; backproject with K; perturb depth or K | Surface-point error, camera-frame XYZ |
| TF2 | Transform a point through moving frames; compare composed transforms | Round-trip / composition residual; stamped point in base frame |
| IK | Solve a reachable target, then vary target or initialization | FK pose residual, limits and unreachable status; joint target |
| Attention | Compute QKᵀ/√d, mask, softmax and weighted V on a small input | Weight normalization and resulting output change; token features |
| Diffusion | Specify a toy data distribution, noise schedule and implemented denoiser; run sampling | Actual intermediate samples and chosen reconstruction/distribution metric |
| Flow Matching | Specify a toy probability path, velocity target and implemented field; integrate the ODE | Actual trajectories and endpoint error under a stated reference |
| World Model | Predict future state from state/history and actions in a small environment; compare held-out rollouts | Multi-step prediction error; predicted states and uncertainty if implemented |

For learned topics, distinguish analytic toy fields, trained toy models and pretrained model inference. Show training and inference as separate operations. An arbitrary attractive particle trajectory is not evidence of diffusion or flow-matching inference. A World Model need not output video. Choose a representation that serves the lesson.

Deliver a reusable model and trace for a simulation request. A formula-only explanation can be delivered as an explanatory animation without a fabricated experiment.

## Level 2 — Papers

Course topic queue: π₀, RT-2, OpenVLA, RISE, τ₀-WM, ForceVLA, GR00T. This is a user-selected queue, not a verified dependency chain or an assertion that every name identifies a unique paper.

Before making paper-specific claims, resolve the exact title, authors, year, version, primary paper URL and official code/model URL when available. Verify niche and changing claims against primary sources. For ambiguous names or model families, investigate first; request the exact paper only if ambiguity remains material. Do not guess what RISE, τ₀-WM, ForceVLA or a GR00T variant refers to.

Build the lesson around:

1. The task and the limitation the paper addresses.
2. Only the Level 1 mechanisms actually used by this paper.
3. Observation/action representations, architecture, training objective and inference path.
4. One central contribution demonstrated with evidence appropriate to the available implementation.
5. Assumptions, observed failure case and where it connects to a robot system.

Choose and disclose the evidence mode before implementation:

- **Paper explanation:** cited architecture/results with explanatory animation; no reproduction claim.
- **Toy demonstration:** a runnable simplified mechanism with local measurements; explicitly not the paper's benchmark performance.
- **Model execution:** actual identified code/checkpoint, preprocessing, embodiment/action specification and logged inference. Call it benchmark reproduction only when the benchmark protocol and required evaluation are actually followed.

Keep published results and locally measured results distinct on screen and in metadata. Record sources with section/figure references for important claims. Do not infer a paper's use of diffusion, flow matching, planning or a world model merely from its name or this curriculum. Reuse Level 1 code only when its assumptions match the paper; document simplifications.

## Level 3 — Robot Simulation

Use the requested teaching view:

`Camera → Perception → VLA → World Model → Planning → Control → Robot`

Then draw the actual execution graph for the chosen task. This teaching sequence is not a universal architecture. A VLA may output action chunks directly; a world model may evaluate candidate actions inside a planner; modules may be absent or integrated. Label omitted, scripted and learned modules. Include language/task and robot proprioception where consumed. Close the feedback loop: robot action changes the environment, which generates the next observation.

Start with one bounded task, such as reaching a visible target. State the embodiment, initial condition, success criterion and termination condition. Build a working minimal baseline before adding learned modules; do not replace missing VLA inference with scripted behavior under a VLA label.

For each module boundary, record only relevant fields:

| Boundary | Contract to establish |
| --- | --- |
| Camera → Perception | RGB/depth dimensions, calibration, optical frame, depth meaning/units and acquisition timestamp |
| Perception → policy/planner | Features or pose, frame, confidence if available; transform convention |
| VLA → executor or world model | Observation/history + task input; action representation, units, frame, chunk horizon and rate |
| World Model ↔ Planning | State/latent representation, candidate actions, prediction horizon, scoring and uncertainty if implemented |
| Planning → Control | Path vs timed trajectory, joint/task space, constraints and reference rate |
| Control → Robot | Command mode, joint order, limits, control period and measured feedback |

Use an explicit simulation clock and specify module update rates and any modeled delay. Log the observations used by each action. Keep ground truth available for evaluation but out of a perception/policy input unless privileged access is an explicitly labeled experiment.

Choose the simulator according to the mechanism. Blender can provide geometry, ray-based observations and visualization. Keyframed playback alone does not establish contact dynamics, stable control or a closed-loop policy. If those matter, use a suitable dynamics backend or an explicitly implemented and validated simplified plant; render its logged states with Blender. State whether collision/contact is actually computed.

Compare the baseline with a meaningful perturbation, such as camera noise, calibration error, a changed target or modeled latency. Report task success and a mechanism-relevant metric (pose error, tracking error, collision count when collision is modeled, or prediction error). Give trial count and seeds; a single rollout is a demonstration, not general policy performance.

## Shared model and production handoff

The full channel workflow is **paper research → Manim → Blender → YouTube publishing**. When available, `physical-ai-paper-research-skill` supplies the source/claim ledger and experiment brief; `youtube-education-publishing-skill` consumes the final artifact, citations, captions and metadata. These are capability handoffs, not authorization to produce or publish additional deliverables. Research-only and package-only requests stop at their requested outputs.

Create one topic folder per subject. Preserve existing paths such as `topics/02_pixel_depth_to_xyz`; store level as metadata rather than moving old deliverables. Put new versions or shorts under that topic. For new topics, use `topics/<id>_<slug>/` and create only directories actually needed.

For a substantive simulation, keep a small `lesson.json` (or existing equivalent) containing:

- topic, level (1/2/3), learning objective and evidence mode;
- episode brief connecting the central mechanism, hero experiment and robot-system takeaway;
- prerequisite topic references and reused model/config versions;
- source references for paper claims;
- model parameters, assumptions, units/frames, seeds and module contracts;
- trace location, metric definitions and measured results;
- mapping from video time to simulation time, including holds or acceleration;
- commands and paths for the actual produced artifacts.

Use one saved numeric trace as the shared contract. Timestamp observations, estimates, reference states, actions and metrics as relevant to the experiment; include sample IDs. Do not require robot-control fields for an attention lesson. Renderers consume the same trace rather than separately recreating results. Keep captions and visual timing tied to the same video timeline.

Default production order when both tools are requested:

1. Resolve level, evidence mode, sources and the experiment contract.
2. Implement and validate the model; generate sensor observations here if the model needs Blender.
3. Produce the Manim draft: intuition, equations, computed readouts, graphs and narration timing.
4. Produce Blender spatial views from the same model/trace and finish the composite, narration and captions.
5. Inspect representative rendered frames and verify model results, synchronization, readability and output media.

“Manim first, Blender finish” governs presentation production; it must not force invented sensor data before a required Blender forward model runs. Purely symbolic lessons do not need a Blender pass unless requested. Use the project's uv environment and existing narration/Whisper alignment workflow when available; Whisper transcribes or aligns speech, while a separate TTS engine generates it.

For this repository, `robotics-curriculum.md` is the maintained source. Identical `references/robotics-curriculum.md` copies ship inside both skills so either folder remains usable independently. Synchronize these copies whenever this curriculum changes.
