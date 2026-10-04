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

1. Consume the compact Director beat sheet or `templates/video_manifest.yaml`; when present, consume the stable narration manifest rather than re-planning narration/SFX/BGM.
2. Inspect Resolve/project/timeline/media read-only.
3. Create or duplicate a working timeline such as `<topic>_EDIT_V01`.
4. Import only required assets and organize them minimally.
5. Assemble picture according to beat IDs and intended timing.
6. Place narration first; retime visual beats to narration where possible, not the reverse.
7. Add subtitles, then sparse SFX/BGM.
8. Export a compact preview or representative frames and route actual output to `render-reviewer-skill`.
9. Apply only Resolve/audio-owned blocker/high patches; create a new timeline version before destructive cleanup.
10. Validate render settings and export.

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
