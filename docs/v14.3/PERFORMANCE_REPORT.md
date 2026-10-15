# Performance Report

## Target work reduction

For the 24-second, 30 fps battery lesson, the plan requests one Blender still plus 180 Blender animation frames: **181 rendered Blender images instead of 720**. The BAT01 still is held for 180 output frames by FFmpeg; it is not counted as 180 Blender renders. Manim continues to render its existing timeline content, and the final video remains 720 frames at 960×540 for preview.

The historical GitHub Actions measurement (Blender 4,430.12 s; Manim 10.62 s) came from a different CI environment and is context only. It is not used as a local baseline or speedup estimate.

## Measured result

An actual local sparse preview completed with Blender 5.2.1 LTS / `BLENDER_EEVEE` and Manim 0.21.0. The measured production stages were:

| Stage | Time |
|---|---:|
| Blender still + animation | 26.70 s |
| Manim | 8.36 s |
| Encode Blender animation segment | 0.41 s |
| FFmpeg composition | 1.31 s |

Blender produced exactly 181 images: BAT01 frame 1 once, plus BAT03 frames 361–540 (180 frames). The final file is `/tmp/v14.3-sparse-actual/v143-blender-final/preview.mp4`, 960×540, 30 fps, 720 frames, 24 seconds, H.264, full decode PASS. This is a measured sparse run; no same-host legacy full-render timing is available, so no elapsed-time speedup is claimed. The 181 vs 720 image-count comparison is a 74.9% reduction in requested Blender images, not a measured runtime reduction.

The sandboxed Windows Blender launch initially failed with `UtilBindVsockAnyPort:309: socket failed 1`; the same installed Blender 5.2.1 executable launched under the approved out-of-sandbox local invocation. GPU use remains unverified because OS-level NVML access is blocked.

## Final acceptance status

On review HEAD `417f592`, the existing video SHA-256 remains `1d5091cd4b94d2c01f1612e0cdbf5d95eafb9ed4397d775f345401ae4d1f933a`. The 24-second 1× playback command completed, and technical media validation and provenance checks pass. Full-motion visual acceptance remains blocked because this review session cannot observe the live playback; 0.5-second samples across all beats and boundary frames were inspected instead. No motion-quality claim is inferred from frame count or decode alone. GPU use remains unverified and does not block the CPU-compatible sparse rendering feature.

Latest Actions for this commit are all successful: [Battery #25](https://github.com/hinoonyaso/make_simulation/actions/runs/38140377012), [Education #44](https://github.com/hinoonyaso/make_simulation/actions/runs/38140377004), and [AI Trace #104](https://github.com/hinoonyaso/make_simulation/actions/runs/38140377014). No Blender Actions job ran.
