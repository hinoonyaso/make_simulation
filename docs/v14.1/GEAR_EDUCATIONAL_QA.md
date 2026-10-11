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
| Asset import | Blender `asset_load_report.json`, matching SHA and four loaded objects | Not established by registry hash alone |
| Pivot and hub | Measured Blender bounds/origins and fixed centers during rotation | Must be checked in Blender output |
| Render | 960×540 H.264, 30 fps, 2,400 frames | Must be probed from the produced MP4 |
| Captions | VTT/SRT and burn-in from shared cues | Technical timing does not prove narration listening |
| Playback review | Normal-speed motion and visual clarity | Not complete until someone watches the full render |

No TTS, Whisper, 1080p master, contact solver, or force/stress result is included in this V14.1 scope.
