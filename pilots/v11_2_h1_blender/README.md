# V11.2 H1 Blender trace render

This is a Blender 3D mesh rendering of a validated MuJoCo trace. The H1 poses and graph values come from the existing stored run; joint positions are interpolated between recorded samples at 30 fps. Blender does not step the physics model again. The floor is a render-only studio surface.

## Reproduce

Export the source trace and compiled MuJoCo geom transforms on the Linux/WSL side:

```bash
uv run python pilots/v11_2_h1_blender/export_trace.py --out /tmp/v112_h1_blender
```

The exporter validates `pilots/v10_mujoco_arm/data/trace.json` and checks the existing H1 MJCF from `assets/unitree_h1/mjcf/h1_with_hand.xml`. It writes a Blender payload and mesh assets to the requested output directory. Render with Blender 5.2 or a compatible build:

```text
blender --background --python pilots/v11_2_h1_blender/render_trace.py -- \
  --payload /path/to/blender_payload.json --output /path/to/render \
  --width 1920 --height 1080 --fps 30
```

In the 2026-10-09 WSL session, Blender 5.2.1 was installed on Windows at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`; it was not in WSL PATH and ordinary WSL interop invocation failed. The installed Windows executable was successfully invoked through the session's approved host execution route. That is an environment launch boundary, not a missing Blender installation. The output is copied to `output/h1_trace_blender.mp4` (1920×1080, H.264, 30 fps, 2.03 s); the `.blend` project is beside it. The export payload, intermediate meshes, and original render log remain under `/tmp/v112_h1_blender`.

## Trace and render boundary

The animation is recorded-state playback. It does not claim that Blender is a physics solver, does not integrate contacts, and does not alter the MuJoCo trace. This short render confirms actual mesh import, materials, studio lights/camera, trace-driven transforms, and delivery decode. It is a technical excerpt rather than a finished narrated lesson.

The Blender scene uses the existing `studio_utils` studio setup/floor/light helpers. Its custom trace-to-mesh payload mapping and recorded-pose playback are local pilot code; they are candidates for a future kit interface. The shared kit was not changed.
