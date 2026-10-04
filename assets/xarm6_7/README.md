# xarm6_7

6/7-DOF industrial manipulator (UFACTORY xArm6/xArm7) with gripper+camera mounts for FK/IK/grasp episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.xarm6_7.v1`) for the machine-readable entry.

## Contents
urdf/ (shared macros for all xArm variants, text-only) + meshes/{xarm6,xarm7,gripper,camera}/ only (lite6/uf850/xarm5 meshes not copied)

## Provenance
- Source: `https://github.com/xArm-Developer/xarm_ros2.git` @ `xarm_description/` (branch `humble`, commit `62936f7ea1846a85f7350de2c4c18f39e6d19715`)
- License: BSD-3-Clause (per repo LICENSE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
