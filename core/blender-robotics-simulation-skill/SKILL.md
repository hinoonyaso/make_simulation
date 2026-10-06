---
name: blender-robotics-simulation-skill
description: Build Blender robotics spatial explanations and physics-backed scenes, using actual solver outputs, shared traces, reusable assets, studio rendering, and faithful 2D handoffs.
metadata:
  version: "5.7-mechanism-and-surface-craft"
---

# Blender Robotics Spatial

Use Blender only when 3D space materially improves understanding. Story/timing comes from the compact manifest.

## Non-negotiables
- A shared trace does not guarantee shared timestamps. Match the displayed plan/map and robot pose to the intended source time; if showing a historical snapshot beside later playback, label the different times and narrate that relationship explicitly.
- Classify Explanation / Trace playback / Simulation / Model execution correctly.
- Frames, axes, units, transforms, and evidence must be correct.
- State changes are first-class: keyframe reusable objects instead of rebuilding the scene for every beat.
- If real computation/simulation exists, consume one shared trace/config; explanatory keyframes must not masquerade as simulation.
- Use reusable `.blend`/procedural assets before regenerating hero geometry. When the episode names a specific real robot, check the registry for a matching `raw_mesh_set` (`asset_registry.py list --tool blender --kind raw_mesh_set`) before defaulting to an abstract primitive.
- `raw_mesh_set` assets (imported STL/DAE) are static geometry only, no joints — rig them via the matching `reference.*` urdf/xacro origin/axis/limit before posing. Procedural primitives (e.g. `add_stylized_robot_arm`) are already posable out of the box.
- Auto-frame hero subjects from their world bounds before hand-tuning camera; avoid small objects floating in empty space.
- Default look = bright studio floor via `templates/studio_utils.py` (EEVEE, AgX Punchy, concrete tiles, soft area lights, native 30 fps, full frame). Reference: `pilots/01_teb_reference` (S1/S3). `scene_kit.py` remains for dark technical shots.
- Mobile-robot episodes use the real TurtleBot3 mesh (`studio_utils.load_turtlebot3`) and use solver wheel orientations for physical replay, or `diff_drive_wheel_angles` for a declared kinematic illustration; state when the planner's footprint differs from the shown robot.
- Never Workbench for delivery, never render below 24 fps and time-stretch; `scripts/check_scene_style.py` fails both.
- Final >=1920x1080; use 2560x1440 for flagship/overlay masters when practical.
- Dense equations stay in Manim. No photoreal detail that does not teach.

## Workflow
1. Read active beat(s), trace path, frames/units.
2. Lookup reusable asset deterministically (`procedural` = posable now; `raw_mesh_set` = needs rigging from its `reference.*` urdf/xacro first).
3. Build/load mechanism; define object states or trace playback.
4. Bootstrap PREVIEW and auto-frame subjects; length = the beat's narrated `sec` from the manifest.
5. Render 3–4 representative frames; fix silhouette/occlusion/framing.
6. Apply one reviewer patch if blocker/high.
7. FINAL/DELIVERY; HERO only for short flagship shots.
8. Write each rendered beat's output path into `visual_manifest.json` `beats[].media` (relative to the manifest), plus `media_in`/`media_out` when one shot file carries several beats.
9. Handing off to a Manim top view: end on `studio_utils.top_view(width_m)` and verify with a blended overlay of both frames before the final render.

## On-demand references
production / evidence / one matching topic.

## Quality gate
3D adds understanding; subject is visually dominant; state transition is readable; trace is faithful when used; lighting separates forms; axes are correct; final >=1080p.

## Show the mechanism

- Choose wide views to establish space and close-ups/top views to expose the decisive clearance, contact, ray, or component. Keep object identity and orientation across changes; a continuous explanation need not be a continuous camera move.
- Settle the camera during a comparison. Sequence camera, object, and overlay changes so they do not compete for attention. Avoid a long orbit/crane with no explanatory purpose.
- Frame the manifest's attention target, not just the robot's global bounds. For a planning beat, that may be the robot footprint and a narrow passage together.
- In real rendered frames, verify route/obstacle/cost-region separation and the robot silhouette. Bright studio lighting must not wash out semantic overlays; shorten irrelevant room context before adding detail.
- Detection, map update, planning and execution must follow the supplied evidence and phrase anchors. A physical object may exist before detection; show that distinction when relevant. Do not move the robot along a route that the teaching sequence has not yet made understandable.

## Critical excerpt before full production

Render the Director-selected contiguous beat IDs with their measured narration before full production. Preserve the same setup/state needed for the inference; a detached result shot is insufficient. Use inexpensive preview settings and the existing manifest ranges. After story/timing approval, reuse the working objects for the full render.

At an abstraction or renderer handoff, match stable landmarks, semantic colors and orientation. Use a genuine geometric transform only when the mapping is valid; otherwise use an orienting cut. Changing rendering style alone does not explain the relationship.

After helper/material changes, verify the rendered result rather than trusting cached output; rerender the affected excerpt without stale caches when necessary. For line geometry, inspect interior fill as well as stroke opacity. Build missing behavior locally when kits are protected, and record concrete reusable kit candidates in the episode README.

## Physics-backed robotics scenes

For this user's robotics episodes, combine the approved discovery explanation with physics-backed spatial setup/outcome when physical motion or contact is relevant. Read `references/evidence.md` for the simulation contract before building such a scene. Choose an installed engine capable of the needed actuation/contact; Blender may render a simulation from another engine. Do not silently substitute keyframed robot poses when the requested engine/model cannot run.

Compute and validate the physical run before final animation. Export measured solver state, controller commands and relevant contacts; both Blender and Manim consume this run. A robot driven by motor/force/torque inputs may deviate from a planned path. Preserve that difference rather than teleporting it onto the reference. The planner may be a simplified educational model; physics execution does not turn it into Nav2/DWB.

Kinematic props, externally prescribed obstacle motion, pose-replayed robots and solver-driven bodies must be distinguished. A dynamic falling prop beside a pose-keyframed robot is not proof of physically simulated robot navigation. Geometry, collision shapes, wheels/joints and planner footprints need explicit matching or documented approximations. Keep missing features local when shared kits are protected.

## Frame the physical response

Choose the view from the event being taught: a wide view establishes route/goal; a closer oblique or top view can expose turning, wheel actuation, clearance or contact. Use a purposeful cut or short settled move when the decisive event is too small in the wide view. Preserve landmarks and travel direction; do not impose a fixed number of shots or add camera motion without explanatory value.

Judge scale from the deciding feature at delivery resolution. A small robot can establish a corridor, but cannot be the only view if wheel/contact detail explains the result. Keep reference/actual lines legible without covering the robot or contact point. Reveal actual history only up to the displayed solver time; show the final full history when comparing completed runs.

Replay solver wheel orientations when available; kinematic wheel-angle helpers are an explicitly scoped fallback, not a replacement for measured wheel response. For final held states, set pose and curve reveal from the intended source sample explicitly. Blender curve datablocks may retain animation after object animation is cleared: verify the actual held comparison render, not just the moving preview. Keep any new close-up/replay helpers local when kits are protected.

## Refine the studio image before expensive rendering

For requested visual polish, read `references/production.md` for material/light/camera diagnosis. Use a cheap comparison at the same recorded pose and source time: baseline versus a candidate that fixes a named visual weakness. Choose from rendered evidence, then check the moving excerpt and renderer handoff. Do not change physical geometry, outcomes or the established bright studio identity to make a shot prettier.

Check all changed camera cuts at entry, the deciding event and exit, not only a flattering settled frame. Use `references/production.md` for imported-surface diagnosis and consistency across the selected views.

Choose material response from object identity and teaching hierarchy; tune lights to expose silhouette and surface form without washing out semantic paths. Compose the robot and deciding clearance/contact/goal together. Depth of field, extra lights and camera motion are optional tools with a specific visual purpose, not quality requirements. Record the chosen candidate and reason in the episode's existing README; keep protected-kit additions local.

## Refine the deciding physical view

For requested surface/camera craft, use the task-led comparison in `references/production.md`: identify the feature the shot must expose, diagnose whether the limit is geometry, shading, lighting or framing, then render a faithful local candidate at the same solver state. A readable route overview alone does not establish close-view surface quality. Preserve physical evidence and stop at the defined target.
