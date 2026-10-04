# V8 Routing

Never preload the bundle. Route by the artifact that exists **now**. Codex custom model roles are defined in `.codex/config.toml`; detailed escalation is in `MODEL_ROUTING.yaml`.

## Default narrated educational video
`director -> narration(if needed) -> manim/blender -> preview -> reviewer -> targeted revision -> resolve -> final review -> youtube(optional)`

## Model route
- Director: Sol/high
- Narration: Terra/medium
- Manim normal: Sol/high; hero escalation: Astra/high
- Blender normal: Sol/high; hero escalation: Astra/high
- Asset lookup: Luna/low
- Review normal: Sol/high; deep escalation: Astra/high
- Resolve: Terra/medium
- YouTube: Luna/low
- Paper research optional: Sol/high; deep escalation: Astra/high

## Skip rules
- narration already locked/no narration -> skip Narration
- no reusable/cross-video asset need -> skip Asset Library
- no preview yet -> never load Reviewer
- no publishing request -> skip YouTube
- principle/tutorial -> skip Paper Research

## Optional research
For a paper/benchmark/SOTA/attributed quantitative claim, first use `paper_research`; escalate to `paper_deep` only under `MODEL_ROUTING.yaml`. Pass only the compact research handoff to Director.

## Context rule
At each stage load the active skill plus at most one needed reference/topic. Pass compact manifests/patches, not full conversation history. Do not spawn duplicate workers for the same stage.
