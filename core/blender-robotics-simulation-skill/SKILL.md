---
name: blender-robotics-simulation-skill
version: 5.0-source-informed-lite
description: High-polish, low-token Blender spatial explanations using reusable stateful objects, automatic framing, shared traces, reusable assets, and 1080p+ delivery.
---

# Blender Robotics Spatial

Use Blender only when 3D space materially improves understanding. Story/timing comes from the compact manifest.

## Non-negotiables
- Classify Explanation / Trace playback / Simulation / Model execution correctly.
- Frames, axes, units, transforms, and evidence must be correct.
- State changes are first-class: keyframe reusable objects instead of rebuilding the scene for every beat.
- If real computation/simulation exists, consume one shared trace/config; explanatory keyframes must not masquerade as simulation.
- Use reusable `.blend`/procedural assets before regenerating hero geometry. When the episode names a specific real robot, check the registry for a matching `raw_mesh_set` (`asset_registry.py list --tool blender --kind raw_mesh_set`) before defaulting to an abstract primitive.
- `raw_mesh_set` assets (imported STL/DAE) are static geometry only, no joints — rig them via the matching `reference.*` urdf/xacro origin/axis/limit before posing. Procedural primitives (e.g. `add_stylized_robot_arm`) are already posable out of the box.
- Auto-frame hero subjects from their world bounds before hand-tuning camera; avoid small objects floating in empty space.
- Default look = bright studio floor via `templates/studio_utils.py` (EEVEE, AgX Punchy, concrete tiles, soft area lights, native 30 fps, full frame). Reference: `pilots/01_teb_reference` (S1/S3). `scene_kit.py` remains for dark technical shots.
- Mobile-robot episodes use the real TurtleBot3 mesh (`studio_utils.load_turtlebot3`) and compute wheel spin for the shown geometry with `diff_drive_wheel_angles`; state when the planner's footprint differs from the shown robot.
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
