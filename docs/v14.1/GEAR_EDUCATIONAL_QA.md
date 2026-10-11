# Gear Educational QA

## Intended explanation

1. Show the 20T input and 40T output as the same persistent physical objects.
2. Rotate the input one turn and the output half a turn in the opposite direction while holding both centers fixed.
3. Use Manim's common pitch point to show equal ideal tangent velocity. Since the contact radii point in opposite directions from the two centers, equal tangent motion requires angular velocities with opposite signs.
4. Substitute the tracked tooth counts: `ω₂/ω₁ = −Z₁/Z₂ = −20/40 = −0.5`.
5. State that this is ideal external-gear kinematics; the polygon mesh is non-involute and no contact dynamics are solved.

## Numerical and geometry contract

- Source: `edu.spur_gears_20_40.v1`, tracked `.blend` plus JSON sidecar and catalog record.
- Tooth counts: 20 and 40; module: 0.002 m.
- Pitch radii: 0.020 m and 0.040 m.
- Expected axis centers: `(-0.030, 0, 0)` m and `(0.030, 0, 0)` m.
- Center distance: 0.060 m.
- Ideal angular velocity ratio: `−0.5`; one input turn maps to minus one-half output turn.
- Pivot origin tolerance: 1 mm on the gear mesh bounds center; hub concentricity is checked in XY.
- Gear mesh may visually intersect because its stylized addendum/tooth form is not an involute conjugate profile. This must be inspected in the actual animation and described as an educational shape, not contact proof.

## QA gates

| Check | Evidence required | Current interpretation |
|---|---|---|
| Lesson plan | 7 beats, 80 s, 30 fps, 2,400 frames, mixed `B`/`M` modes | Plan validation only |
| Kinematics | Unit tests for ratio, turns, timeline boundary continuity | Does not validate Blender motion |
| Asset import | Blender `asset_load_report.json`, matching SHA and four loaded objects | PASS; Blender 5.2.1, actual tracked `.blend` loaded, source unchanged |
| Pivot and hub | Measured Blender bounds/origins and fixed centers during rotation | PASS; 18 sampled frames, max centroid error `3.06e-8 m`, 1 mm tolerance |
| Render | 960×540 H.264, 30 fps, 2,400 frames | PASS; 80.0-second mixed preview and full decode |
| Captions | VTT/SRT and burn-in from shared cues | PASS; 16 timed cues burned into silent preview; no narration to listen to |
| Playback review | Normal-speed motion and visual clarity | Partial; representative Blender and Manim transition frames inspected. Full-length normal-speed review and automated black/freeze analysis remain pending. |

No TTS, Whisper, 1080p master, contact solver, or force/stress result is included in this V14.1 scope. The preview is at `pilots/v14_education/output/gear-v14.1-final-fixed/preview.mp4`; delivery validation reports 960×540, 30 fps, 2,400 frames, 80.0 seconds, and full decode PASS.

## Compatibility regression checks

- Bearing Blender retains its `--manifest` and `--timeline` interface; it does not need the gear-specific context argument or load report. Local compatibility validation invokes the actual Blender scene without `--context`.
- Spur gears declares the context and strict load-report requirements in the renderer registry. Regression tests verify the expected asset ID/hash, objects, pivots and fixed-center evidence, and prevent provenance from claiming an import when the report is missing.
- The ratio-only smoke uses ordinary Manim text for formula glyphs, avoiding `MathTex` and a system LaTeX dependency. CI renders and decodes the 5-second, 150-frame smoke.
