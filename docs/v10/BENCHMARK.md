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


## MuJoCo arm PoC (2026-10)

| Item | Observed result |
|---|---:|
| Engine / model | MuJoCo 3.7.0 / Unitree H1 with hand, fixed pelvis |
| Physics step / duration | 0.002 sec / 2.0 simulated sec |
| Trace | 101 samples, 20 joints, 19 actuators |
| End-effector start-to-end travel | 0.06004 m |
| FK replay max hand-position difference | 0 m at stored precision |
| Repeat-run difference | ≤1e-12 absolute tolerance for qpos and hand position |
| 2 ms vs 1 ms max paired hand-position difference | 0.000106713 m (1 mm tolerance) |
| Self contacts | 3–4 per sampled state; not the teaching claim |
| Render | 9.8 sec, 1920×1080, 30 fps, H.264, video-only, 298,183 bytes |

The controller's target is not treated as the achieved result: peak target error is 0.120 rad at the shoulder and 0.209 rad at the elbow. The fixed pelvis and ideal PD motor law are modeling choices. No added floor, contact lesson, hardware controller, ROS2 runtime or Blender mesh render is claimed. System-level Blender/SoX installation is blocked by the container's `no new privileges` restriction; the existing Manim path produced and decoded the video successfully.

## Three.js 3D RAG PoC (2026-10)

| Item | Observed result |
|---|---:|
| Runtime | Node 22.23.2, Three.js 0.186.1, Playwright 1.64.0, Chromium Headless Shell 156 |
| Input points | 11 recorded E5 chunk vectors + 1 recorded query, all 384D |
| Display | PCA/SVD 3D, first-three component explained variance 0.4865 |
| Browser render | WebGL PASS, 12 points, 29 draw calls; top3 exactly C08 → C11 → C07 |
| MP4 | 8.00 sec, 1920×1080, 30fps, H.264, video-only, 883,804 bytes |
| Decode | `validate_delivery.py --fps 30 --full-decode`: PASS |
| npm audit | 0 vulnerabilities at run time |

The PCA variance describes only the first three components; the projection is lossy. The 3D geometry does not calculate retrieval. Three.js and browser frame-render time were not separately instrumented, so this experiment makes no speed or cost comparison against Manim. Remotion was not added because the fixed composition rendered through Three.js frame capture + FFmpeg without needing a React timeline.
