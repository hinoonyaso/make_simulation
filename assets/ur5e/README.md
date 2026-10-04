# ur5e

6-DOF industrial manipulator (Universal Robots UR5e) for FK/IK/grasp episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.ur5e.v1`) for the machine-readable entry.

## Contents
urdf/ (shared macros for all UR variants, text-only) + meshes/ur5e/{visual,collision}/ only (other UR variant meshes not copied)

## Provenance
- Source: `https://github.com/UniversalRobots/Universal_Robots_ROS2_Description.git` @ `urdf/ + meshes/ur5e/` (branch `humble`, commit `b48aa88ac18a17466e767929f05f45b23e332a8e`)
- License: BSD-3-Clause (per repo LICENSE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
