# franka_fr3

7-DOF research/industrial manipulator (Franka FR3) with hand gripper for FK/IK/grasp episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.franka_fr3.v1`) for the machine-readable entry.

## Contents
robots/fr3 + robots/common (arm xacro) + end_effectors/franka_hand + end_effectors/common (gripper xacro); meshes/robots/fr3 + meshes/robot_ee/franka_hand_white

## Provenance
- Source: `https://github.com/frankaemika/franka_description.git` @ `robots/fr3, end_effectors/franka_hand` (branch `main`, commit `7aeeddc449edf8d62b594f9e36a81da53e7796f9`)
- License: Apache-2.0 (per repo LICENSE/NOTICE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
