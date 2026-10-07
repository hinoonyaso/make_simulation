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

For an explicit surface/lighting refinement or a demonstrated flat studio image, use [surface-lighting.md](surface-lighting.md). It specifies part-based diagnosis, material-only/light-only/combined comparisons, effective shader/light evidence, and selection on actual boundaries. A small parameter change or technically readable image does not by itself satisfy a requested refinement.

For a camera refinement, keep materials, lights and source pose fixed while comparing framing. Preserve deciding contact/clearance, robot-relative direction, semantic overlays and bright studio identity. Verify the selected view at entry, decisive state and exit before full rendering.

## Imported surfaces and consistency across shots

Diagnose the rendered surface before adding detail: material response, normals/smoothing, coarse silhouette and lighting are different causes. Use selective smoothing on curved surfaces while retaining actual hard boundaries. If the silhouette itself is coarse, changing normals will not repair it; choose a faithful existing asset or a documented render-only refinement when needed. Keep physical collision dimensions and solver output intact, and verify the deciding clearance/contact remains truthful. Avoid blanket subdivision or beveling that rounds mechanical edges or shifts the perceived gap.

Compare the chosen material/light treatment in context, clearance/contact and goal/detail views at delivery size. Metal/plastic/rubber should retain recognizable value and highlight relationships across cuts; detail should not turn to uniform gray, black clipping or sparkle. Tune competing floor/path reflections locally before increasing every light or making every surface glossy. Inspect motion-dependent noise and highlights in moving media; record that check unavailable if only stills can be viewed.

For each changed camera cut, render its first visible pose, the critical event/worst plausible occlusion from the trace, and last pose. Verify the whole necessary robot feature and obstacle/goal relation fit together. A tight end-state crop may cut out an approaching robot; a lower clearance view may hide its wheels behind the obstacle. Correct camera bounds/angle before rendering the full shot. Compare adjacent cuts for landmark orientation, exposure, apparent scale and overlay space. These are checks of the actual shot, not a fixed camera-count or robot-size rule.

## Task-led studio craft beyond basic readability

For a requested studio upgrade, start from a real deciding frame and name the remaining weakness precisely. Distinguish a route/context shot from a contact, turning or stopping detail; choose a view that exposes that feature while retaining enough landmark context to orient the viewer. Compare the candidate with the existing view at the same solver time. A tighter crop is useful only if the deciding relation gains clarity; settled cameras are acceptable when motion would compete with it.

Separate geometry from light response before changing either. Imported TurtleBot3 meshes already receive angle-based smoothing in the current kit; inspect the actual mesh and rendered silhouette before repeating smoothing as a supposed fix. Retain planar deck faces and mechanical boundaries. For a visibly coarse analytic drum/ring, a local render-only tessellation candidate may improve the silhouette while preserving its dimensions; for a measured robot asset, use a faithful higher-detail asset when available. Do not round, remesh or invent mechanical details that change perceived clearance. If faithful geometry is unavailable, record the asset limit rather than claiming a material change repaired it.

Choose light response by the deciding feature: plate layers and gaps need controlled fill, rubber and sensor housings need material separation, and contact/clearance needs a grounded shadow with an inspectable gap. Tune one diagnosed cause at a time; keep camera and solver pose fixed for a material/light comparison. Check the selected treatment in context and detail, including the cut boundaries, for lost gaps, black clipping and washed-out paths. Added gloss, depth of field, texture or lights must demonstrate a specific benefit in rendered pixels. Moving highlights/noise require actual playback evidence.

If reusing unaffected frames, verify all visible state, including goal annotations and material animation, rather than checking only robot poses. Keep the scene source capable of reproducing the retained states; a same-frame pixel comparison can verify a local reuse claim. Record changed/reused ranges and the remaining asset or playback limits in the existing README. These are episode-local implementations while kits are protected.

## Reveal the deciding component

When whole-body motion hides the mechanism, isolate the faithful wheel pair, hinge, contact region or internal part with a local close-up, selective visibility or an explanatory cutaway. Keep left/right, axes, source pose and landmarks identifiable through the abstraction. If the requested lesson includes rolling/contact, a wheel-pair comparison and a local contact explanation have different jobs: retain the pair view, then use a settled low/oblique view showing the relevant wheel phase and a fixed ground landmark together. Do not add a contact shot when contact is not part of the inference. Indicate removed/transparent parts as a rendering aid; do not suggest the solver geometry or real machine was modified. Do not invent internal hardware to fill an asset gap.

Frame the decisive component at delivery size; full-robot bounds are unnecessary in a clearly oriented component shot. Bridge its geometry to the Manim relation using the same state and semantic roles, then return to the recorded body response. Render input cues as targets unless measured response exists. Recorded root/joint poses support rotation and center travel, but alone do not establish an exact contact point, slip or contact force. Verify the required trace fields before claiming those quantities; collect missing evidence only within the authorized scope, or narrow to disclosed ideal geometry. No quantitative contact-force arrows without force data; a qualitative explanatory arrow must be identified as such.

Surface improvements should make curved silhouettes, part boundaries and contacts readable. Inspect entry, mechanism state and exit against the baseline at the same source time; attractive lighting alone does not demonstrate the mechanism. Preserve the user's bright studio and asset identity. If finer faithful geometry or local visibility helpers are needed, prototype within the pilot, record the kit candidate and keep shared kits unchanged.

## A component must visibly act

For requested mechanism repair, show faithful articulation from recorded joint orientations/positions and its corresponding body response. Establish the complete object first, reveal the deciding part with local visibility/cutaway, then retain enough ground/axle context to read what moves relative to what. Select a side/oblique view exposing the wheel face or joint motion; a top view of a nearly symmetric wheel can hide rotation. Set camera bounds from the necessary part's swept positions over the source interval, not a single flattering pose.

Validate trace wheel order, world/local transforms and initial joint axes before animating. For each displayed frame, retain source sample/time and check root/joint transforms against the record. Interpolated/retimed states are presentation, not new solver output. A command target must never supply the measured joint pose when recorded response exists. Keep command cues and response labels distinct; a continuous solver interval has changing commands, so do not keep a frozen command number looking current.

If symmetry hides recorded rotation, attach a small render-only phase mark rigidly to the actual wheel pivot. Document it as an annotation, preserve the faithful mesh/dimensions and do not add fabricated spokes, mechanical geometry or forces. Validate that the mark follows the recorded wheel transform and identify any removed body geometry as a viewing aid. Inspect first/middle/last and a dense short frame sequence for turn direction, occlusion and phase change. This supports observable displacement; normal-speed motion judgment remains a separate inspection.

Keep missing implementation local while kits are protected. Reusable candidates include recorded-joint component replay, trace-interval swept bounds and phase annotations, each with axis/order checks. Do not require an exploded cutaway for a topic whose natural view already makes operation readable.

## Component framing after R14

For a wheel-operation close-up, frame the necessary wheel pair, axle reference and local ground contact over their swept interval. Whole-room or whole-robot bounds can leave the wheels too small amid empty floor even when nothing is cropped. Compare the baseline and a tighter faithful view at the same solver time, with final captions: the rotating phase/contact and left/right roles should be easy to locate at delivery size. Preserve enough ground/body context to explain relative motion, and return to context when body travel becomes the task. Avoid a universal size percentage; choose bounds from the relation being taught.

Use material/light separation to expose tread, wheel face and axle depth in that selected view, retaining bright studio identity. Diagnose a gray, flat result at fixed camera/pose before adding lighting or geometry. Verify cut entry, deciding state and exit for contact visibility, readable phase, consistent exposure and caption space. Keep camera-bound helpers local to the pilot while kits are protected, and record only demonstrated reusable candidates.

## Keep the mechanism connected and diagnose its surface

In a requested component cutaway, retain the shared mechanical relation after hiding housing. For differential drive, use an explicitly render-only axle reference, body-center/heading cue and ground history, all driven from recorded wheel/root transforms. An annotation connecting wheel centers is not a claim that the asset has a visible shaft. Preserve wheel order, rigid wheel phase markers and source-time mapping; return to the complete body in the same run. No quantitative contact forces without force data. Inspect entry, removed-body state and restored-body state at delivery size.

For a demonstrated flat body treatment, compare baseline, material-only and material-plus-light candidates with identical pose/camera/exposure. Separate metal/plastic/rubber through plausible roughness and reflectance, preserve planar deck faces, and use broad light/fill to resolve layers/contact without washing out paths. Do not round imported geometry to imitate a polished surface. Choose the treatment on actual native pixels in context and detail: compare plate/side boundaries, dark tyre separation and grounded contact shadows, not added gloss or material names. Where the named boundary remains indistinct, record the unresolved gap rather than claiming polish from a new roughness value. Moving highlight/noise judgments require playback. Record the candidate choice and retained geometry in the pilot README.

Subsequent experiment shots should foreground the changed relation after the first established setup. Keep sufficient ground/orientation context; avoid repeating camera choreography simply because another case starts. Local annotation/material helpers are kit candidates only after their rendered benefit and pose invariants are verified.
