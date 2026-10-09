# V10 Three.js RAG embedding space

This optional Phase 4 PoC makes a real interactive 3D view and an 8-second 1080p30 video from the same validated RAG AI trace as `pilots/v10_rag_poc/`.

## Build and verify

Run from this directory:

```bash
npm ci
npx playwright install chromium --only-shell
npm run build:data
npm run test:browser
npm run render:video
```

`build:data` loads `pilots/v10_rag_poc/data/ai_trace.json`, validates it, and computes a deterministic three-component PCA/SVD projection from the 11 recorded chunk vectors and the recorded query vector. `test:browser` opens the actual page in headless Chromium with software WebGL and checks 12 rendered points, 384D source dimension, 3D display dimension, 29 WebGL draw calls, and selected IDs C08, C11, C07. `render:video` captures 240 fixed-time browser frames and uses FFmpeg to create `output/threejs_rag_3d.mp4`.

## Data and visual limits

The projection records the source AI trace hash, method and explained variance (0.4865 for the first three components). The 3D geometry is a lossy display only. Retrieval selection and order are the existing squared-L2 results from original 384D vectors; the scene does not recalculate or infer retrieval from 3D distance. It highlights the recorded top-three sequence and keeps chunk IDs visible.

This is an 8-second video-only renderer experiment, not a complete narrated RAG episode. The 34-second Manim video remains the main explanation. Remotion was not added: fixed composition/capture works with Three.js + headless Chromium + FFmpeg and no React timeline feature was required in this PoC.

The package pins Three.js 0.186.1 and Playwright 1.64.0 in `package-lock.json`. Chromium is a separate Playwright-managed user cache download, not a repository asset. In a container that blocks Chromium sandbox startup, run the browser commands in a user session that permits headless Chromium; project-system package installation is not required for this PoC.
