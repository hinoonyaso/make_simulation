# Codex orchestration — Robotics / AI Visual Video V8

Use `ROUTING.md` first. Do not preload all skills or references.

## Delegate by stage
When Codex multi-agent roles are available, use the matching custom role from `.codex/config.toml`:
- story/beat sheet -> `director`
- narration timing/audio cues -> `narration`
- normal Manim -> `manim`
- normal Blender -> `blender`
- reusable asset lookup/register -> `asset_library`
- preview QA -> `reviewer`
- Resolve finishing -> `resolve`
- explicit YouTube packaging/publishing -> `youtube`
- optional paper/benchmark research -> `paper_research`

## Astra escalation
Do not use Astra by default. Escalate only when `MODEL_ROUTING.yaml` triggers it:
- Manim -> `manim_hero`
- Blender -> `blender_hero`
- review -> `reviewer_deep`
- paper research -> `paper_deep`

Astra is a precision escalation, not a default worker.

## Context discipline
1. Pass compact artifacts (beat sheet, narration manifest, asset IDs, review patch, research handoff) instead of conversation history.
2. A worker reads its own `SKILL.md` plus at most one active reference/topic unless a blocker requires more.
3. Do not spawn duplicate workers for the same stage.
4. Manim and Blender may run in parallel only after the beat sheet and narration timing are locked and their outputs are independent.
5. Reviewer runs only after an actual preview exists. Default one review pass; maximum two revision passes unless a blocker remains.
6. Resolve runs only after assets are approved. YouTube runs only when explicitly requested.
7. Preserve evidence labels downstream; never turn illustration/toy simulation into measured or research evidence.

## Fallback
If a custom role/model is unavailable, continue with the nearest non-escalation role and report the fallback once. Do not stop the production solely because Astra is unavailable.
