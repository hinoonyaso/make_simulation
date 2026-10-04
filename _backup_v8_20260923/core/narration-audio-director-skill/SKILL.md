---
name: narration-audio-director-skill
version: 1.0
description: Low-token narration and audio direction for high-quality robotics/AI explainers. Converts a compact beat sheet into speakable narration timing and sparse audio cues that Manim, Blender, and Resolve can share.
---

# Narration & Audio Director

Use for **narrated educational videos** after the Director beat sheet and before detailed animation timing. Skip for silent demos or clips whose narration is already locked.

## Goal

Create one timing source of truth so speech, animation and edit rhythm agree:
`beat sheet -> narration manifest -> Manim/Blender timing -> Resolve mix`.

Do not imitate a creator's exact voice, catchphrases, cadence, or persona. Optimize for clarity, curiosity and natural spoken Korean/English as requested.

## Core rules

- One beat = one spoken idea + one dominant visual event.
- Write for speech, not essays: concrete subject, short clauses, minimal parentheticals.
- Explain visible intuition before dense terminology when possible.
- Put pauses where the viewer must inspect geometry/equations; do not fill every second with speech.
- Highlight at most one key phrase per beat.
- SFX/BGM are cues, not decorations. Narration remains dominant.
- Do not invent measurements, paper claims, transcripts, or pronunciation certainty.

## Minimal workflow

1. Consume the compact beat sheet only.
2. Draft narration by beat; preserve terminology, variables, units and evidence mode.
3. Estimate speaking duration and add intentional pause budget.
4. Attach exact visual cue intent: what should happen on the emphasized phrase or after the pause.
5. Add SFX only for meaningful state changes/reveals/errors; set BGM state `off | low | normal`.
6. Save `templates/narration_manifest.json` shape and validate with `scripts/validate_manifest.py` when used as an automation handoff.
7. After final voice is recorded/generated, allow small animation retiming; do not rewrite the whole story merely to fit an arbitrary duration.

## Handoff fields

Per beat keep only:
`id | text | target_seconds | pause_after | emphasis | visual_cue | sfx | bgm`

Manim/Blender consume timing + visual cue. Resolve consumes final audio path plus SFX/BGM intent. Later stages should not reread this skill once the manifest is stable.

## On-demand references — do not preload all

- spoken writing/clarity -> `references/writing.md`
- pacing/synchronization -> `references/timing.md`
- SFX/BGM/mix intent -> `references/audio-cues.md`
