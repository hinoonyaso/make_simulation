# JetRover reference assets

Raw reference geometry/kinematics for the JetRover robot, imported for use by the Blender skill
when an episode needs accurate JetRover geometry instead of the abstract stylized robot-arm
primitive in `blender-robotics-simulation-skill`. Not wired into any topic by default; loaded
only when a scene explicitly needs it.

## Contents
- `urdf/` — ROS2 xacro source (`jetrover.xacro` + per-part includes: arm, gripper, car_mecanum/
  car_acker/car_tank, lidar, imu, depth_camera, materials, inertial_matrix). These are xacro
  macros, not a flat URDF; use them as a reference for joint names/origins/axes/limits, not as a
  direct Blender import target.
- `meshes/` — 47 STL meshes grouped by subsystem: `arm/`, `gripper/`, `sensors/` (lidar, imu),
  `body/` (chassis back shells), `mecanum/`, `acker/`, `tank/` (drivetrain variants). Import
  these directly into Blender with the STL importer.

No standalone motor model exists anywhere in the source repo — drive/servo motors aren't
represented as separate meshes there, only as ROS control topics/messages; their housings are
baked into `body/`, `mecanum/acker/tank` wheel meshes, and the `arm/servo_link1`/`servo_link2`
covers.

## Provenance
- Source: `AI_secretary_robot/src/control/jetrover_arm_moveit/{urdf,meshes}`
  (`git@github.com:hinoonyaso/AI_secretary_robot.git`, commit `e3f0fb2a0d554095f2d08065293c5a96011025d9`)
- License: Apache-2.0 (as declared in that package's `package.xml`)
- This is a point-in-time copy, not a live link. If the source package changes materially,
  re-copy and bump the registry entry version.
- `sensors/` and `body/` were split out of the source's original `common/` folder locally for
  clarity; the `urdf/*.xacro` files still reference the original `meshes/common/...` path since
  they're kept unmodified as joint-reference source, not reprocessed — don't xacro-resolve them
  directly against this folder's layout.

## Registry
Each subsystem is its own entry, so an episode that only needs one part (e.g. just the lidar)
doesn't have to know about the rest: `blender.jetrover.sensors.v1`, `blender.jetrover.body.v1`,
`blender.jetrover.arm.v1`, `blender.jetrover.gripper.v1`, `blender.jetrover.base_mecanum.v1`,
`blender.jetrover.base_acker.v1`, `blender.jetrover.base_tank.v1`, plus
`reference.jetrover.urdf_xacro.v1` for the joint/kinematics reference. Look one up with
`core/visual-assets/asset_registry.py get <id>` — see `core/visual-assets/registry.json`.
