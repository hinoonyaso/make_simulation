# V10 Three.js RAG embedding space

This trace-driven 3D segment is designed for the embedding/similarity beat in `pilots/v10_rag_poc/`. Its eight seconds show chunk vectors appearing, the recorded query arriving, and the real 384D score order selecting the top three. It can also be opened as a standalone local view.

## Build and verify

Run from this directory:

```bash
npm ci
npx playwright install chromium --only-shell
npm run build:data
npm run test:browser
npm run render:video
```

`build:data` loads `pilots/v10_rag_poc/data/ai_trace.json`, validates it, and computes a deterministic three-component PCA/SVD display projection from 11 stored chunk vectors and the stored query vector. It carries all recorded squared-L2 scores and ranks without recomputing them. `test:browser` checks progressive embedding, query appearance, 384D-to-3D display, WebGL rendering, and exact top-three IDs. `render:video` captures 240 fixed-time browser frames and creates `output/threejs_rag_3d.mp4`.

## Data and visual limits

The projection records the source AI trace hash, method and explained variance (0.4865 for the first three components). The 3D geometry is a lossy display only. Retrieval selection and order are the existing squared-L2 results from original 384D vectors; the scene does not recalculate or infer retrieval from 3D distance. It highlights the recorded top-three sequence and keeps chunk IDs visible.

`uv run python pilots/v10_rag_poc/build_video.py final --with-threejs --silent` inserts the segment at the existing presentation interval 8.5–17.0 seconds and holds its actual final frame for 0.5 seconds. The resulting `embedding_segment_manifest.json` records trace/query/chunk identity, ranks/scores, timeline and the fact that AI execution timestamps are not present in the source. Remotion was not added because the fixed composition is captured with Three.js, Chromium and FFmpeg.

The package pins Three.js 0.186.1 and Playwright 1.64.0 in `package-lock.json`. Chromium is a separate Playwright-managed user cache download, not a repository asset. A silent Manim replay does not require Node, Chromium or this segment; use the core RAG pilot README for that clone-safe route.
