# V10 RAG mechanism renderer

The RAG renderer replays any supported `ai-mechanism-trace/v1` with dynamic chunk IDs/counts, actual source ranges and overlaps, trace-dimension vectors, score metric/direction, Top-K and context content. The checked-in `data/ai_trace.json` remains a clone-safe replay input. New UTF-8 documents/questions can be processed locally by the supported lexical TF-IDF runner. That mode uses cosine similarity and context assembly only: it has no semantic embedding model and does not generate an answer.

## Rebuild

From the repository root:

```bash
uv run python scripts/validate_ai_trace.py pilots/v10_rag_poc/data/ai_trace.json
uv run python core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py pilots/v10_rag_poc/visual_manifest.json
uv run python scripts/check_scene_style.py pilots/v10_rag_poc/rag_mechanism_scene.py
uv run python scripts/produce_ai_video.py --topic rag --trace pilots/v10_rag_poc/data/ai_trace.json --render auto --silent
```

The production CLI validates the trace and single V9 beat manifest, makes a preview, runs a full-decode technical check and then renders the 1080p final. It writes a per-trace folder under `output/runs/` with `ai_trace.json`, `visual_manifest.json`, preview/final media, `renderer_selection.json`, and `production_report.json`. Use `--render manim` for a fully local fallback. Optional `--durations CHUNK VECTOR RETRIEVAL CONTEXT` values are recorded in that same manifest.

To execute a new document and question locally:

```bash
uv run python scripts/produce_ai_video.py --topic rag \
  --document tests/fixtures/rag_long_document_ko.txt \
  --question '질문과 가까운 청크를 실제 점수로 고르는 과정은?' \
  --chunk-size 48 --overlap 12 --top-k 5 --render auto --silent
```

The local execution is `character windows → TF-IDF lexical features → cosine similarity → context`. It is intentionally not labeled semantic RAG and has no generated answer. Top-K values 1, 3 and 5 are covered by the data tests.

For an explicit, standalone Three.js render with a new trace, install the pilot-local packages/browser once. The main production CLI chooses this segment automatically when the renderer can run:

```bash
cd pilots/v10_threejs_rag
npm ci
npx playwright install chromium --only-shell
cd ../..
uv run python pilots/v10_rag_poc/build_video.py final --trace <trace.json> \
  --manifest <visual_manifest.json> --auto-threejs --silent
```

The segment is mapped to the manifest's vector beat duration and is never treated as inference latency. `embedding_segment_manifest.json` records the trace/query/chunk IDs, metric/direction, scores/ranks, Top-K and trace hash. The PCA/SVD coordinates are display only; ranking comes from the recorded original feature/vector dimensions.

Narration and captions are optional. The default production path is video-only and does not send narration to any TTS service. To reuse measured audio explicitly, provide the complete `--audio-source`, `--audio-manifest` and `--caption-timing` triple. Audio duration must match the V9 manifest timeline. `--silent` always skips audio composition.

## Earlier replay motion evidence (commit `78a090a`)

| Measure | Before (`4505be9`) | After | Method / boundary |
|---|---:|---:|---|
| Explicit `BeatClock.wait` total | 27.6 s | 4.65 s | Sum of scene wait calls; remaining beat time is spent on actual transitions. |
| Near-static frame-pair ratio | 70.1% | 56.7% | 2 fps samples, downscaled to 320px wide, grayscale mean absolute pixel change `<0.5/255`; 67 adjacent pairs each. This is a motion proxy, not a perceptual score. |
| Mean adjacent-frame change | 1.076/255 | 0.921/255 | Same frame sample and difference method. Overall screen similarity still remains high because explanatory holds/background are retained. |
| Full render wall time | 28.67 s | 37.53 s | Same local host. New run renders the denser Manim scene and integrates the already fresh 8-second Three.js segment; before run also composed optional narration/captions, after run was silent. Not a like-for-like production benchmark. |
| Output | 34.0 s, 1080p30 | 34.0 s, 1080p30 | H.264; after is intentionally video-only for clone-safe replay. |

Those measurements describe the saved-vector replay completed at commit `78a090a`. They are not measurements of the generic renderer below.

## Data boundaries and provenance

The saved E5/FAISS trace retains source-run provenance and SHA-256, model names and the recorded full-dimensional squared-L2 retrieval. Its missing operation times remain null. The new-document runner records its actual local retrieval loop and identifies its lexical TF-IDF method. Neither trace uses presentation duration as inference latency. The lexical trace contains a source-document path and content hash; it does not include an answer-model output.

The latest local fixture execution uses a different Korean document and query and produces 27 overlapping character chunks, 214-dimensional TF-IDF features, cosine scores and Top-5 context. This evidence validates a fresh local lexical run plus its Manim/Three.js presentation; it does not validate semantic retrieval or a generative answer. Preview frame review can expose crop/readability issues, but no normal-speed narration/listening or learner-comprehension claim is made for a silent video.

## Files

- `data/ai_trace.json`: adapted and validated trace.
- `rag_mechanism_scene.py`: trace-driven scene.
- `build_video.py`: preview/final rendering and approved-source audio assembly.
- `visual_manifest.json`: default V9 beat contract; production runs write a trace-adjusted copy beside their artifacts.
- `output/runs/<run-id>/`: isolated per-input trace, manifest, renderer selection, segment mapping, preview/final and production report.
