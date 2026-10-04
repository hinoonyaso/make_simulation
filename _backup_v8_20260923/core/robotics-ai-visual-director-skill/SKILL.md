---
name: robotics-ai-visual-director-skill
description: Direct high-quality robotics/AI educational videos using curiosity-driven storytelling, continuous visual reasoning, and selective Manim/Blender routing with low context use. Paper research is optional and excluded from the default route.
---

# Robotics / AI Visual Director

Paper research is **optional, not default**. Start directly with this Director for principle/tutorial videos. Use `optional/physical-ai-paper-research-skill` only when a specific paper, benchmark, state-of-the-art comparison, or attributed quantitative research claim is central to the episode. If used, consume its compact handoff instead of rereading the source here.

Design the video before implementation. The goal is **deep understanding with minimal visual noise**, not imitation of any creator's exact style.

## Core promise

Every video should answer one sharp question and make the answer feel visually inevitable.

Use three complementary principles:
- **Curiosity first**: begin with a concrete question, paradox, failure, or misconception.
- **Continuous visual reasoning**: keep important objects alive and transform them instead of replacing slides.
- **Evidence compression**: when verified research is intentionally included, explain only the problem, key idea, evidence, and limitation relevant to the story.

## Default structure

`Hook -> Problem -> Intuition -> Mechanism -> Derivation -> Robot consequence -> Evidence/limitations -> Recap`

For short videos, compress stages; do not remove the causal chain.

## Beat rule

One narration beat should usually have:
1. one sentence or idea,
2. one dominant visual change,
3. one attention target.

Prefer `existing object -> transformation -> new meaning` over `fade out -> new slide`.

## Tool routing

Use **Manim** for equations, algorithms, probability, graphs, tensors, state transitions, and symbolic reasoning.
Use **Blender** only when 3D geometry materially changes understanding: camera rays, coordinate frames, depth, robot kinematics, LiDAR, grasp pose, spatial planning.
Use both only when the handoff is meaningful. Default target is roughly `Manim 70–85% / Blender 15–30%`, not a quota.

## Minimal workflow

1. Write the central question in one sentence.
2. Write the misconception or missing intuition in one sentence.
3. Define the persistent visual object(s): e.g. point P, robot pose, ray, trajectory, token.
4. Draft 6–12 beats using `references/storyboard.md` only if needed.
5. Mark each beat `M` (Manim), `B` (Blender), or `E` (editorial/no generated animation).
6. Define one shared visual contract: colors, variable names, units, coordinate frames.
7. Generate only the assets required by those beats.
8. For narrated videos, hand the compact beat sheet to `narration-audio-director-skill`; do not write detailed animation timing twice.
9. Run the director QA before implementation handoff.

## Progressive disclosure

Never show all variables, equations, frames, labels, and diagrams at once. Introduce only the piece needed for the current inference. If a new element appears, it must answer the current question.

## Evidence rules

Never invent measured performance, benchmark values, sensor traces, paper results, or simulation outcomes. Clearly distinguish `illustration`, `toy simulation`, `trace playback`, `model execution`, and `reported paper result`.

## On-demand references — do not preload all

- storyboard/beat design -> `references/storyboard.md`
- verified paper/research section only -> `references/research-compression.md`
- cross-tool continuity -> `references/visual-contract.md`
- final review -> `references/director-qa.md`

## Deliverable contract

Return a compact beat sheet before implementation:
`beat | narration intent | persistent object | visual change | tool | evidence mode`.
Then, for narrated videos, pass that beat sheet once to `narration-audio-director-skill` to create the compact narration manifest. Route implementation to Manim/Blender using only the active beats plus that manifest. After a preview exists, route actual rendered output to `render-reviewer-skill`. Use `visual-asset-library-skill` only for reusable assets; never preload it.
