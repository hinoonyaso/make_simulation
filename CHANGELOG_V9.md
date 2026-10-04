# V9 Source-Informed Lite

- Keeps V8 Lite's low-agent routing and Astra escalation policy.
- Encodes production patterns found in public creator source repositories into original reusable helpers.
- Adds state-transition-first scene design and deterministic beat/trace validation.
- Adds shared trace files so Manim and Blender can consume the same computed data.
- Adds Manim selective-density helpers for dense graphs/attention and continuous state transforms.
- Adds Blender `StateObject`, trace keyframing, reusable `.blend` asset append, and automatic camera framing from world bounds.
- Adds deterministic sequence staging for Resolve handoff.
- Keeps source/provenance notes optional so default context does not grow materially.

## 9.1 contract/gate fixes
- `visual_manifest.json` is the single beat contract (`caption/audio/media` added). Resolve template keeps editor settings only; `stage_segments.py` fails on 0 segments or unrendered Manim/Blender beats.
- Manifest validator requires `trace` for `trace_playback`/`model_execution` and validates referenced traces; trace validator checks schema, units, per-sample keys, numeric types, finiteness.
- `core/narration/prepare_audio.py`: shared TTS/measured-timing/caption stage (promoted from 8 identical topic copies; byte-identical output on topic 09) that writes measured `sec`/`audio` into the manifest.
- `validate_delivery.py`: optional `--fps`, `--audio-manifest`, `--caption-timing`, `--full-decode` (replaces per-topic media checks).
- Reviewer references and `extract_review_frames.py` wired into its SKILL; review report fields aligned.
- `validate_codex_setup.py` also checks documented paths, BUNDLE_MANIFEST entries, and `.claude/skills` links.
- Claude Code: `.claude/skills/` links + `CLAUDE.md`.

## 9.2 quality-first (pilot 01 promoted)
- `pilots/01_teb_reference` is the quality bar: studio Blender + continuous Manim, pixel-aligned handoff, narration-timed beats.
- Blender `studio_utils.py`: studio scene/floor/lights, corridor/drum/goal props, real TurtleBot3 loader (Apache-2.0 mesh, URDF placement), diff-drive wheel spin, glowing band, length-keyed `reveal_trajectory`, top-view/crane camera.
- `animation_utils`: Blender 5 layered-action F-curve access (`fcurves`, `set_interpolation`); old `Action.fcurves` path failed on 5.x.
- `manim_kit`: `world_window`, `turtlebot3_top`, `beat_seconds`, `BeatClock`.
- Beat contract: `min_sec` (silence padding for visuals), `media_in`/`media_out` (several beats per shot); staging rejects duplicate ranges.
- Narration: sentence-level caption cues aligned by Whisper word times (topic 09 output unchanged); delivery gate accepts several cues per utterance.
- `scripts/check_scene_style.py`: fails slide resets, Workbench, sub-24 fps renders.
- Policy: quality first; flagship shots up to 3 targeted review/revision passes.
