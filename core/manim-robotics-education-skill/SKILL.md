---
name: manim-robotics-education-skill
version: 5.0-source-informed-lite
description: High-polish, low-token Manim reasoning scenes using persistent visual states, data-driven visuals, selective density, rapid preview, and 1080p+ delivery.
---

# Manim Robotics Education

Use Manim for reasoning. The manifest already owns story/timing; do not re-plan it.

## Non-negotiables
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
