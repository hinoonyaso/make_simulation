# Evidence / Simulation Rules

- Explanation: scripted geometry illustrating a concept.
- Trace playback: recorded or precomputed states replayed faithfully.
- Simulation: state evolves from an implemented model/physics/simulator.
- Model execution: output comes from an actual inference/control runtime.

Do not call explanatory keyframes a simulation. Never invent benchmark numbers or traces. If Manim and Blender show the same motion/data, use one shared trace/config.

## Physics contract for robot motion and contact

Distinguish these mechanisms in episode documentation and evidence labels:

| Mechanism | What generates robot state | Permitted claim |
| --- | --- | --- |
| Scripted pose/keyframe replay | Author or stored poses | Illustration / trace playback |
| Kinematic motion model | Velocity integration without simulated forces/contact | Simplified kinematic simulation |
| Physics-backed execution | Engine integrates actuated bodies and resolves modeled contact | Physical simulation within stated model limits |

Realistic rendering alone proves none of these. A previous episode remains trace playback unless a new physical run is actually performed.

### Plan the physical experiment

- State the physical question: e.g. does a velocity command produce the expected motion/clearance, or how does contact/slip affect it? Preserve the approved explanation rather than adding an unrelated crash spectacle.
- Choose the minimum capable existing engine. Blender rigid-body dynamics can serve suitable contact demonstrations; wheeled controlled robots require supported wheel/joint actuation and contact behavior. If unavailable, report the missing capability and propose a suitable engine; do not pretend a mesh or wheel-spin animation is an actuator model.
- Define units/axes, gravity, mass/inertia assumptions, collision shapes, wheel/joint geometry, friction/restitution, initial conditions, actuation/control update rate and solver time step/settings. Verify applicable capabilities/version in the installed environment before using APIs.
- Declare control mode: closed loop with simulated state/sensing, open-loop recorded commands, or prescribed pose playback. Recorded commands can drive a new physical run; stored poses cannot stand in for its result. Declare which obstacles are static, kinematic or dynamic.

### Execute and retain evidence

Keep a local reproducible runner/config and the simulator/version, run command, seed if applicable, time step/substeps, initial state, relevant contacts and actual body poses/velocities. Export a V9-compatible projection for renderers; retain necessary raw solver outputs/provenance beside it in established episode locations. Validate the projection with `core/shared-data/validate_trace.py`. This gate checks the data schema, not the truth or adequacy of the physical model.

Check units, stable initial conditions, floor contact, unintended penetration/explosion, actuator response and the physical claim being illustrated. Use a repeat run with stated numeric tolerance and, when contact/dynamics decides the lesson, a smaller-step or higher-substep comparison. Report actual results and sensitivity; deterministic-looking frames alone are not validation. Record important approximations, including omitted slip, sensor delay, simplified collision geometry or ideal actuators.

Do not change mass/friction/solver settings just to force the desired story without declaring the change and rerunning evidence. A failure or deviation can be useful evidence; narrow the claim if the model does not support the intended conclusion.

### Explain and render the same run

Map controller/plan events, robot response and contacts to source timestamps. Manim uses the new run's map/planner/command records and actual physical states when making execution claims. A historical plan may be an input or reference, but it must be labeled and must not be presented as a plan recomputed from the new physical state. Never mix the old episode's trajectory with a new physical result as though they were one run.

Use existing manifest evidence enums: `toy_simulation` plus a shared `trace` for a newly computed simplified physical run, `trace_playback` for its rendered replay. Put engine/model provenance in the episode README/run artifacts and scope the narration as educational physics, not real hardware or Nav2 execution. Do not introduce an unsupported `physics_simulation` enum.

Preserve source time/coordinate/object identity across Blender setup -> Manim mechanism -> Blender physical consequence. Intentional pauses, slow motion and held states belong to presentation only; do not alter solver time to accommodate speech. Inspect the critical excerpt with actual physical behavior before costly full rendering. If the physical run is missing or fails relevant checks, its acceptance is incomplete/FAIL even if the render is attractive.
