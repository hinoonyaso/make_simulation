# realsense_d435

depth camera module (Intel RealSense D435/D435i) for depth_xyz/camera-frame episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.realsense_d435.v1`) for the machine-readable entry.

## Contents
urdf/ (shared macros for all RealSense models, text-only) + meshes/ trimmed to d435.dae + plug/plug_collision.stl only (other camera model meshes not copied, ~92MB->16MB)

## Provenance
- Source: `https://github.com/IntelRealSense/realsense-ros.git` @ `realsense2_description/` (branch `ros2-master`, commit `9a11121700cb4780e273e34141f6402fe184321d`)
- License: Apache-2.0 (per repo LICENSE/NOTICE.md)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
