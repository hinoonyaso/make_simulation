# V10 Three.js RAG display

This package renders the recorded query and chunk feature vectors as an optional 3D display for the embedding/similarity beat in `pilots/v10_rag_poc/`. It is trace-driven and accepts variable chunk counts, dimensions, Top-K and presentation duration. It does not use 3D distances to perform retrieval.

## Integrated production

From the repository root, the normal automatic route is:

```bash
uv run python scripts/produce_ai_video.py \
  --topic rag \
  --trace pilots/v10_rag_poc/data/ai_trace.json \
  --render auto --silent
```

The Director CLI validates the trace and V9 manifest, creates a preview, runs technical QA, and then renders the final video. When recorded vectors and the local Node/Playwright/Chromium runtime are available, `auto` inserts this 3D segment into the embedding beat. If the optional runtime fails, it records the reason and uses the Manim visualization. `renderer_selection.json` records the selected path. Use `--render manim` to skip Three.js explicitly.

For standalone development, run from this directory:

```bash
npm ci
npx playwright install chromium --only-shell
npm run build:data
npm run test:browser
npm run render:video
```

The standalone scripts accept `V10_AI_TRACE`, `V10_THREE_PROJECTION`, `V10_THREE_VIDEO`, `V10_THREE_DURATION`, and `V10_THREE_FPS`. The production builder supplies those values from the same trace and V9 manifest used by Manim.

## Data contract and limits

`build_projection.py` validates the AI trace, projects the recorded query/chunk vectors from their original dimension to three display coordinates, and stores the source trace SHA-256. It carries the trace's exact retrieval metric, direction, scores, ranks and selected IDs. `embedding_segment_manifest.json` also records trace/query/chunk IDs and the presentation interval. The segment duration is mapped to the manifest beat; the trace's algorithm execution time is not presented as video time.

The 3D projection is lossy and is only a visual aid. Similarity scores and selection come from the original trace. A TF-IDF lexical run is labeled as lexical features, never as semantic embeddings. Three.js is optional; a silent Manim-only replay needs no Node, browser or network access.

`npm run test:browser` exercises the progressive scene and score identity. `npm run render:video` captures a standalone segment. These local checks do not imply that GitHub Actions ran the browser workflow or that the integrated video was watched at normal speed. Audio review is not applicable to this silent component.
