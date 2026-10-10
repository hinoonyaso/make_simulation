# V13 Bearing Pilot Educational QA

## Review questions

- Does the opening establish the shaft/housing relative-motion problem?
- Can a beginner identify inner race, outer race, rolling elements and cage?
- Does the comparison make the difference between sliding and rolling contact visible?
- Does the load path read continuously from shaft through inner race, balls and outer race to housing?
- Are rotation direction and part identity stable through disassembly/reassembly?
- Is conceptual geometry clearly distinguished from measured contact or friction results?
- Does narration have enough time to explain one state change per beat?

## Evidence record

### Local preview run: `bearing-v13-preview-r6`

- Rendered from V9 manifest + V12 integer-frame timeline; Blender 5.2.1 and Manim 0.21.0.
- 84.000 s, 2,520 frames, 960×540, 30 fps, H.264; `validate_delivery.py --full-decode` PASS.
- V9 `validate_visual_manifest.py --require-media` PASS.
- Blender render 310.48 s; Manim render 11.09 s.
- Silent preview only. No TTS was requested or generated. VTT sentence captions are present and burned into the preview.
- Sampled frames at 3, 15, 25, 32, 36, 44, 54, 70 and 82 seconds. The comparison and force-path diagrams are legible at sampled sizes; the exploded assembly reads as a structural illustration. The staged reassembly and bearing rotation still need full-motion review at normal speed.
- The orange shaft pointer is weak/partly occluded from this camera angle. Do not claim that a viewer can infer the shaft rotation direction from that marker alone.
- Full normal-speed playback and audio review were not performed. Learner comprehension, retention and learning effect are untested.

Sampled stills do not verify continuity. Do not promote this silent preview to narrated final until normal-speed motion review and audio review are completed.

## Known conceptual limits

The procedural bearing is a single-row deep-groove conceptual assembly. It omits seals, lubricant, preload, tolerances, elastic contact deformation, wear and detailed cage pockets. Idealized ball circulation does not solve no-slip kinematics or bearing forces. The render must not label an animation as a physical simulation result.

## Technical source review

- SKF, [Bearing basics](https://cdn.skfmediahub.skf.com/api/public/0901d196802809de/pdf_preview_medium/0901d196802809de_pdf_preview_medium.pdf), section A.1: verifies the common inner ring, outer ring, rolling elements and cage, and that rolling elements transfer load between rings.
- SKF, [Simulation of dynamic behavior of rolling bearings](https://evolution.skf.com/en/simulation-of-dynamic-behavior-of-rolling-bearings/): distinguishes measured bearing behavior from animation; the V13 pilot has no corresponding force or cage-pocket measurements.
- SKF, [At the boundary between lubrication and wear](https://evolution.skf.com/at-the-boundary-between-lubrication-and-wear-part-1/): notes sliding can be superimposed on rolling in bearing contacts. This supports the script's caveat that friction and slip are not zero.

The script uses these as technical review sources, but the video is still an illustrative teaching model and is not manufacturer design guidance.

## V13.5 local production branch review (2026-10-11)

### Output

- Generated, ignored output: `pilots/v13_education/output/lessons/bearing-v13.5-silent-review-r2/preview.mp4`.
- 84.000 s, 2,520 frames, 960×540, 30 fps, H.264, silent. Blender 5.2.1 render: 319.05 s; Manim 0.21.0 render: 11.55 s.
- `validate_delivery.py --fps 30 --caption-timing ... --timeline ... --full-decode`: PASS; V9 manifest `--require-media`: PASS.
- Manim smoke preview: PASS at 960×540, 30 fps, full decode. It emitted the existing missing-SoX warning; SoX is not needed by this silent route.
- All repository unit tests: 162/162 PASS in the existing project virtual environment. Education-focused module: 14/14 PASS. Python `compileall`: PASS. Asset registry: 39 entries PASS; education asset validation: 39 registry entries, six catalog models, six generated assets checked PASS.
- Scene style: Blender PASS; Manim PASS.

### Changes and frame review

- The Blender rotation beat now uses a camera-space counter-clockwise arc and a contrasting marker attached to the shaft face. The direction cue appears only during the rotation phase. A one-frame Blender 5.2.1 check verified the shared `studio_utils.set_interpolation` helper and saved the expected frame.
- The first full preview review found the component label panel overlapping the bearing. The panel was moved to a narrower right-side area and the complete preview was rerendered as R2. A still check confirmed the labels fit inside the frame without covering the bearing.
- Two render-review passes were performed. The final pass inspected 12, 24, 31, 36, 40, 43, 46, 48, 53, 65, and 77 seconds. No blocker/high issue was found in the inspected frames. The rotation marker and rolling-element arrangement differ across sampled times; the exploded and reassembly poses show vertical separation.
- This is a sampled-frame review, not normal-speed playback. Full-motion rhythm/continuity, audio playback, and novice comprehension remain unreviewed. `review_report.yaml` records this as `INCOMPLETE`, not PASS.

### Delivery boundary

- The user declined Edge TTS script transmission. No external TTS call was made; `audio_qa.json` records the audio step as not run. Consequently, this output is a silent preview only: no `final.mp4`, AAC stream, or 1080p master was produced.
- The captions are sentence-level. `caption_timing.json` is the single timing source for VTT/SRT and burn-in; ASS represents the same cue boundaries rounded to centiseconds while VTT/SRT retain millisecond timestamps. Unit tests check that the burn-in consumes the saved cue list and that the audio mux path does not use `-shortest`.
- The bearing remains a conceptual illustration. No contact, friction, deformation, or load-distribution solver was run; the load arrow is an explanatory overlay, not a computed force result.
- The generated video and reports are ignored local artifacts and are not present in a clean clone. CI was not run for this local review; remote Actions status is recorded separately by the PR.
