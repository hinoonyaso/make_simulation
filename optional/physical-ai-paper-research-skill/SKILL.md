---
name: physical-ai-paper-research-skill
version: 2.0
description: Low-token, evidence-first research for robotics/Physical AI papers. Resolves paper identity/version, extracts mechanisms/equations/experiments, and hands a compact verified brief to Director/Manim/Blender.
---

# Physical AI Paper Research

Research only what the current request needs. Do **not** preload every reference and do not render, train, download large checkpoints, or publish unless another skill explicitly owns that step.

## Route on demand

- find/latest/shortlist -> `references/discovery.md`
- read/compare/verify one or more papers -> `references/deep-read.md`
- convert verified research into a video/experiment brief -> `references/handoff.md`

## Core rules

1. Resolve exact title, authors, year, identifier, revision, code/checkpoint identity before technical claims. Prefer paper/appendix, official project page, author code/model card.
2. Read the mechanism, equations, experiment protocol and limitations—not only abstract/conclusion. Inspect PDF figures visually when layout matters.
3. Keep **training / inference / imagined rollout / online planning / physical execution** distinct. Track important shapes, coordinate frames, units and clocks. Never infer architecture from a model name.
4. Attach central claims to exact source locations. Label evidence as: `source-stated | source-measured | researcher-inference | local-measured | illustrative`.
5. Compare numbers only when task, dataset, embodiment and protocol are compatible. Otherwise explain differences without a ranking.
6. For production, pick one teachable mechanism and one revealing intervention; explicitly choose `paper explanation | toy demo | actual model execution`.
7. State unknowns and missing full text/code honestly. Do not convert plots into invented exact numbers.

## Compact output

Return only the requested artifact. A production handoff should be short enough for the Director to consume without rereading the paper: `identity | viewer question | mechanism | claim ledger | experiment | Manim/Blender mapping | limitations/open issues`.

For “latest,” browse current primary sources and record the search date/scope. Preserve citations and provenance through later narration/description.
