# V10 RAG mechanism PoC

This is a 34-second trace-driven RAG replay. Its only required data input is the versioned `data/ai_trace.json`; it does not need `pilots/07_naive_rag/` to validate or render a silent video. Manim shows the actual source character ranges and chunk overlap, continuous query/chunk identity through embedding and score-ordered retrieval, and selected chunks moving into context.

## Rebuild

From the repository root:

```bash
uv run python scripts/build_ai_rag_trace.py
uv run python scripts/validate_ai_trace.py pilots/v10_rag_poc/data/ai_trace.json
uv run python scripts/check_scene_style.py pilots/v10_rag_poc/rag_mechanism_scene.py
uv run python pilots/v10_rag_poc/build_video.py final --silent
uv run python scripts/validate_delivery.py pilots/v10_rag_poc/output/rag_mechanism_poc.mp4 --fps 30 --full-decode
```

To include the Three.js embedding/similarity segment in the 8.5–17.0 second beat, install its pilot-local packages and browser once, then render:

```bash
cd pilots/v10_threejs_rag
npm ci
npx playwright install chromium --only-shell
cd ../..
uv run python pilots/v10_rag_poc/build_video.py final --with-threejs --silent
```

The Three.js 8-second clip occupies the existing 8.5-second beat; its last captured frame holds for 0.5 seconds. `output/embedding_segment_manifest.json` records the exact V9 presentation interval, trace/query/chunk IDs, original ranking/scores and trace hash. The trace contains no per-operation execution timestamps, so no inference timestamps or model latency are invented. The adapter recomputes only the display PCA from stored vectors; retrieval uses the stored 384-dimensional squared-L2 values and ranks without modification.

Narration and captions are optional. Without the former Naive RAG episode files the build prints an `AUDIO ADAPTER` message and leaves a video-only MP4. To reuse already approved voice explicitly, provide all three: `--audio-source <video-with-audio> --audio-manifest <timed-manifest.json> --caption-timing <measured-cues.json>`. `--silent` always skips that adapter. No TTS request is made.

## Before/after evidence

| Measure | Before (`4505be9`) | After | Method / boundary |
|---|---:|---:|---|
| Explicit `BeatClock.wait` total | 27.6 s | 4.65 s | Sum of scene wait calls; remaining beat time is spent on actual transitions. |
| Near-static frame-pair ratio | 70.1% | 56.7% | 2 fps samples, downscaled to 320px wide, grayscale mean absolute pixel change `<0.5/255`; 67 adjacent pairs each. This is a motion proxy, not a perceptual score. |
| Mean adjacent-frame change | 1.076/255 | 0.921/255 | Same frame sample and difference method. Overall screen similarity still remains high because explanatory holds/background are retained. |
| Full render wall time | 28.67 s | 37.53 s | Same local host. New run renders the denser Manim scene and integrates the already fresh 8-second Three.js segment; before run also composed optional narration/captions, after run was silent. Not a like-for-like production benchmark. |
| Output | 34.0 s, 1080p30 | 34.0 s, 1080p30 | H.264; after is intentionally video-only for clone-safe replay. |

The final frame sweep shows actual source ranges and the observed C05/C06 overlap, chunk embeddings followed by the query, progressive 384D squared-L2 values in recorded rank order, and selected chunks entering context. IDs and scores were compared directly with `ai_trace.json`; the integrated segment manifest carries the trace hash and `[8.5, 17.0)` presentation interval. The source trace was not regenerated or edited.

The MP4 was fully decoded and representative frames across the 34-second timeline were inspected. A normal-speed human watch/listen and learner-comprehension check were not performed; this silent render has no educational-review PASS claim.

## Data boundaries and provenance

The committed trace retains source-run provenance and SHA-256, source data hash, model names and retrieval index. The source run contains only LLM answer-generation timing; that measured duration is retained. Chunking, embedding and retrieval execution durations are not present and remain null. Scene duration is presentation time and is not model latency. The optional adapter can rebuild from an explicitly supplied `--source-run`; by default `build_ai_rag_trace.py` only validates and reuses the committed trace.

When the optional audio files are supplied, the selected voice windows and measured sentence captions are composed into the 34-second track. The default silent command remains reproducible from the checked-in trace alone.

This is a visualization replay of a saved real prior execution, not a newly executed end-to-end RAG run. Automated video checks establish dimensions, frame rate and full decode; sampled-frame review does not certify normal-speed viewing/listening or learner comprehension.

## Files

- `data/ai_trace.json`: adapted and validated trace.
- `rag_mechanism_scene.py`: trace-driven scene.
- `build_video.py`: preview/final rendering and approved-source audio assembly.
- `output/rag_mechanism_poc.mp4`: final 1080p30 video.
- `output/rag_mechanism_poc_preview.mp4`: 540p30 preview.
- `output/caption_timing.json`, `output/subtitles.ko.srt`: selected caption cues.
