# Performance Report

## Target work reduction

For the 24-second, 30 fps battery lesson, the plan requests one Blender still plus 180 Blender animation frames: **181 rendered Blender images instead of 720**. The BAT01 still is held for 180 output frames by FFmpeg; it is not counted as 180 Blender renders. Manim continues to render its existing timeline content, and the final video remains 720 frames at 960×540 for preview.

The historical GitHub Actions measurement (Blender 4,430.12 s; Manim 10.62 s) came from a different CI environment and is context only. It is not used as a local baseline or speedup estimate.

## Measured result

Not measured: the current WSL session cannot launch its mounted Windows Blender 5.2 binary (`UtilBindVsockAnyPort:309: socket failed 1`), and no Linux Blender executable is available on PATH. NVIDIA NVML access is blocked by the operating system. Therefore Blender render time, GPU backend use, sparse end-to-end time, and speedup are **BLOCKED / NOT MEASURED**. FFmpeg fixture composition is verified in the sparse-render tests; it is not a substitute for a real lesson render.
