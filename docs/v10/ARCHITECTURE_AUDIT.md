# V10 architecture audit

## Scope and baseline

Reviewed the repository's README, AGENTS.md, ROUTING.md, MODEL_ROUTING.yaml, BUNDLE_MANIFEST.json, agent TOML files, relevant Director/Manim/Blender/Reviewer/Resolve skills, shared trace validator, asset registry and assets, pilots/01, pilots/05/revision_14, pilot/07 Naive RAG inputs and renderer scripts. Existing pilot outputs and topic episodes were retained.

The current system is a V9 production pipeline: Director → single-beat visual manifest → validated robotics trace where applicable → Manim (`M`), Blender (`B`) or editor (`E`) → preview/review → final delivery. The manifest and robotics trace validators are established contracts. The routing guidance already emphasizes state changes, shared traces and separate technical/educational QA.

## Findings

- The robotics trace contract is domain-specific. Reusing it for RAG would misstate AI operations and data; V10 therefore adds a separate `ai-mechanism-trace/v1` schema and validator.
- A real local Naive RAG execution record already exists under `pilots/07_naive_rag/data/rag_run.json`. It contains document chunks and offsets, multilingual E5 384-dimensional embeddings, query embedding, FAISS `IndexFlatL2` scores/ranks, PCA display coordinates, assembled context, generated answer and generation time. This enables a truthful adapter and visual PoC without changing the original episode or rerunning external services.
- The current registry can validate listed assets and source hashes but does not provide resolution/conversion caching. A new local adapter adds these operations without changing the registry schema. It requires an injected converter and does not download or convert formats itself.
- At the time of the V10 audit, no MuJoCo Python package or Blender CLI was available. The later environment setup added MuJoCo 3.7.0 and passed a headless Unitree H1 MJCF smoke run; Blender CLI remains unavailable.
- At baseline, Node.js was installed but Three.js, Remotion and a browser capture runtime were not configured. The later Phase 4 PoC installed Three.js and a Playwright-managed headless Chromium; Remotion remains deferred after the 3D scene rendered through FFmpeg.
- Build scripts currently have no shared cache/invalidation contract across simulation, trace, scene, audio and final composition. V10's asset cache is a scoped local foundation, not a complete pipeline cache.

## Baseline checks

- Existing asset registry: 33 entries validated successfully.
- Codex agent configs: 10 validated successfully.
- Existing RAG source and video are treated as inputs; this work writes only under `pilots/v10_rag_poc/`, `core/ai-mechanism/`, `core/visual-assets/asset_factory.py`, `scripts/`, `tests/` and `docs/v10/`.

## Preserved contracts

The V9 manifest's single-beat shape, `M/B/E` tool values, robotics trace schema, routing, existing episode files and model routing remain unchanged. AI trace validation is additive. The RAG renderer consumes one validated trace rather than inventing scores or IDs.
