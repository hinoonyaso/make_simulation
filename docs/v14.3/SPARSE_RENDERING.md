# Sparse Rendering Contract

`core/education/sparse_render_plan.py` maps the saved shared timeline to ordered, gap-free, overlap-free segments. Timeline ranges are zero-based and half-open. Blender source frames are one-based and inclusive: timeline `[start, end)` maps to Blender `[start + 1, end]`.

The lesson must explicitly set `render_mode: "still"` on a Blender beat before it can use a still image. The allow-listed renderer must also advertise `supports_sparse_stills`. Unmarked Blender beats render as animation; Manim beats remain video. Unsupported modes, renderers, gaps, overlaps, and frame count mismatches fail closed.

The battery smoke lesson declares BAT01 static. Its expected segment plan is:

| Beat | Renderer | Timeline range | Output frames | Blender source |
|---|---|---:|---:|---|
| BAT01 | Blender still | `[0, 180)` | 180 | frame 1 rendered once, held by FFmpeg |
| BAT02 | Manim video | `[180, 360)` | 180 | Manim frames 180–359 |
| BAT03 | Blender animation | `[360, 540)` | 180 | Blender frames 361–540 |
| BAT04 | Manim video | `[540, 720)` | 180 | Manim frames 540–719 |

Blender writes one PNG for BAT01 and the BAT03 PNG sequence in one Blender process, using the same validated PyBaMM run and scene keyframes as the existing full render. FFmpeg encodes BAT03 locally and composes the segments to exactly 720 frames. The still-image hold is recorded as one Blender-rendered image, not 180 Blender frames. Solver result hash, run ID, asset hash, and timeline hash remain in the generated reports.

`legacy_full` remains available for registered renderers. It is never selected as a fallback when `sparse` is unsupported. Existing topics retain their registered `legacy_full` default; the battery renderer advertises and defaults to `sparse`.
