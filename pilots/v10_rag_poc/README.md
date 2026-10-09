# V10 RAG mechanism PoC

This is a 34-second Manim demonstration built from the recorded local Naive RAG execution in `pilots/07_naive_rag/data/rag_run.json`.

## Rebuild

From the repository root:

```bash
uv run python scripts/build_ai_rag_trace.py
uv run python scripts/validate_ai_trace.py pilots/v10_rag_poc/data/ai_trace.json
uv run python scripts/check_scene_style.py pilots/v10_rag_poc/rag_mechanism_scene.py
uv run python pilots/v10_rag_poc/build_video.py final
uv run python scripts/validate_delivery.py pilots/v10_rag_poc/output/rag_mechanism_poc.mp4 --require-audio --fps 30 --audio-manifest pilots/v10_rag_poc/output/audio_manifest.json --caption-timing pilots/v10_rag_poc/output/caption_timing.json --full-decode
```

The renderer reads `data/ai_trace.json`; it does not calculate new scores. The adapter uses the source run's actual chunks, E5 embeddings (384 dimensions), query vector, saved PCA coordinates, FAISS IndexFlatL2 squared-distance ranking, selected context and answer. It keeps IDs C01…C11 across the sequence and highlights the actual top three: C08, C11, C07. PCA is marked as a lossy display projection; retrieval ranks come from the original vectors. The scene shows excerpts in cards, not the entire source chunks.

## Data boundaries and provenance

The adapter reads the existing run without modifying the source RAG episode. The generated trace stores the source run path and SHA-256, source data hash, model names and retrieval index. The source run contains only LLM answer generation timing; that measured duration is retained. Chunking, embedding and retrieval execution durations are not present and remain null. Scene duration is presentation time and is not model latency.

The narration and sentence captions are excerpts from the existing Naive RAG final video and its measured caption timing. This did not send a new script to a TTS service. Selected audio windows are composed into a 34-second track.

This is an adapter + visualization replay of a saved real prior execution, not a newly executed end-to-end RAG run. The educational quality has only received representative frame inspection; no claim is made about full normal-speed viewing/listening or learner comprehension.

## Files

- `data/ai_trace.json`: adapted and validated trace.
- `rag_mechanism_scene.py`: trace-driven scene.
- `build_video.py`: preview/final rendering and approved-source audio assembly.
- `output/rag_mechanism_poc.mp4`: final 1080p30 video.
- `output/rag_mechanism_poc_preview.mp4`: 540p30 preview.
- `output/caption_timing.json`, `output/subtitles.ko.srt`: selected caption cues.
