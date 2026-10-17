# Cross-Pilot Visual QA

## Scope and decision

- Audit branch: `audit/cross-pilot-visual-consistency`
- Audited source HEAD: `331bdfea6625b6cef5fa90f64f77e3702db40c03`
- PR #10 at audit time: Open / Draft; this worktree is separate and does not modify PR #10 or `main`.
- Review method: existing MP4s and their recorded reports, sampled frames, two contact sheets, shared visual-system source inspection, and one current-source PyBaMM-backed Blender still render.
- No existing full video was re-rendered. The generated render is one frame used to resolve a suspected title-margin defect.

**Overall visual design score: 7.3/10 (subjective snapshot audit).** Existing work has a recognizable visual language: semantic input/output colors, restrained technical-dark explanations, studio-light physical scenes, and consistent Korean typography choices. The score is limited by uneven provenance across older pilots, visible renderer handoffs that are not consistently bridged, and a mixture of current-source stills and historical final videos. It is not a motion-quality or educational-effectiveness score.

| Dimension | Score | Evidence-based assessment |
|---|---:|---|
| Visual consistency | 7.5/10 | Semantic colors and two visual profiles are shared by current education renderers; older robotics pilots predate or do not record the same source contract. |
| Typography | 7/10 | Main headings and Korean captions are legible in sampled frames. Small numeric annotations in dense technical scenes need full-resolution, normal-speed review; contact-sheet scaling is not sufficient for a readability PASS. |
| Layout | 7.5/10 | Physical subjects generally have useful separation. DWB handoff samples show a brief loss of path context, and some technical frames are dense. |
| Color / lighting | 8/10 | Light physical scenes and dark analytical scenes serve different purposes; model silhouettes and orange obstacle/input accents remain distinct. Do not force one background across renderers. |
| Educational communication | 7/10 | Several samples connect a physical object to its analytical representation. Still samples cannot establish that the complete explanation is understandable. |
| Motion QA | INCOMPLETE | This audit sampled frames, not complete normal-speed playback. Moving Obstacle's prior review also marks full motion/audio review incomplete. |

No P0/P1 issue was established. No source-level visual edit met the evidence threshold in this pass. One historical DWB output concern and one renderer-handoff concern are documented below for follow-up against provenance-bound renders.

## Contact sheets and audit artifacts

These files are local audit artifacts under `/tmp`; they are not committed. Their samples come from project outputs, not generated reference imagery.

| Artifact | Contents | SHA-256 |
|---|---|---|
| `/tmp/make_simulation-visual-audit/cross_pilot_contact_sheet.png` | TEB, DWB, Moving Obstacle R18, Robot Arm Manim, H1 Blender smoke, Bearing R6, Gear V14.1, V14.5 bearing stills, V14.5 gear stills, and battery renderer-only frames. | `23db302c4507c3bf1ae65346b8a5473d0c5d06728de6e63e6fefddbf4259e358` |
| `/tmp/make_simulation-visual-audit/renderer_transition_contact_sheet.png` | TEB and DWB handoff samples at 11.4/12.0/12.6 s; Gear V14.1 samples at 33.5/34.0/34.6 s. | `6306bf4a80bbd295ff850ec755ed12054a38e821d4fa8a6caf7f83c1ad42a9e2` |
| `/tmp/make_simulation-visual-audit/battery_render/source-frame-1/battery_still.png` | One 960×540 current-source Blender frame, generated from a validated PyBaMM result to inspect the title margin. | `9735e44698f164253372cee3013f90e598b07c7acadae5b66bf7a75c3b5ee548` |

The full contact sheet labels V14.5 battery stills as non-composite frames and the V14.5 gear stills as non-final output. They must not be interpreted as completed mixed videos.

## Shared design system: guidance versus adoption

The current V14.5 system defines semantic colors, `studio_light` and `technical_dark` profiles, typography/layout values, and motion ranges in `core/visual_primitives/design_tokens.json` and its Python loader. The Manim kit imports the token module and exposes theme, palette, and semantic text helpers. The Blender scene kit builds semantic materials from shared tokens; `studio_utils.py` applies the selected world profile. Current Battery and Gear education scenes call those helpers.

That is real but partial adoption. TEB/DWB and older pilot outputs remain their own established visual programs; the audit found no basis to migrate them wholesale to V14.5 tokens. Shared meaning (input/output/obstacle/trajectory) is more consistent than identical backgrounds or identical layouts. Preserve that distinction.

## Content review

| Content | Information | Layout | Typography | Color | Consistency / provenance | Motion QA |
|---|---|---|---|---|---|---|
| TEB | 7.5/10 — robot, obstacle, path, and analytical frame are identifiable in sampled views. | 7/10 — subject separation is good; explanatory frame is denser. | 7/10 — main labels readable in samples; small annotations not assessed at native playback size. | 8/10 — orange obstacle and purple/cyan path remain distinct across the sampled renderer handoff. | 6/10 — historical local MP4 has no embedded renderer/source/input provenance. | INCOMPLETE; sampled 0, 31, 62 s and 11.4/12.0/12.6 s handoff only. |
| DWB | 7/10 — candidate path and cost ranking can be identified; the old output has a cluttered cost-table moment. | 6.5/10 — sampled 12.0 s has robot/title but no visible path, which reappears by 12.6 s. | 6.5/10 — cost rows are small and crowded in the historical 36 s frame. | 8/10 — obstacle and path colors remain clear. | 5.5/10 — old MP4 is not bound to a source hash; current B04 source segment renders cleanly. | INCOMPLETE; sampled 0, 36, 70 s and 11.4/12.0/12.6 s handoff only. |
| Moving Obstacle R18 | 8/10 — the obstacle/robot/path relationship is clear in the sampled beats. | 7.5/10 — physical and explanatory layouts are appropriately distinct. | 6.5/10 — sampled overlays are small at contact-sheet scale; full-resolution reading not certified here. | 8/10 — green planned path, cyan/blue reference, and orange obstacle are distinct. | 7/10 — output has trace/pose validation and a review record, but no complete renderer-source binding was found. | INCOMPLETE; report records mosaic review of 90 frames, not complete continuous playback/audio. |
| Robot Arm Manim | 7/10 — arm pose and target/actual graph coexist, but the complete lesson is a short historical clip. | 7/10 — arm and plot have separate regions. | 6.5/10 — graph ticks are small in the sampled video. | 7.5/10 — target/actual curves and joint colors are distinguishable. | 5.5/10 — historical output lacks source/input provenance. H1 Blender file is a separate 2.03 s smoke, not a final. | INCOMPLETE; sampled 1, 4.9, 8 s / H1 0.1, 1.0, 1.9 s. |
| Bearing R6 | 8.5/10 — components and rolling elements are visually prominent; the object reads clearly. | 8/10 — clean 3D composition with supporting text separated to the side. | 7/10 — labels are readable in sampled frames, but small text at 540p warrants full-speed review. | 8/10 — metal races, balls, and cage are visually separable. | 7/10 — validated 84 s silent preview and asset provenance exist; exact source commit/render-code hash is not in the report. This is pre-V14.5. | INCOMPLETE in this audit. The prior user review was PASS for R6 at normal speed, but it does not validate the later V14.5 sources. |
| Gear V14.1 | 7.5/10 — input/output ratio and counter-rotation are shown. | 7/10 — gear pair dominates the physical frame; the analytical screen has several concurrent labels. | 6.5/10 — equation labels are small in 540p samples. | 8/10 — input/output use distinct semantic colors. | 6.5/10 — 80 s pre-V14.5 mixed preview exists; no exact source binding established in this audit. | INCOMPLETE; samples at 5, 39, 64 s and around 33.5–34.6 s only. |
| Battery V14.5 | 7/10 — cell, electrodes, SOC gauge, and Manim computation layers have clear roles in individual stills/layers. | 7/10 — current-source frame has safe title margin; no completed mixed composition was available. | 7/10 — current-source title is not clipped; detailed graph tick readability remains unreviewed. | 8/10 — light/dark profile separation is effective and cell/electrode colors are distinct. | 7.5/10 — current Blender still uses a validated PyBaMM result; output layers are not a final composite. | INCOMPLETE; one Blender still and historical layer outputs only. |

Scores are subjective assessments of the sampled visual evidence, not a metric produced by an automated checker. `INCOMPLETE` means motion has not been established by this frame-based audit.

## Observations and priorities

### P2 — Historical DWB cost panel is crowded (artifact-level, not confirmed in current source output)

- **Scene / time:** DWB historical MP4, approximately 36–37 s.
- **Observed:** candidate command rows are visible behind/near weighted cost values, reducing the table's visual separation in the sampled frame.
- **Source check:** current tracked `pilots/02_dwb_reference/manim_shot.py` SHA-256 is `86a10e066641329b2e78850191d78270a1c89194327ceb69e529a3685873e4b2`; B04 fades the command rows before the cost panel. A current-source 1080p30 render of B04 produced the same tested frame before and after a temporary explicit removal (`mean pixel difference 0`, frame SHA identical). The temporary edit was reverted.
- **Disposition:** no source change. The historical MP4 has no exact source provenance, so it cannot prove a current-source regression. If this MP4 is still a delivery artifact, rebuild it from current source and bind the output report to the code/input hashes.
- **Risk / verification:** a rebuild could change legacy timing; compare the same cost-panel timestamp and preserve the trace and timeline.

### P2 — DWB path context drops during the renderer handoff (sampled-sequence concern)

- **Scene / time:** DWB handoff at 11.4, 12.0, and 12.6 s in the historical local MP4.
- **Observed:** the 11.4 s studio frame has the route; at 12.0 s the dark analytical frame shows the robot and heading but not the route; by 12.6 s a candidate route is visible again.
- **Root cause:** unknown. The samples show a short representation gap, but do not establish whether the transition is an intentional staged reveal or an unwanted disappearance.
- **Disposition:** no code change because source provenance and continuous normal-speed review are unavailable. On the next provenance-bound render, confirm that the route identity remains understandable through the handoff; if it is intentional, the reveal should read as one staged transition.
- **Risk / verification:** changing the cross-renderer transition could affect timing and semantic mapping. Review continuous playback and compare route/robot IDs and trace timestamps before editing.

### Battery title margin: suspected issue not reproduced

The older local frame raised a clipping concern. A new single-frame render from current HEAD shows the full `18650 EDUCATION MODEL` heading with visible top margin in 960×540. No title-position fix is warranted. This is not a full Battery video review.

## Reproduction and provenance

### Existing videos

| Content | Local file | Output SHA-256 | Format / samples | Source provenance |
|---|---|---|---|---|
| TEB | `/home/sang/make_simulation/pilots/01_teb_reference/output/pilot_teb_reference.mp4` | `2ae70645da50bd48c0155de69f02d0222816c86a5174a46c60b55216f555b615` | 1920×1080, 30 fps, 71.2 s; 0, 11.4, 12, 12.6, 31, 62 s | Legacy ignored output; exact renderer commit, settings, and trace hash not bound to video. Current `manim_shot.py` SHA-256 `67b54edde80f4650fd7a2b0d4488a25731fbcc0d7d65525aba8366677d3eab8f`. |
| DWB | `/home/sang/make_simulation/pilots/02_dwb_reference/output/dwb_reference_ko.mp4` | `8314f6b2280d689cf4a63753b4f056d335bedab64bad2cff02cdf33a1477c961` | 1920×1080, 30 fps, 83.333 s; 0, 11.4, 12, 12.6, 36, 70 s | Legacy ignored output; exact renderer commit/settings/input hashes not bound. Current `manim_shot.py` SHA-256 `86a10e066641329b2e78850191d78270a1c89194327ceb69e529a3685873e4b2`. |
| Moving Obstacle R18 | `/home/sang/make_simulation/pilots/05_moving_obstacle/revision_18/output/planner_control_long_ko_v18.mp4` | `09e8fa56d496fe4980af70a5277bccad5fd0ff39acfb79ec24fc2723db42b095` | 1920×1080, 30 fps, 382.4 s; B08 123.44, B19 333.63, B20 356.20 s | `render_validation.json` and `render_review.json` were present and report trace/pose validation; 90 mosaic frames reviewed. Exact source-tree hash was not linked to the MP4. |
| Robot Arm | `/home/sang/make_simulation/pilots/v10_mujoco_arm/output/mujoco_h1_arm.mp4` | `5bc8d3592d6eed6225e423b02a5a98a037122b6bea397b6d2dd4bd29c04afe58` | 1920×1080, 30 fps, 9.8 s; 1, 4.9, 8 s | Historical output, no renderer/input provenance found. Scene SHA-256 `35f040718ed93e4275b076750cd291d9cb81ba3eaca8b60b727f7232f3e4a4f7`; builder SHA-256 `162043d4508b7a6871edc3c616d122697ead8b50283982f41402f112ff57e5ec`. These hashes identify current files only, not the video's origin. |
| H1 Blender smoke | `/home/sang/make_simulation/pilots/v11_2_h1_blender/output/h1_trace_blender.mp4` | `c057af1ef7c9dfcd706a503e384d62d11d91da772aae76d24771ebe2c8e7be6b` | 1920×1080, 30 fps, 2.033 s; 0.1, 1.0, 1.9 s | Smoke artifact only; not a lesson/final video. |
| Bearing R6 | `/home/sang/make_simulation-r6/pilots/v13_education/output/r6_visual_qa/r6-final/preview.mp4` | `c44219f83365482ef12e0223994b59c0022ff849a83e8c59655d9480109bd457` | 960×540, 30 fps, 84 s; 24, 49, 71 s | `SILENT_PREVIEW`; H.264/full decode PASS; Blender 5.2.1 / Manim 0.21; asset hash recorded. Exact renderer source commit/hash not recorded; pre-V14.5. |
| Gear V14.1 | `/home/sang/make_simulation/pilots/v14_education/output/gear-v14.1-final-fixed/preview.mp4` | `559c54ced14f973614ba6ef529446d5f8e79ca177c62509b76ec846311390cad` | 960×540, 30 fps, 80 s; 5, 33.5, 34, 34.6, 39, 64 s | Historical pre-V14.5 mixed preview; exact source/input binding not established here. |

### Current-source Battery still

| Item | Value |
|---|---|
| Source HEAD | `331bdfea6625b6cef5fa90f64f77e3702db40c03` |
| Scene source | `pilots/v14_education/blender/battery_scene.py`, SHA-256 `9b00ff4651fa42408bc28b02db81656576ef8c1ae0fa809e5bbd24ff7ee3c3a2` |
| Solver | PyBaMM 26.10.0.0, IDAKLUSolver, CPU, SPM/Chen2020, 1C, 1800 s; 361 samples at 5 s; result SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25` |
| Render | Blender 5.2.1 LTS, 960×540, 30 fps, `technical_dark`, still frame 1; renderer asset validation PASS |
| Image | `/tmp/make_simulation-visual-audit/battery_render/source-frame-1/battery_still.png`; SHA-256 `9735e44698f164253372cee3013f90e598b07c7acadae5b66bf7a75c3b5ee548` |
| Limits | One still validates title placement only. It does not validate the mixed Battery sequence, graph labels, animation, audio, or 1080p final. |

## Shared design decisions and next improvements

### Keep

- Continue using the two existing profiles for distinct jobs: studio-light physical scenes and technical-dark analysis. They already provide useful visual contrast across a lesson.
- Preserve semantic colors for input/output, obstacles, candidate paths, and axes. Meaning should follow the object/data when the renderer changes.
- Keep physical models uncluttered. Add explanatory overlays only where they explain a real state or calculation.

### Improve next

1. **Bind every deliverable video to its renderer/source/input hashes.** This is the highest-leverage cross-pilot improvement: it would distinguish current-source defects from stale ignored outputs and make frame comparisons repeatable.
2. **Review renderer handoffs as continuous clips.** In particular, inspect DWB route continuity at 11.4–12.6 s on a provenance-bound render before changing timing or reveal choreography.
3. **Review dense technical labels at native output size.** Use the 1080p source frame and 1× playback; do not infer readability from the resized contact sheet.

No global token change is justified by this audit. A scoped visual edit should follow only after a same-source output confirms a concrete defect.

## Changed files and validation

- Changed file: this report only. No scene, shared kit, design token, trace, timeline, or existing media was edited.
- Solver validation/render: current PyBaMM battery solver returned PASS with 361 samples and full requested duration; one current-source Blender still rendered and its asset validation passed.
- DWB diagnostic: current source B04 rendered at 1920×1080/30; the cost-panel frame remained pixel-identical with and without the temporary explicit removal (`mean pixel difference = 0`). The no-op source edit was reverted.
- Contact sheets and generated stills: inspected visually. They remain local under `/tmp` and are not committed.
- Full suite, all-scene style check, complete video decode, 1080p final render, and audio review were not repeated because no source changed and this is a comparative audit. Do not treat them as PASS for this work.
- `git diff --check`: run before commit.

## Final QA status

- P0/P1 visual blocker: none established from reviewed frames.
- Confirmed current-source title clipping: none; the suspected Battery issue did not reproduce.
- P2 follow-up: historical DWB cost-table crowding and handoff route gap need confirmation against a provenance-bound current render.
- Motion, audio/caption synchronization, full-speed viewing of all pilot videos, Battery mixed playback, and learner comprehension: **INCOMPLETE / NOT REVIEWED**.
- Current overall visual quality: **7.3/10 snapshot audit**, not approved as a production-wide final visual acceptance.
