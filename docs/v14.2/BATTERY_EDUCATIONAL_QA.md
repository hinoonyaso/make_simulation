# Battery Educational QA

## Verified

| Check | Result |
|---|---|
| Normal PyBaMM SPM run | PASS — PyBaMM 26.10.0.0, CPU IDAKLUSolver, 361 samples, 0–1800 s at 5 s interval |
| Normal result validation | PASS — SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25` |
| Early voltage cutoff | PASS — requested 7200 s; event at 3606.549305848102 s; 62 samples; result SHA-256 `23ca1050317fe899e43ce0c5ebbdf42dab3c5438d1d3e7dd1cb8676bffcb5b3e` |
| Result metadata regression | PASS — row count, final time, interval, termination/event metadata, units and persisted hashes are checked; no extrapolation or SOC clamping |
| Blender 5.2.1 asset load | PASS in [Battery Actions run 38129252744](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252744) — asset `edu.mechanical_primitives.v1`, actual required battery objects and same solver run recorded |
| Battery still | PASS — artifact `battery_still.png` produced by the same run; inspected for camera framing and object visibility |
| 6 s Manim solver smoke | PASS — 960×540, H.264, 30 fps, 180 frames, full decode |
| 24 s mixed CI preview | PASS for corrected source `f6dd301938fe6aa29986b5f1d2210d0d54a40b13` — [run 38129252744](https://github.com/hinoonyaso/make_simulation/actions/runs/38129252744), 960×540, H.264, 30 fps, 720 frames, silent, full decode |
| Corrected Manim scene | PASS locally and in CI — clears state during Blender beats, recreates the title per Manim beat, and holds the final frame |
| Unit regression | PASS — 207 tests |
| Python compileall | PASS |
| Asset registry/catalog validation | PASS — 39 registry entries; six catalog/generated assets |
| Scene style and whitespace | PASS — both battery scene files; `git diff --check` |
| TTS / 1080p | NOT RUN — outside this task's scope |

The corrected CI preview SHA-256 is `d1d0fdab89e3506986a602224faaacff1737f92cf9e9ff2a89d81ebb0eff0e4a`. The first artifact had chart objects underneath the later summary text; frame review of the corrected artifact confirms the stale graph is gone. The final encoded frame contains the model limits summary. The 15 sampled frames span all renderer boundaries; the video has 716 unique frame hashes out of 720, confirming it is not a static image sequence.

## Local Blender environment

This WSL session cannot launch the installed Windows Blender or `cmd.exe` (`UtilBindVsockAnyPort:309: socket failed 1`), and its Linux Python does not provide `bpy`. No local Blender rerender is claimed. Corrected-source run 38129252744 is direct evidence of Blender 5.2.1 asset loading, the still and mixed render.

## Interpretation boundary

The 18650 mesh is a CC0 educational concept asset, not Chen2020 geometry. The displayed bar is estimated SOC from Coulomb Counting over model discharge capacity, not measured SOC or BMS output. The lesson does not show electrolyte concentration, temperature, electric fields or current density. This is a validated SPM model computation, not experimental evidence.
