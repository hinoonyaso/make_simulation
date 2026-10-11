# Battery Educational QA

## Verified

| Check | Result |
|---|---|
| Normal PyBaMM SPM run | PASS — PyBaMM 26.10.0.0, CPU IDAKLUSolver, 361 samples, 0–1800 s at 5 s interval |
| Normal result validation | PASS — SHA-256 `e29e858dd80f48c969f8d4b51f6ef004c62241175f598c5b7bd965b65fb44b25` |
| Early voltage cutoff | PASS — requested 7200 s; event at 3606.549305848152 s; 62 samples; result SHA-256 `f2631a1c28111bf4e19af646a6c82978990f36e9025480ee107235b22d43c66a` |
| Result metadata regression | PASS — row count, final time, interval, termination/event metadata, units and persisted hashes are checked; no extrapolation or SOC clamping |
| Blender 5.2.1 asset load | PASS in [Battery Actions run 38122266473](https://github.com/hinoonyaso/make_simulation/actions/runs/38122266473) — asset `edu.mechanical_primitives.v1`, actual required battery objects and same solver run recorded |
| Battery still | PASS — artifact `battery_still.png` produced by the same run; inspected for camera framing and object visibility |
| 6 s Manim solver smoke | PASS — 960×540, H.264, 30 fps, 180 frames, full decode |
| 24 s mixed CI preview | PASS for source `02a1a57e01e927c6956aafc82eb30b48d2811f5c` — 960×540, H.264, 30 fps, 720 frames, silent, full decode |
| Corrected Manim scene | PASS locally — removes Manim state during Blender beats and creates a fresh title per Manim beat; the recomposed 24 s candidate passes manifest, delivery and full-decode validation |
| Unit regression | PASS — 207 tests |
| Python compileall | PASS |
| Asset registry/catalog validation | PASS — 39 registry entries; six catalog/generated assets |
| Scene style and whitespace | PASS — both battery scene files; `git diff --check` |
| TTS / 1080p | NOT RUN — outside this task's scope |

The original CI preview SHA-256 is `61dd936667f7d56764519f52dfe4a2b1fbd32d8afc209cd02aa1a8da60972037`. Frame review found that chart objects remained underneath the later summary text. The corrected local recomposition SHA-256 is `05823bffa2d7a939731cc75ab152dace82cab107f4cc86910f185b67cb0f1af8`. The corrected source has not yet had a remote CI run; keep PR #7 Draft until that run passes.

## Local Blender environment

This WSL session cannot launch the installed Windows Blender or `cmd.exe` (`UtilBindVsockAnyPort:309: socket failed 1`), and its Linux Python does not provide `bpy`. Therefore no local Blender rerender is claimed. The remote artifact from run 38122266473 is direct evidence of Blender 5.2.1 asset loading, the still and mixed render on the pre-cleanup source. The corrected local composite reused the verified CI Blender segment and rerendered Manim only.

## Interpretation boundary

The 18650 mesh is a CC0 educational concept asset, not Chen2020 geometry. The displayed bar is estimated SOC from Coulomb Counting over model discharge capacity, not measured SOC or BMS output. The lesson does not show electrolyte concentration, temperature, electric fields or current density. This is a validated SPM model computation, not experimental evidence.
