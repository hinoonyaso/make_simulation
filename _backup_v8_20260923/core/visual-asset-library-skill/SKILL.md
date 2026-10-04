---
name: visual-asset-library-skill
version: 1.0
description: Low-token reusable visual asset registry for Manim/Blender robotics explainers. Prevents style drift and duplicate generation by resolving existing procedural/cached assets before creating new ones.
---

# Visual Asset Library

Use only when a Manim/Blender beat needs a **reusable visual component** or when a newly created component should become channel-wide infrastructure. Do not load for one-off simple geometry already covered by the local helper.

## Goal

Improve consistency and reduce code/tokens:
`resolve existing asset -> reuse -> create only if missing -> register compact metadata`.

## Resolve-before-create rule

Before generating a reusable coordinate frame, point, trajectory, camera/sensor primitive, robot abstraction, icon, material/look or overlay:
1. query `assets/registry.json` with `scripts/asset_registry.py`,
2. reuse a compatible asset/recipe when possible,
3. adapt only parameters that are explicitly variable,
4. create a new asset only when no suitable entry exists,
5. register it with provenance/version/license when relevant.

Do not duplicate Manim/Blender helper APIs into prompts. Registry entries may point to procedural helper functions instead of files.

## Asset contract

Every reusable entry needs only what affects correct reuse:
`id | tool | kind | source | version | coordinate/unit assumptions | semantic role | license/provenance if external`.

Prefer procedural assets for simple technical primitives. Prefer cached `.blend`/GLB/SVG/PNG only when geometry/artwork is costly to recreate and reuse is likely.

## Quality rules

- preserve shared semantic colors and naming;
- keep Blender assets readable, abstract and correctly scaled before adding detail;
- keep Manim assets transformation-friendly rather than flattened screenshots;
- no unverified external asset licensing;
- never alter an existing asset in place for one episode—version or instance it.

## On-demand references — do not preload all

- metadata/version/unit conventions -> `references/asset-contract.md`
- cross-video visual identity -> `references/style-consistency.md`
- external asset provenance/license -> `references/provenance.md`

Registry operations use `scripts/asset_registry.py`. Do not read the entire registry into context when a targeted `get`/`list` query is enough.
