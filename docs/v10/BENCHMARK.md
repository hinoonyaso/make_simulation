# V10 benchmark and cost observations

## Reproducible sample

| Item | Observed result |
|---|---:|
| Output | 34.00 sec, 1920×1080, 30 fps, H.264 + AAC |
| MP4 size | 2,391,858 bytes (final readability rerender) |
| Captions | 11 sentence-level cues reused from the source pilot |
| Trace operations / intermediate values | 6 / 34 |
| Source embedding | multilingual E5, 384 dimensions, recorded in source run |
| Search | FAISS IndexFlatL2, recorded squared-L2 ranking |
| Source model generation time | 16.6247 sec for answer generation, from recorded run |
| Reused assets | 1 prior local RAG run, existing narration/caption excerpts; no external asset downloads or TTS calls |
| Newly registered assets | 0 |
| Cache result | Asset Factory unit test: injected conversion called once for two identical requests; cache hit and invalidation verified |

## Measurement boundaries

The source run does not record chunking, embedding or retrieval wall-clock durations; these are null in the trace. The 16.6247 sec generation time is a recorded model execution measurement, not video duration. Renderer and composition stage times were not separately instrumented, so no speedup or production-cost reduction is claimed. Codex token usage and dollar cost were not observed. MP4 file size is an observed artifact property, not a cost metric.

The Asset Factory cache test uses a deterministic test converter, not a real URDF-to-GLB conversion. It proves cache mechanics only; it does not establish semantic preservation or Blender compatibility.

## Next useful benchmark

Instrument separate render-stage wall times and cache hit/miss counts for a baseline and repeated render with one controlled change at a time. For simulation comparisons, use identical model, solver settings, timestep and initial state. For Three.js/Remotion, compare only after a working local capture path can render the same trace at the same output specification.
