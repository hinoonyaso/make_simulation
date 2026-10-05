---
name: render-reviewer-skill
description: One-pass QA of real rendered previews, focused on comprehension, state continuity, subject scale, and production defects.
metadata:
  version: "1.5-physics-evidence"
---

# Render Reviewer

Run only after real frames/video exist. Default one pass; flagship shots may take up to three targeted passes.
Before judging pixels, run `scripts/check_scene_style.py <scene files>`; a FAIL is a blocker owned by the scene author.
Quality bar: `pilots/01_teb_reference/output/pilot_teb_reference.mp4` (studio 3D + continuous 2D, pixel-aligned handoff).
When a value looks wrong, measure it in the data or the saved `.blend` before calling it a defect.

Sample frames deterministically: `scripts/extract_review_frames.py <video> --times <times...>`. Include the central explanation's before/during/after states and phrase/event anchors, not only beat starts. Inspect the corresponding moving excerpt with audio for timing claims. If playback/listening is unavailable, compare frame timestamps against measured caption/audio timings and report the limitation; do not claim that stills prove motion or voice quality.
Load on demand, at most one: `references/visual.md` (still-frame composition), `references/motion.md` (timing/sync), `references/final.md` (final cross-tool handoff).

## Comprehension gate

Before technical polish, answer from the actual preview: what changed, what visible evidence explains it, and how does that answer the opening question? Check the central cause -> constraint/comparison -> consequence. Consult manifest/trace to verify, not to fill a gap the viewer cannot see.

A **high** issue includes a missing decisive explanation that leaves the central question unanswered; narration/event order that suggests a false cause; an unreadable decisive feature; or prolonged unexplained dead time that materially breaks the lesson. Alternative aesthetics, exact creator resemblance, and harmless pauses are not high issues.

If the preview lacks sound or necessary decision moments, mark those checks incomplete and request the smallest missing excerpt. A technical gate PASS cannot substitute for this inspection.

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
Do not rewrite full scenes. PASS only if the required central-explanation inspection is complete and no blocker/high defect exists. Report technical gate status and educational review status separately; PASS is not a claim of parity with a reference creator. A Director-owned missing mechanism requires a targeted story/timing patch, not prettier materials. Astra escalation only for central non-trivial defects or failed normal patch.

## Critical excerpt acceptance

For the Director's critical excerpt, first inspect picture with sound and the opening question without reading the script/trace. Record what changed, the visible reason, and the answer to a supported change-of-condition question; then check evidence and scope. Use `references/motion.md` for the listening/motion pass. Record concrete misunderstandings and timestamps; do not grade exact creator resemblance.

For a narrated full explainer, track comprehension, motion and audio inspection separately in the report. A timing-table comparison can support sync analysis but cannot complete a motion or voice inspection. Overall educational PASS requires all necessary modalities inspected and no blocker/high issue. Use `incomplete` when access prevents one of these checks, even if sampled frames are acceptable. A short silent graphics task may mark audio `not_applicable` with a reason.

An important central defect found after the default pass needs its patch verified on new media. Reuse unaffected inspection, but reopen changed picture/speech/timing checks. If the targeted review budget is exhausted, report FAIL/incomplete and remaining defects; never convert the budget limit to PASS. Minor craft improvements may be recorded as observations, not blockers. They may be implemented when polishing is explicitly requested, without turning normal QA into an unbounded redesign.

## Physics evidence acceptance

When the video claims physically simulated robot behavior, read Blender's `core/blender-robotics-simulation-skill/references/evidence.md` as the active evidence reference. Verify that the relevant robot state comes from solver-driven execution, not pose keyframes beside an unrelated dynamic prop. Inspect the run/config provenance, input-to-response relationship, relevant physical checks and shared-run/source-time handoffs. Schema PASS and realistic pixels are insufficient.

Report physics status separately from render and comprehension checks. Missing solver output or required validation leaves physics acceptance incomplete; a known false physics claim, fabricated outcome or old/new-run mismatch is high severity (blocker when it invalidates the central evidence). Check visible collision/penetration, contact response, reference-versus-actual path and model limits. Do not demand engine execution for an honestly labeled illustration or trace-only task. Educational physical simulation is not real-hardware or Nav2 validation.
