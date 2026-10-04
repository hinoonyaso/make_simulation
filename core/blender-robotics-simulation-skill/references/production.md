# Blender Production Rules

## Stateful objects
Treat a robot, sensor, point, or frame as a reusable object with timed states. Prefer keyframing its transform/material/visibility over deleting and rebuilding the scene.

## Simulation/data separation
Compute simulation/model results outside the presentation layer when possible. Store a compact trace/config and replay it faithfully. This keeps correctness testable and lets Manim/Blender share identical values.

## Reusable assets
Use a stable procedural or `.blend` asset for recurring robots/sensors/graphs. Style variants belong in materials and state changes, not duplicated geometry.

## Automatic framing
Before aesthetic camera tuning, frame the selected hero objects from their world-space bounds with margin. Manual camera work starts from a readable composition, not from guesswork.

## Visual hierarchy
One hero mechanism per shot. Background is simpler/darker/lower contrast. Bevel hero hard surfaces; use material contrast before extra lights.

## Camera/light
35–50mm context, 50–70mm mechanism, 70–100mm detail; orthographic for axis/parallelism comparisons. Soft key + weaker fill + subtle rim. Camera motion only reveals a relation/viewpoint.

## Iteration
Render representative stills before full animation. Use alternate angle previews only to diagnose occlusion/framing, not as extra final shots by default.

## Studio look (validated, pilots/01_teb_reference)
- Light concrete tiles (albedo 0.30-0.37) + world tone ~ far floor, so the horizon dissolves.
- Under AgX, strong emission turns pastel: keep emission 1-2 and saturate the base colour instead.
- Hero shots: DOF focused on the robot itself (not the look-at target), f/2.8; drive shots f/5.6.
- Put the chase camera on the side the robot passes, so obstacles never occlude it.

## Camera mechanics
- Exact top view: `look()` blends the up vector Z->Y; Track-To flips when looking straight down.
- Crane: `crane_pose()` grows distance early and turns late; passing close over props distorts them.
- Key the camera every frame from a smoothed subject path; no constraint chains.

## Data-faithful reveals
- `reveal_trajectory()` keys length fractions with SPLINE mapping. SEGMENTS mapping lagged the robot by 0.31 m.
- Discrete planner updates (e.g. 5 Hz bands) use CONSTANT interpolation; motion uses LINEAR per-frame keys.
- Blender 5 layered actions: use `animation_utils.fcurves()/set_interpolation()`, not `Action.fcurves`.
