# TEB 1080p Production Acceptance

## Result

**Human review: PASS.** The user confirmed they watched the finished video and described it as good. This records the user's direct review, rather than inferring playback from extracted frames or technical media checks.

## Reviewed delivery

- Local artifact: `pilots/01_teb_reference/output/pilot_teb_reference.mp4` (ignored by Git; not included in this PR)
- SHA-256: `b452c6bbe004d596fe45209e75df1d4ed3ef95a118ccd58ba3c392717ad7d0d9`
- Format: H.264, 1920×1080, 30 fps, 71.20 seconds; Korean AAC narration and embedded Korean captions
- Production source commit: `239b5b488faf7c58eed2f1d37291e423b1dd6b1d`
- Base: `main` at `69854cf10b4f73e4e1c2108ed8d00ba4cd726cc1`

The user confirmed direct viewing after the final caption-safe-area adjustment and full rerender. Their review was positive. The review applies to the exact artifact hash above.

## Technical acceptance evidence

The local production report records passing trace regeneration and validation, Blender and Manim scene style checks, required-media manifest validation, seven-segment staging, 1080p30 delivery validation with required audio and caption timing, and full decode of all 2,136 frames. It also records no detected black interval of 0.1 seconds or longer. These are local checks; they do not imply GitHub Actions success.

The renderer change reserves additional camera space for sentence captions in the Manim shot. The output video and production report are local ignored artifacts, so reviewers must use the hash and metadata above to identify the reviewed render.

## Release state

- Human video review: PASS (user-confirmed)
- Local technical production checks: PASS (see ignored `pilots/01_teb_reference/output/production_report.json`)
- GitHub Actions for this production branch: not yet run through a pull request
- PR #11: separate cross-pilot visual QA documentation; unrelated to this TEB production change
- Merge: not performed
