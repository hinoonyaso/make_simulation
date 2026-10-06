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
- Optional hero DOF focuses on the actual subject, not merely the look-at target. Keep contact/clearance/reference lines sharp together; deepen or disable DOF when it hides the deciding relation. Aperture follows that task rather than a fixed hero preset.
- Put the chase camera on the side the robot passes, so obstacles never occlude it.

## Camera mechanics
- Exact top view: `look()` blends the up vector Z->Y; Track-To flips when looking straight down.
- Crane: `crane_pose()` grows distance early and turns late; passing close over props distorts them.
- Key the camera every frame from a smoothed subject path; no constraint chains.

## Data-faithful reveals
- `reveal_trajectory()` keys length fractions with SPLINE mapping. SEGMENTS mapping lagged the robot by 0.31 m.
- Discrete planner updates (e.g. 5 Hz bands) use CONSTANT interpolation; motion uses LINEAR per-frame keys.
- Blender 5 layered actions: use `animation_utils.fcurves()/set_interpolation()`, not `Action.fcurves`.

## Material, lighting and camera polish

Use the existing bright studio/reference palette as the baseline. Compare inexpensive stills at the same source pose/camera before changing another factor. When the camera itself is under review, keep pose, materials and lights fixed. Keep a baseline and only enough candidates to diagnose the named weakness; avoid open-ended style exploration. Select a candidate for a visible improvement, then verify representative moving frames and the adjacent 2D handoff before full rendering.

| Visible weakness | Targeted candidate | What to verify in rendered pixels |
| --- | --- | --- |
| Robot surfaces merge into uniform gray | Different roughness/material response for existing metal, rubber and plastic components; restrained value separation | Plates, wheels and gaps read at delivery size without arbitrary semantic recoloring |
| Form appears flat or contact floats | Adjust soft key direction, fill balance and grounded contact shadow | Silhouette and surface normals remain readable; shadow locates contact without hiding the gap |
| Bright floor washes out paths or materials | Reduce competing floor/highlight contrast, tune roughness/light balance | Green reference and blue actual history remain distinct, with useful highlight detail |
| Faceting or import shading distracts in close view | Inspect normals and smoothing; use local render-only treatment where appropriate | Hard rims stay intentional; cylinder sidewalls/highlights are clean; collision shape stays unchanged |
| Robot/detail competes with room or text | Reframe the deciding robot-plus-contact/goal bounds and simplify context | The feature is readable, uncropped and not covered by a label |
| Cuts change perceived turn direction | Match landmarks, robot-forward cue and camera side; use an orienting view when needed | A newcomer can follow robot-relative left/right across the cut |

Use metalness/roughness according to the represented surface, not to make every object glossy. Microtexture and bevels are useful only when they improve scale/form at the intended view; do not imply physical dimensions/contact that the collision model does not support. Preserve protected kits and semantic colors. Strong cinematic grading, dark backgrounds, shallow focus and continuous camera movement are not default upgrades.

In motion, inspect highlight/shadow stability, flicker/noise and readability at turn/contact/stop, not only a flattering still. A smoother camera must preserve event timing and exact solver poses; it should settle for the decisive relation. Record the baseline weakness, selected source-time example, candidate and observed improvement in the existing episode README. Report remaining craft observations separately from blocking technical or evidence defects.

## Imported surfaces and consistency across shots

Diagnose the rendered surface before adding detail: material response, normals/smoothing, coarse silhouette and lighting are different causes. Use selective smoothing on curved surfaces while retaining actual hard boundaries. If the silhouette itself is coarse, changing normals will not repair it; choose a faithful existing asset or a documented render-only refinement when needed. Keep physical collision dimensions and solver output intact, and verify the deciding clearance/contact remains truthful. Avoid blanket subdivision or beveling that rounds mechanical edges or shifts the perceived gap.

Compare the chosen material/light treatment in context, clearance/contact and goal/detail views at delivery size. Metal/plastic/rubber should retain recognizable value and highlight relationships across cuts; detail should not turn to uniform gray, black clipping or sparkle. Tune competing floor/path reflections locally before increasing every light or making every surface glossy. Inspect motion-dependent noise and highlights in moving media; record that check unavailable if only stills can be viewed.

For each changed camera cut, render its first visible pose, the critical event/worst plausible occlusion from the trace, and last pose. Verify the whole necessary robot feature and obstacle/goal relation fit together. A tight end-state crop may cut out an approaching robot; a lower clearance view may hide its wheels behind the obstacle. Correct camera bounds/angle before rendering the full shot. Compare adjacent cuts for landmark orientation, exposure, apparent scale and overlay space. These are checks of the actual shot, not a fixed camera-count or robot-size rule.

## Task-led studio craft beyond basic readability

For a requested studio upgrade, start from a real deciding frame and name the remaining weakness precisely. Distinguish a route/context shot from a contact, turning or stopping detail; choose a view that exposes that feature while retaining enough landmark context to orient the viewer. Compare the candidate with the existing view at the same solver time. A tighter crop is useful only if the deciding relation gains clarity; settled cameras are acceptable when motion would compete with it.

Separate geometry from light response before changing either. Imported TurtleBot3 meshes already receive angle-based smoothing in the current kit; inspect the actual mesh and rendered silhouette before repeating smoothing as a supposed fix. Retain planar deck faces and mechanical boundaries. For a visibly coarse analytic drum/ring, a local render-only tessellation candidate may improve the silhouette while preserving its dimensions; for a measured robot asset, use a faithful higher-detail asset when available. Do not round, remesh or invent mechanical details that change perceived clearance. If faithful geometry is unavailable, record the asset limit rather than claiming a material change repaired it.

Choose light response by the deciding feature: plate layers and gaps need controlled fill, rubber and sensor housings need material separation, and contact/clearance needs a grounded shadow with an inspectable gap. Tune one diagnosed cause at a time; keep camera and solver pose fixed for a material/light comparison. Check the selected treatment in context and detail, including the cut boundaries, for lost gaps, black clipping and washed-out paths. Added gloss, depth of field, texture or lights must demonstrate a specific benefit in rendered pixels. Moving highlights/noise require actual playback evidence.

If reusing unaffected frames, verify all visible state, including goal annotations and material animation, rather than checking only robot poses. Keep the scene source capable of reproducing the retained states; a same-frame pixel comparison can verify a local reuse claim. Record changed/reused ranges and the remaining asset or playback limits in the existing README. These are episode-local implementations while kits are protected.
