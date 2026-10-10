# V11.5 motion and frame accuracy

Baseline: `01c4a8f489e49ab05d2528a4d7433b3fcef85f0a`, confirmed against origin/main before edits. Baseline local suite: 87 tests passed. The three reproduced causes were endpoint-only H1 motion classification, source/whole-video speed labelling, and a separate PID ValueTracker running independently of the timeline.

## Joint motion evidence

`core/mechanism/joint_motion.py:analyze_joint_motion` reads the complete ordered trajectory. It reports displacement from the initial pose, deadband-filtered cumulative travel, active joint count/duration, per-joint thresholds/units, peak recorded qvel, isolated outliers and the decision reason. A return to the initial pose still has nonzero displacement and travel.

Fixed-base H1 has scalar revolute coordinates in radians. The default revolute/continuous deadband is **0.001 rad** (about 0.057°); explicit prismatic metadata uses **0.0001 m**. Repeated sub-deadband jitter does not accumulate into false motion: travel updates only after leaving the last accepted position's deadband. These are educational routing thresholds, not measured H1 encoder resolution or hardware safety limits.

An isolated interior excursion that returns to within the deadband of its neighbours, with both adjacent secant speeds above 30 rad/s (5 m/s for prismatic coordinates), is recorded as an implausible spike and screened from motion classification. This conservative heuristic does not certify sensor validity; sparse three-sample motion and a spike can be intrinsically ambiguous. Ordinary 0 → 60° → 0 over two seconds passes. Sustained/repeated motion above the deadband passes. Trace values are never rewritten.

Continuous positions retain all recorded turns. Unwrapping is used only for joints explicitly named in `wrapped_joint_names` with type `continuous`; already unwrapped coordinates are not reduced modulo 2π. NaN/Inf, ragged qpos/qvel, joint metadata shape mismatch, missing/backward/duplicate timestamps are refused. Recorded qvel is supplementary evidence, not a substitute for observed displacement.

Routing uses this evidence for `auto`. `comparative_analysis` still chooses Manim; an explicit 3D requirement still requires Blender. The production decision records motion evidence. Blender process/asset failures stay blocked where 3D is required.

## H1 playback

`phase_playback()` computes source interval / **that phase's integer-frame duration**. Setup and analysis phases have identical source endpoints and display `정지 · 분석`. Each exported frame records phase, source time, presentation time, state and speed. The payload and production renderer provenance carry the same per-phase records. Blender uses persistent frame visibility drivers for the phase label; the reference hand path is static, so it does not suggest motion during a hold.

For the tested H1 trace: source duration 2.0 s, setup 3.9 s, motion 3.9 s, analysis 3.9 s. The motion label is **0.51×** (2/3.9), not 0.17× (2/11.7). Tests also cover 2/4 = 0.5×, 2/8 = 0.25×, 1× and reverse replay.

The existing timeline contract maps first and last phase frames to the source endpoints. Reported speed is the phase-average source-seconds/presentation-seconds rate; the final endpoint occupies its final frame interval. It is not an assertion of constant instantaneous speed at every interpolation step. Interpolated qpos still passes through MuJoCo FK to produce mesh transforms; Blender does not integrate physics. Existing joint ordering, limits and FK checks remain active.

## PID frame mapping

`PIDPlayback` maps video frame → `source_time_for_frame()` → latest recorded sample at or before that time. All displayed values (setpoint/error/P/I/D/PWM/motor/encoder/count/index) come from that **one discrete sample**. P/I/D terms are calculated from its recorded controller states and gains. PWM and encoder curves use steps. All current values, including motor speed, use zero-order hold; no interpolated sensor/count/controller values are invented.

The setpoint phase holds the initial sample, motor_response progresses through the source trace, and pid_terms explicitly replays the same trace. Replay never runs the plant again. The renderer's animation callback selects an integer frame at every render update; it no longer has an independently timed ValueTracker. Optional `V115_FRAME_DEBUG=/path/frames.json` records the exact states used by those updates. The default report remains small.

Inspect selected frames without rendering:

```bash
uv run python scripts/inspect_frame_state.py --trace <run>/trace.json \
  --timeline <run>/timeline.json --frames 0 140 141 281 282 421
uv run python scripts/validate_mechanism_render.py <run>/production_report.json \
  --pid-frames /path/frames.json
```

The mapper preserves recorded setpoint changes. The current numerical PID generator still has a constant setpoint; adding a new setpoint scheduler is outside this change. Tests of changed setpoints concern playback of recorded states, not new simulated behaviour.

## Timeline validation

The schema remains `mechanism-timeline/v1`. Both source endpoints, including backward replay endpoints, are checked against both stored bounds and caller-supplied trace bounds. Integer frame continuity, phase order, duration/second fields, hold endpoints, nonfinite values, last-frame mapping and content hash are checked. Completed render reuse also validates the saved timeline, its identity hash and frame count. Technical decode alone never substitutes for these state checks.
