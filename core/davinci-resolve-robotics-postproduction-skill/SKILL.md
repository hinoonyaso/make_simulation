---
name: davinci-resolve-robotics-postproduction-skill
version: 1.0
description: Low-token, high-quality DaVinci Resolve post-production for robotics/AI educational videos. Consumes Director/Manim/Blender outputs and uses the connected davinci-resolve MCP for safe timeline assembly, narration, SFX/BGM, subtitles, review, and delivery.
---

# DaVinci Resolve Robotics / AI Post-production

Use this skill only for the **editorial finishing layer** after Director, Manim, and/or Blender assets exist.

Do not duplicate the MCP server's own API documentation. Use the connected `davinci-resolve` MCP in **compound mode** and call only the domain needed for the current task.

## Goal

Turn generated assets into a polished educational video while preserving technical clarity:

`Director beat sheet -> narration manifest -> Manim/Blender assets -> preview review -> Resolve assembly -> final review -> delivery`

## Non-negotiables

- Inspect first; do not edit blindly.
- Never modify the user's only/master timeline. Duplicate or create a clearly named working timeline before destructive edits.
- Prefer reversible operations and dry-run/probe actions when the MCP provides them.
- Keep narration dominant. Music and SFX support understanding; they must not compete with speech.
- Do not add transitions, zooms, motion graphics, or sound merely for decoration.
- Preserve the Director's persistent objects, beat order, semantic colors, terminology, variable names, units, and evidence labels.
- Do not fabricate captions, measurements, paper results, or audio transcripts. Use supplied script/transcript or verified media analysis.
- Keep Resolve MCP in compound/default mode unless a required capability genuinely needs full/granular mode.

## Start-of-session check

Before any edit, use read-only MCP actions to report:
1. Resolve version/edition and connection state.
2. Current project.
3. Current timeline name, resolution, frame rate, duration, and track layout.
4. Relevant media availability and offline/missing-media warnings.

If the bridge is unavailable, stop Resolve mutations and report the connection issue.

## Delivery baseline

- Final timeline/render: **1920x1080 minimum**; prefer 2560x1440 for line/text-heavy YouTube masters when practical.
- Never accidentally deliver a PREVIEW-sized 960x540/720p asset as final.
- Default subtitle style: clean high-contrast text with subtle outline/shadow; avoid opaque colored boxes unless accessibility/contrast requires them.
- Avoid persistent `SCENE`, episode badges, or metadata lower-thirds. Titles belong at the opening or meaningful section boundaries only.

## Default track contract

Use this unless the project already has an intentional layout:

- `V1` main Manim/Blender picture
- `V2` overlays / equations / transparent Blender or Manim elements
- `V3` subtitles / title graphics when appropriate
- `A1` narration / dialogue
- `A2` SFX
- `A3` BGM
- `A4` optional ambience

Do not create unused tracks.

## Editing grammar

- conceptual continuity -> preserve the shot or use a meaningful visual transform in the source asset
- major idea/location/time change -> cut
- viewpoint change already encoded in Manim/Blender -> do not duplicate it with editor zooms
- emphasis -> prefer subtle audio cue or existing semantic highlight, not gratuitous punch-in
- dead time -> tighten only when comprehension is preserved
- explanatory pause -> keep enough time to read equations and inspect geometry

## Audio hierarchy

Priority: `Narration > important SFX > BGM > ambience`.

Default behavior:
- keep narration centered and intelligible;
- reduce BGM under dense explanations;
- use SFX sparingly for state changes, selections, reveals, errors, and key insight moments;
- avoid constant whooshes/clicks;
- do not apply aggressive processing without listening/review evidence.

Read `references/audio.md` only for an audio-heavy pass.

## Minimal workflow

1. Consume the Director `visual_manifest.json` (beats + `audio` + `media`) and stage it with `scripts/stage_segments.py <visual_manifest.json> sequence.json`; it fails if a Manim/Blender beat has no rendered media, or if two beats claim the same media range (set `media_in`/`media_out` when one shot carries several beats). `templates/video_manifest.yaml` holds editor-only settings, never a second copy of beats. Do not re-plan story/narration.
2. Inspect Resolve/project/timeline/media read-only.
3. Create or duplicate a working timeline such as `<topic>_EDIT_V01`.
4. Import only required assets and organize them minimally.
5. Assemble picture according to beat IDs and intended timing.
6. Place narration first; retime visual beats to narration where possible, not the reverse.
7. Add subtitles, then sparse SFX/BGM.
8. If a cross-tool preview has not already been reviewed, export one compact preview for `render-reviewer-skill`; otherwise do not duplicate review.
9. Apply only Resolve/audio-owned blocker/high patches.
10. Validate the export with the bundle gate:
    `scripts/validate_delivery.py <final> --require-audio --fps <fps> --audio-manifest <assets/audio/manifest.json> --caption-timing <output/caption_timing.json> --full-decode`.
    Any FAIL (sub-1080p, fps, duration vs narration end, caption outside its utterance, decode error) blocks delivery.

## MCP routing — load only what is needed

Rely on the installed Resolve MCP's own domain skills/tooling instead of embedding them here:

- session/project inspection -> Resolve session/project tools
- media import/organization -> media-pool domain
- cuts/timeline/clip transforms -> edit/timeline domain
- narration/audio/subtitles -> audio/Fairlight domain
- titles/motion graphics -> Fusion domain, only when actually needed
- final render/QC -> delivery/render domain

Do not preload all Resolve domain skills.

## Review loop

Before final delivery, review representative moments from:
`hook | densest explanation | Manim↔Blender handoff | equation/3D consequence | evidence/result | recap`.

Check:
- immediate attention target,
- no unreadable text,
- no competing motion,
- narration/visual synchronization,
- sufficient equation dwell time,
- SFX/BGM restraint,
- continuity across Manim/Blender/editor,
- no missing/offline assets,
- correct frame rate/resolution.

Use this checklist for a quick editor-local pass. For cross-tool visual/motion judgment, route the actual preview to `render-reviewer-skill`; do not duplicate a full review here. Read `references/review.md` only for Resolve-local diagnostics.

## Deliverable contract

Return a compact edit report, not a transcript of every MCP call:

`timeline version | assets used | major editorial changes | audio/subtitle status | unresolved issues | render status`

Only report measured/verified output properties.

If publishing is the next step, hand off only the selected final render path/version, verified duration/resolution/frame rate, subtitle/thumbnail paths, and unresolved issues to `youtube-education-publishing-skill`; do not upload from this skill.
