# V14.1 — Blender + Manim Gear Education

V14.1 builds the first mixed-renderer gear lesson on the V14 generic education pipeline. The V14 renderer PR #5 was merged into `main` as `e6c12505f5bd052c9b14bb7f92a0b2ab0bbb9529`; this V14.1 work is a follow-up branch and requires its own review and merge.

## Lesson

`examples/education/spur_gears_full.json` is an 80-second Korean beginner lesson at 30 fps. Blender beats show the tracked 20T/40T asset and its rotation. Manim beats explain equal ideal tangential velocity, opposite angular directions, the `−Z₁/Z₂` ratio, and the boundary between ideal kinematics and physical contact analysis. The original 12-second `spur_gears.json` Manim smoke remains supported.

```bash
uv run python scripts/produce_lesson.py \
  --spec examples/education/spur_gears_full.json --plan-only \
  --output-root /tmp/v14.1-gear-plan --run-id plan

uv run python scripts/produce_lesson.py \
  --spec examples/education/spur_gears_full.json --preview \
  --output-root pilots/v14_education/output/lessons --run-id spur-gears-full
```

The Preview command requires working Manim, Blender, WSL/Windows path translation when applicable, and FFmpeg. It should produce 960×540 H.264 at 30 fps, 2,400 frames, plus VTT/SRT, burned-in captions, QA reports, and the renderer provenance in the run directory. A planned or Manim-only render is not the mixed final preview.

## Asset and pivot handling

The Blender renderer loads `assets/education/generated/spur_gears_20_40.blend` by registry ID `edu.spur_gears_20_40.v1` and checks its SHA-256 against the sidecar/catalog. It requires `Pinion_20T`, `Gear_40T`, `Pinion_Hub`, and `Gear_Hub`. In this generated asset the gear mesh coordinates include their center offsets while object origins may remain at the world origin. The Scene checks the mesh bounds centers against the shared ±30 mm axes, clears the generator's preview animation in memory, and parents each gear/hub to a temporary Empty at its true axis while preserving its world matrix. It does not save the loaded `.blend`.

The generated geometry is CC0-1.0 according to the tracked sidecar. It is stylized polygonal, non-involute teaching geometry, not a commercial CAD part. The resulting lesson does not calculate tooth contact, forces, friction, efficiency, stress, or deformation.

## Shared kinematics and timing

The V14 context builder derives module 2 mm, pitch radii 20/40 mm, center distance 60 mm, and `ω₂/ω₁ = −20/40 = −0.5` from the validated asset metadata. Both renderer tracks consume that context. `core/education/gear_animation.py` maps each Blender beat's input turns to continuous, half-open-timeline-aligned Blender keyframes; both gears and hubs share their axis rotation. Manim retains exact duration for Blender-owned beats, and the generic compositor selects each beat's renderer by manifest tool and phase ID.

After Blender has loaded the asset and validated pivots, it writes `asset_load_report.json` with the actual Blender version, file hashes, object names/origins/bounds, axis locations, and center distance. The common pipeline requires this report before marking `asset_loaded_by_renderer` true.

## Verification status

The pure planning and animation-keyframe checks can run in CI without Blender. Full mixed-renderer acceptance also requires the actual Blender asset load, short rotation test, rendered 80-second Preview, exact frame count, subtitle checks, and FFmpeg full decode. These remain separate status items; tests or plan-only do not imply they passed.
