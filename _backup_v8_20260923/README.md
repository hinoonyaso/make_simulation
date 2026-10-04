# Robotics / AI Visual Video V7 Bundle

High-quality, low-context production stack for robotics/AI educational videos.

## Default pipeline

`Visual Director -> Narration & Audio Director -> Manim and/or Blender -> Preview -> Render Reviewer -> targeted revision -> DaVinci Resolve -> YouTube Publishing (optional)`

`Visual Asset Library` is a side service used only to resolve or register reusable Manim/Blender components. `Paper Research` remains opt-in.

## Core skills

- `core/robotics-ai-visual-director-skill` — question, causal story, beat sheet, tool routing
- `core/narration-audio-director-skill` — spoken script timing + visual/audio cue manifest
- `core/manim-robotics-education-skill` — equations, algorithms, 2D reasoning
- `core/blender-robotics-simulation-skill` — 3D spatial/robotics explanation
- `core/visual-asset-library-skill` — targeted reuse/versioning registry for shared visual assets
- `core/render-reviewer-skill` — evidence-based QA on actual preview pixels/motion; precise patch routing
- `core/davinci-resolve-robotics-postproduction-skill` — timeline assembly, audio/subtitles, final finishing through Resolve MCP
- `core/youtube-education-publishing-skill` — package/preflight and explicitly authorized publishing

## Optional module

- `optional/physical-ai-paper-research-skill` — primary-source paper/benchmark research with compact evidence handoff

Use Paper Research only when a paper, benchmark, current SOTA comparison, or attributed quantitative research claim is central. Ordinary TF2, FK/IK, Depth->XYZ, basic SLAM/Nav2, ROS2, and general quantization explainers start at Director.

## Token policy

**Never preload the bundle.**

1. Start at `ROUTING.md`, then load only the active skill.
2. Narration Director consumes the compact beat sheet and emits one stable manifest; later stages consume the manifest, not the skill.
3. Manim/Blender load only the active topic/reference. Query Asset Library by exact ID/filter instead of reading the registry wholesale.
4. Reviewer loads only after an actual preview exists. Default one pass; maximum two revision passes unless a blocker remains or the user asks for more.
5. Resolve loads only after assets exist; low-level API knowledge stays in the installed MCP.
6. YouTube loads only when packaging/publishing is requested.
7. Optional Paper Research loads only under the activation rules above; later stages consume its compact handoff.

## Quality loop

`plan once -> narrate once -> generate -> inspect real render -> patch root causes -> finish`.

Do not substitute more prompting for actual preview inspection. The reviewer should route a defect to the smallest owning stage rather than re-planning the entire episode.

## Evidence policy

Never strengthen evidence while it flows downstream. Keep `illustration`, `toy simulation`, `trace playback`, `model execution`, `local measured`, and `reported research result` distinct through visuals, edit, captions, and publishing metadata.
