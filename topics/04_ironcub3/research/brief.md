# iRonCub 3 — production research brief

Source: Gorbani et al., **iRonCub 3: The Jet-Powered Flying Humanoid Robot**, arXiv:2506.01125v1, 2025-06-01. Read HTML and all PDF text; visually inspected PDF pages 1, 3–5, 7–8. Accessed 2026-09-16. Local PDF is research material, not included as video footage.

Primary sources:
- https://arxiv.org/abs/2506.01125v1
- https://arxiv.org/html/2506.01125v1
- https://github.com/ami-iit/paper_gorbani_mohamed_2025_ironcub3 (revision in `repository_revision.txt`)
- https://ami.iit.it/aerial-humanoid-robotics

## Claim ledger

| ID | Claim / evidence | Source location | Scenes |
|---|---|---|---|
| C1 | Four turbines, arm/back placement; prototype hand removal | Paper II-A, Figs. 2–4; official IIT platform page | hook/platform |
| C2 | Model-based state/thrust estimation and MPC; jet/joint rates differ | II-B–E, Fig. 6 | mpc |
| C3 | Nonlinear second-order jet dynamics in paper | II-C/E | delay |
| C4 | Simulation trajectory tracking and hardware liftoff are separate evaluations | IV-A/B, Figs. 13–16 | evidence |
| C5 | Brief flight, touchdown/re-liftoff, final controller shutdown | IV-B, Fig. 15 caption | evidence |
| C6 | Authors discuss model mismatch, vibration and thrust estimation | IV-B, V | evidence |
| L1 | Position/attitude comparison metrics | Own `output/simulation.json`; NOT paper measurements | experiment |
| A1 | 50 kg, 8 kg m², .32 m moment arms, first-order .35/.77 s thrust dynamics | Our chosen educational assumptions | force through experiment |

No paper benchmark reproduced. No official footage or CAD redistributed. Repository listing contains a README and demonstration media; no complete controller execution was performed. The paper contains only compact governing equations; this video's QP and planar dynamics are original teaching models, not claimed as the paper's precise LPV/variable-sampling implementation.

## Editorial and technical choices

Viewer question: why does available upward thrust not guarantee stable humanoid flight? Follow force balance → moment allocation → actuator lag → receding-horizon optimization → actual computed robot pose.

Evidence mode: paper explanation + original runnable toy demonstration. Level 2 with a bounded Level 3-style feedback experiment. Core model: airborne planar rigid body, ideal state feedback, first-order thrust, exact-discretized linear prediction and nonlinear plant integration. Four visual turbines share left/right force commands. Reference trajectory identical in both cases. Only plant lag changes; controller assumes .35 s in both.

Inputs are thrust commands in N after conversion from acceleration-normalized deviations. State is x,z,vx,vz,pitch,angular rate, two thrust deviations. Simulation integration is .01 s; controller is .1 s; horizon is 3 s. The time axis in this experiment is not the paper's real experiment timeline. No ground contact, UKF, articulated dynamics, turbine thermodynamics or exhaust-flow physics is computed. Exhaust length is a qualitative force cue.

The 3D body is schematic, with effective jet lever arms matching our model. Rendering reads the saved dynamics trace. We report position RMSE and maximum absolute pitch over the same 12-second trial window. Do not describe these as iRonCub performance or a universal stability boundary. The experiment starts airborne; it is not a simulated contact/takeoff reproduction.

Avoid repeating a sensor taxonomy error: the paper calls the T265 a depth camera; this video does not make that claim. Do not cite the paper's incomplete MAE sentence as numerical evidence. Avoid the text's approximate orientation claim when Fig. 14 uses nonzero reference angles; describe qualitative drift and shutdown instead.

## Source-to-output handoff

Narration: `storyboard.json`, audio and Whisper alignment under `assets/audio`/`output`.
Computation: `simulation.py` → `output/simulation.json`.
2D: `lesson.py`; 3D: `blender_scene.py`; packaging: `finish_video.py`.
YouTube description must state toy-model limitations and link the paper and official demonstration. Public upload to the previously authorized channel is requested by the user.
