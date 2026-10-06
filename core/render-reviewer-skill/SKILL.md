---
name: render-reviewer-skill
description: One-pass QA of real rendered previews, focused on comprehension, state continuity, subject scale, and production defects.
metadata:
  version: "2.1-mechanism-and-token-proof"
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

For acceptance, review blocker/high issues. When craft refinement is requested, also assess the defined targets and record nonblocking observations:
1. attention target + hero subject scale / wasted frame area
2. typography/equation readability
3. state continuity: did a persistent object transform, or did the video unnecessarily reset like slides?
4. competing motion / pacing / narration sync
5. data integrity: plotted/animated values match supplied trace/config when one exists
6. Blender silhouette, occlusion, auto-framing result, lighting/material separation
7. Manim↔Blender continuity
8. final resolution/fps/missing media

For dense graph/network shots, flag hairball clutter when the active relation cannot be identified; recommend threshold/top-k reveal rather than smaller lines.

Put blocker/high findings in `issues` using `templates/review_report.yaml`; put requested craft findings in `observations` or the optional `craft_targets`, without upgrading taste preferences into blockers. Issue shape:
`severity | beat | time | evidence | owner | patch | verify`.
Do not rewrite full scenes. PASS only if the required central-explanation inspection is complete and no blocker/high defect exists. Report technical gate status and educational review status separately; PASS is not a claim of parity with a reference creator. A Director-owned missing mechanism requires a targeted story/timing patch, not prettier materials. Astra escalation only for central non-trivial defects or failed normal patch.

## Critical excerpt acceptance

For the Director's critical excerpt, first inspect picture with sound and the opening question without reading the script/trace. Record what changed, the visible reason, and the answer to a supported change-of-condition question; then check evidence and scope. Use `references/motion.md` for the listening/motion pass. Record concrete misunderstandings and timestamps; do not grade exact creator resemblance.

For a narrated full explainer, track comprehension, motion and audio inspection separately in the report. A timing-table comparison can support sync analysis but cannot complete a motion or voice inspection. Overall educational PASS requires all necessary modalities inspected and no blocker/high issue. Use `incomplete` when access prevents one of these checks, even if sampled frames are acceptable. A short silent graphics task may mark audio `not_applicable` with a reason.

An important central defect found after the default pass needs its patch verified on new media. Reuse unaffected inspection, but reopen changed picture/speech/timing checks. If the targeted review budget is exhausted, report FAIL/incomplete and remaining defects; never convert the budget limit to PASS. Minor craft improvements may be recorded as observations, not blockers. They may be implemented when polishing is explicitly requested, without turning normal QA into an unbounded redesign.

## Physics evidence acceptance

When the video claims physically simulated robot behavior, read Blender's `core/blender-robotics-simulation-skill/references/evidence.md` as the active evidence reference. Verify that the relevant robot state comes from solver-driven execution, not pose keyframes beside an unrelated dynamic prop. Inspect the run/config provenance, input-to-response relationship, relevant physical checks and shared-run/source-time handoffs. Schema PASS and realistic pixels are insufficient.

Report physics status separately from render and comprehension checks. Missing solver output or required validation leaves physics acceptance incomplete; a known false physics claim, fabricated outcome or old/new-run mismatch is high severity (blocker when it invalidates the central evidence). Check visible collision/penetration, contact response, reference-versus-actual path and model limits. Do not demand engine execution for an honestly labeled illustration or trace-only task. Educational physical simulation is not real-hardware or Nav2 validation.

## Physical explanation and duration review

From the actual excerpt, identify the command/input, visible response and feedback or outcome. Check that reference/actual differences remain visible and source-time handoffs are understandable. If wheel, turning or contact is decisive, inspect that feature at delivery size; a readable route overview does not establish component readability.

For the ending, record whether each held interval offers a new comparison, measurement, limitation or useful inspection. Report repeated outcomes, insufficient local framing and a merely labeled control loop as timestamped craft observations when the central answer remains understandable. Escalate to high only when a necessary relation is unreadable/missing, the claim is misleading, or dead time materially breaks the lesson. Do not equate zero blocker/high issues with excellent craft.

Keep motion/voice, frame comprehension and physics evidence separate. Retain user playback feedback with the exact excerpt and question it covers; do not expand a pace approval into full-video or technical correctness approval. Reinspect changed comparison frames after patches, including complete actual history and exact final state.

## Separate learner evidence from studio craft

Use the first-view procedure in `core/robotics-ai-visual-director-skill/references/director-qa.md` when learner understanding is in scope. Record in the optional `learner_check` report fields whether the respondent was a human novice, an informed user or an agent, the inspected clip, prompts and answers before hints, and the specific misunderstanding. A user's natural pacing approval does not answer the steering-reason question. An agent can diagnose a likely gap but cannot certify novice comprehension. Missing learner evidence is `not_assessed`, not a hidden PASS or an automatic production blocker.

For requested material/light/camera polish, use `references/visual.md` to compare rendered candidates and record timestamped craft observations with an owner, minimal change and visible verification target. Correctness and zero blocker/high defects do not establish polished craft. Escalate only when a defect hides a necessary relation or misleads; aesthetic preferences remain observations. User playback feedback may support motion/audio assessment within its stated scope and must be attributed to the user, without claiming direct tool inspection.

## Decide when requested refinement is finished

Consume the episode's defined targets and inspect their named evidence; read `references/visual.md` for transition/cut and craft completion checks. Record each target as met, needs_revision or uninspected with the exact media/range and reason. A technical PASS does not satisfy a craft target, and a missing playback/novice check does not by itself prove poor quality. Avoid introducing new aesthetic requirements at delivery after the agreed targets are met. Reopen a completed target for a verified regression or changed user scope; necessary correctness defects remain actionable.

End the craft pass when the defined targets are met and blocker/high defects are resolved. Report unavailable evidence separately and preserve overall educational `incomplete` when required modalities remain uninspected. If the existing review budget ends with an unmet target, deliver the scoped status and specific remainder; do not silently declare success or start an unbounded redesign. Summarize achieved improvements, remaining demonstrated defects and unverified questions separately. Do not turn ordinary polish possibilities into a renewed claim that the finished work is inadequate.

## Review the link and the surface separately

When narrative or studio refinement is requested, use `references/visual.md` to inspect whether one discovery provides the next question's evidence and whether the deciding physical view resolves its named surface/framing weakness. Keep understandable, technically correct and polished as separate findings. Record candidate benefit at its exact range; neither a checklist nor zero high issues establishes creator parity.

## Requested creator comparison

When the user requests creator-level comparison, load `references/benchmark.md` as the active comparison reference. Compare matched explanatory functions and record exact evidence in optional `reference_comparison` fields. Zero blocker/high defects and stronger instructions cannot establish parity. Preserve previously met targets; broaden the comparison only when the user's scope changes.
