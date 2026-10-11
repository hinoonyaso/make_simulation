# Battery Educational QA

## Verified

| Check | Result |
|---|---|
| Actual PyBaMM SPM run | PASS — PyBaMM 26.10.0.0, IDAKLUSolver, 0.1183 s local measured execution |
| Output | PASS — 361 samples, 0–1800 s, 5 s requested interval |
| Result validation | PASS — result SHA `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25` |
| Actual PyBaMM cutoff event | PASS — request 7200 s; lower-voltage event at 3606.549305848152 s; 62 samples; result SHA `f2631a1c28111bf4e19af646a6c82978990f36e902548c5b7bd965b65fb44b25` |
| Result metadata regression | PASS — row count, final time, interval, termination/event metadata, units and persisted hashes are checked; event endpoint is not extrapolated or clamped |
| Blender engine compatibility logic | PASS — unit-tested engine discovery/fallback and minimum sample handling; not an actual Blender runtime test |
| Manim using actual solver CSV | PASS — 960×540, H.264, 30 fps, 180 frames, 6 s, full decode |
| V9 manifest trace contract | PASS — `battery_trace.json` revalidates result, config and CSV hashes |
| Unit regression | PASS — 207 tests |
| Python compileall | PASS |
| Asset registry / education asset metadata | PASS — 39 registry entries; 6 catalog models/generated files checked |
| Lesson plan | PASS — 24 s / 720-frame mixed timeline, status `PLANNED` without solver side effects |
| Blender battery asset load | BLOCKED locally — see environment limitation below; official 5.2.1 runtime CI added but not yet executed |
| 24 s Blender + Manim composition | NOT RUN locally — CI job added; no mixed preview is complete until that job succeeds |
| TTS / 1080p | NOT RUN — out of scope |

Manim actual-solver preview path: `/tmp/v14.2-preview-final/battery-manim-final/preview.mp4` (local, untracked). One 2.5-second frame was inspected; chart tick labels do not overlap the Korean voltage-axis label. Full normal-speed audio review does not apply because the preview is silent.

## Blender limitation

Blender 5.2.1 is present at `/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe`. Direct `--version` and `cmd.exe /c ver` both fail in this WSL session with `UtilBindVsockAnyPort:309: socket failed 1`. The Linux Python environment also does not provide `bpy`. Therefore the `.blend` was not opened, the Blender battery scene was not executed, and the mixed 24-second video was not rendered. A successful solver or Manim run is not evidence of Blender success.

This confirms an interop failure before Blender startup in this session; it does not establish that the user's earlier Blender run did not work. The implementation now queries the running Blender's enum identifiers, validates Eevee sample support, and has a `produce_lesson.py --blender-still-frame` path that writes the regular solver-backed context before rendering a PNG. The first CI attempt reached lesson setup but was stopped by the existing guard against using `--manim-only` on Blender-required beats; the test workflow now uses the dedicated still-frame path. The new run must pass before Blender success is claimed.

## Interpretation boundary

The existing 18650 mesh is a CC0 educational concept asset. It is not a geometry-specific model of Chen2020. The displayed bar is estimated SOC calculated by Coulomb Counting from the model discharge-capacity output and nominal capacity; it is not measured state, BMS output, electrode concentration, temperature, electric field or current-density. The run is an engineering model computation, not experimental evidence.
