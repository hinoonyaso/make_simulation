# V10 architecture audit

## Scope and baseline

Reviewed the repository's README, AGENTS.md, ROUTING.md, MODEL_ROUTING.yaml, BUNDLE_MANIFEST.json, agent TOML files, relevant Director/Manim/Blender/Reviewer/Resolve skills, shared trace validator, asset registry and assets, pilots/01, pilots/05/revision_14, pilot/07 Naive RAG inputs and renderer scripts. Existing pilot outputs and topic episodes were retained.

The current system is a V9 production pipeline: Director → single-beat visual manifest → validated robotics trace where applicable → Manim (`M`), Blender (`B`) or editor (`E`) → preview/review → final delivery. The manifest and robotics trace validators are established contracts. The routing guidance already emphasizes state changes, shared traces and separate technical/educational QA.

## Findings

- The robotics trace contract is domain-specific. Reusing it for RAG would misstate AI operations and data; V10 therefore adds a separate `ai-mechanism-trace/v1` schema and validator.
- A real local Naive RAG execution record already exists under `pilots/07_naive_rag/data/rag_run.json`. It contains document chunks and offsets, multilingual E5 384-dimensional embeddings, query embedding, FAISS `IndexFlatL2` scores/ranks, PCA display coordinates, assembled context, generated answer and generation time. This enables a truthful adapter and visual PoC without changing the original episode or rerunning external services.
- The current registry can validate listed assets and source hashes but does not provide resolution/conversion caching. A new local adapter adds these operations without changing the registry schema. It requires an injected converter and does not download or convert formats itself.
- Existing assets include URDF and MJCF files, but no MuJoCo Python package or Blender CLI is available in this environment. A MuJoCo physics run and Blender render cannot be demonstrated here.
- Node.js is installed, but Three.js and Remotion are not configured. The 2D RAG question is served by Manim and measured execution data; introducing a separate browser/video toolchain for this slice would add setup without evidence of an educational or cost benefit.
- Build scripts currently have no shared cache/invalidation contract across simulation, trace, scene, audio and final composition. V10's asset cache is a scoped local foundation, not a complete pipeline cache.

## Baseline checks

- Existing asset registry: 33 entries validated successfully.
- Codex agent configs: 10 validated successfully.
- Existing RAG source and video are treated as inputs; this work writes only under `pilots/v10_rag_poc/`, `core/ai-mechanism/`, `core/visual-assets/asset_factory.py`, `scripts/`, `tests/` and `docs/v10/`.

## Preserved contracts

The V9 manifest's single-beat shape, `M/B/E` tool values, robotics trace schema, routing, existing episode files and model routing remain unchanged. AI trace validation is additive. The RAG renderer consumes one validated trace rather than inventing scores or IDs.
