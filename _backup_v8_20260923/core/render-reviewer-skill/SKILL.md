---
name: render-reviewer-skill
version: 1.0
description: Low-token visual QA for rendered robotics/AI educational videos. Reviews actual preview frames/video, finds only actionable defects, and returns precise owner-routed patches without re-planning the whole episode.
---

# Render Reviewer

Use only **after a preview render exists**. Review the pixels/motion actually produced; do not grade source code from intent alone.

## Goal

Raise production quality with the smallest useful revision loop:
`preview -> evidence-based review -> targeted patch -> re-preview`.

Default to **one review pass**. Allow at most **two revision passes** unless the user explicitly asks for more or a blocker remains.

## Inputs

Consume only what is needed:
- preview video and/or representative frames,
- compact Director beat sheet,
- narration manifest when sync matters,
- visual contract only when cross-tool consistency is in question.

Do not reread full research, scripts, or all source code unless a defect requires it.

## Review order

1. **Blockers**: wrong frame/axis/unit, missing media, clipping, unreadable text, broken render, false evidence implication.
2. **Comprehension**: unclear attention target, overcrowding, insufficient equation dwell, ambiguous 3D depth, continuity break.
3. **Motion**: competing motion, rushed reveal, dead time, camera movement without explanatory value.
4. **Polish**: spacing, silhouette, exposure, material separation, transition restraint, Manim/Blender/Resolve consistency.

Never request decorative changes that do not improve understanding or perceived production quality.

## Minimal workflow

1. Inspect the actual preview. If direct video inspection is unavailable, use `scripts/extract_review_frames.py` and inspect the resulting frames; use timestamps around suspected motion issues.
2. Map each real issue to a beat/time range and one owner: `Director | Narration | Manim | Blender | Resolve | Asset`.
3. Assign severity: `blocker | high | medium | low`.
4. Return only actionable patches. Group repeated symptoms under one root cause.
5. Re-review only changed/affected moments plus hook and final recap.
6. Stop when no blocker/high issue remains; do not chase microscopic polish indefinitely.

## Patch contract

Return compact rows:
`severity | time/beat | observed problem | why it hurts | owner | exact patch | verify`

A good patch is specific enough to execute without reinterpreting the whole video.

## On-demand references — do not preload all

- still-frame composition/readability -> `references/visual.md`
- timing/camera/competing motion -> `references/motion.md`
- final cross-tool/editor QA -> `references/final.md`

Use `templates/review_report.yaml` only when a machine-readable handoff is useful.
