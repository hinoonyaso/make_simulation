# robotiq_2f85

2-finger parallel gripper (Robotiq 2F-85) for grasp episodes, mountable on UR5e/xArm/FR3 end effectors.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.robotiq_2f85.v1`) for the machine-readable entry.

## Contents
urdf/ (shared macros for 2F-85/2F-140, text-only) + meshes/{collision,visual}/2f_85/ only (2f_140 meshes not copied)

## Provenance
- Source: `https://github.com/PickNikRobotics/ros2_robotiq_gripper.git` @ `robotiq_description/` (branch `main`, commit `a74d007d8f2f06dc6a503ad21038ba869d4999a6`)
- License: per repo LICENSE
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
