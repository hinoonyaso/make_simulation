---
name: manim-robotics-education-skill
description: High-polish, low-token Manim reasoning scenes using persistent visual states, data-driven visuals, selective density, rapid preview, and 1080p+ delivery.
metadata:
  version: "5.2-discovery-preview"
---

# Manim Robotics Education

Use Manim for reasoning. The manifest already owns story/timing; do not re-plan it.

## Non-negotiables
- A shared trace does not guarantee shared timestamps. Match the displayed plan/map and robot pose to the intended source time; if showing a historical snapshot beside later playback, label the different times and narrate that relationship explicitly.
- Beat = persistent object state transition, not slide replacement.
- Intuition before notation; copy/transform visible quantities into equations.
- Use trackers/updaters for continuously changing quantities and `TransformMatchingTex`/state transforms for identity-preserving changes.
- For real computed data, read the shared trace/config; never invent a nicer curve.
- Dense graphs/attention/networks start with top-k/thresholded relations. Visual density is a teaching variable.
- Use `templates/manim_kit.py`; repeated patterns become helpers, not longer scene code. Reference: `pilots/01_teb_reference/manim_shot.py`.
- Spend each beat's narrated `sec` with `BeatClock`; read lengths with `beat_seconds(manifest)`; never hard-code durations after narration exists.
- Top views that follow a Blender shot use `world_window(width_m)` + `turtlebot3_top` so the crossfade is pixel-aligned.
- Optimiser/simulation snapshots are real; frames between them are a visual tween. Say so in the episode README.
- `scripts/check_scene_style.py` must PASS (no `self.clear()` resets, continuity primitives present).
- Final >=1920x1080; prefer 2560x1440 for line/text-heavy masters when practical.
- Main concept dominates frame; no tiny dashboard cards/badges by default.
- At most two semantic highlight colors compete at once.

## Workflow
1. Read only active beat(s) + optional trace path.
2. Load at most one topic/reference.
3. Build the densest reasoning beat first.
4. Use named sections and cheap preview before final render.
5. Preserve visual identity across beats; stagger secondary reveals.
6. Review key frames once; apply only blocker/high patch.
7. After FINAL render, write each beat's output path into `visual_manifest.json` `beats[].media` (relative to the manifest) so Resolve staging can find it.

## On-demand references
production / evidence / one matching topic.

## Quality gate
Viewer knows where to look within one second; symbols map to visible quantities; state changes read continuously; dense structures remain legible; final output is 1080p+.

## Explain the decision

- Render the manifest's decisive relation, not only the final output. Align alternatives to the same coordinates; distinguish unchanged context from the active constraint. Keep enough of the prior state to make the difference inspectable.
- Introduce local labels/color meaning when first needed. Separate invalid region and invalid path by shape/line treatment as well as color; verify contrast on the actual rendered background.
- Use measured phrase anchors for constraint -> comparison -> result. Do not let a decorative path draw lag behind the robot following that path. If playback must pause or slow for teaching, keep trace order and disclose the presentation time mapping.
- If the manifest lacks the evidence needed to explain a choice, return the specific gap to Director. Do not invent scores or silently replace the lesson with a result animation.

## Critical excerpt before full production

Render the Director-selected contiguous beat IDs with their measured narration before full production. Preserve the same setup/state needed for the inference; a detached result shot is insufficient. Use inexpensive preview settings and the existing manifest ranges. After story/timing approval, reuse the working objects for the full render.

At an abstraction or renderer handoff, match stable landmarks, semantic colors and orientation. Use a genuine geometric transform only when the mapping is valid; otherwise use an orienting cut. Changing rendering style alone does not explain the relationship.

After helper/material changes, verify the rendered result rather than trusting cached output; rerender the affected excerpt without stale caches when necessary. For line geometry, inspect interior fill as well as stroke opacity. Build missing behavior locally when kits are protected, and record concrete reusable kit candidates in the episode README.

## Explanation of physical execution

When paired with physics-backed Blender, consume the same physical run and source timestamps. Derive position, velocity, contacts and execution comparisons from actual solver output. Display the reference plan separately from the actual trajectory; identify any historical plan or prescribed input. Do not reuse an old idealized trajectory as the physical result. Match shared landmarks/orientation at the handoff, and disclose presentation pauses/interpolation. Physics provenance and validity are checked separately from trace schema and visual style.
