---
name: render-reviewer-skill
version: 1.2-source-informed-lite
description: One-pass QA of real rendered previews, focused on comprehension, state continuity, subject scale, and production defects.
---

# Render Reviewer

Run only after real frames/video exist. Default one pass; flagship shots may take up to three targeted passes.
Before judging pixels, run `scripts/check_scene_style.py <scene files>`; a FAIL is a blocker owned by the scene author.
Quality bar: `pilots/01_teb_reference/output/pilot_teb_reference.mp4` (studio 3D + continuous 2D, pixel-aligned handoff).
When a value looks wrong, measure it in the data or the saved `.blend` before calling it a defect.

Sample frames deterministically: `scripts/extract_review_frames.py <video> --times <beat starts...>` (default: 7 evenly spaced). Pass beat start times from the manifest's measured `sec` when available.
Load on demand, at most one: `references/visual.md` (still-frame composition), `references/motion.md` (timing/sync), `references/final.md` (final cross-tool handoff).

Review blocker/high issues only:
1. attention target + hero subject scale / wasted frame area
2. typography/equation readability
3. state continuity: did a persistent object transform, or did the video unnecessarily reset like slides?
4. competing motion / pacing / narration sync
5. data integrity: plotted/animated values match supplied trace/config when one exists
6. Blender silhouette, occlusion, auto-framing result, lighting/material separation
7. Manim↔Blender continuity
8. final resolution/fps/missing media

For dense graph/network shots, flag hairball clutter when the active relation cannot be identified; recommend threshold/top-k reveal rather than smaller lines.

Output blocker/high only, in `templates/review_report.yaml` shape:
`severity | beat | time | evidence | owner | patch | verify`.
Do not rewrite full scenes. PASS if no blocker/high defect exists. Astra escalation only for central non-trivial defects or failed normal patch.
