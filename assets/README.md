# Reference robot assets

Raw URDF/xacro/SDF + mesh imports for real robots, used by the Blender skill when an episode
needs accurate geometry/kinematics instead of the abstract stylized primitives in
`blender-robotics-simulation-skill`. None of these are wired into any topic by default — loaded
only when a scene explicitly needs one. Each subfolder is a point-in-time copy of the relevant
description package from its upstream repo, not a live link; see each subfolder's own README.md
for exact source path/commit/license, and `core/visual-assets/registry.json` for the
machine-readable lookup entries (`asset_registry.py list --tool blender`).

STL/DAE meshes alone carry no joints/skeleton. To actually pose/animate a robot, build a joint
hierarchy in Blender (Empties or Armature bones) from each robot's urdf/xacro `origin`/`axis`/
`limit` values, then either pose by hand (FK) or keyframe from a real joint-angle trace via
`blender-robotics-simulation-skill/templates/animation_utils.py`.

| Folder | Robot | Category | Registry id |
|---|---|---|---|
| `jetrover/` | Hiwonder JetRover (mecanum/acker/tank base + arm) | mobile manipulator | `blender.jetrover.{sensors,body,arm,gripper,base_mecanum,base_acker,base_tank}.v1`, `reference.jetrover.urdf_xacro.v1` |
| `unitree_go2/` | Unitree Go2 | quadruped | `blender.unitree_go2.v1` |
| `unitree_h1/` | Unitree H1 | humanoid (19 joints) | `blender.unitree_h1.v1` |
| `robotis_op3/` | ROBOTIS OP3 | humanoid (simpler than H1) | `blender.robotis_op3.v1` |
| `rotors_firefly/` | AscTec Firefly (ETH RotorS) | hexrotor drone | `blender.rotors_firefly.v1` |
| `px4_iris/` | 3DR Iris (PX4) | quadrotor drone, SDF not URDF | `blender.px4_iris.v1` |
| `crazyflie/` | Bitcraze Crazyflie | small educational drone | `blender.crazyflie.v1` |
| `ur5e/` | Universal Robots UR5e | 6-DOF arm | `blender.ur5e.v1` |
| `xarm6_7/` | UFACTORY xArm6 / xArm7 | 6/7-DOF arm + gripper/camera mounts | `blender.xarm6_7.v1` |
| `franka_fr3/` | Franka FR3 | 7-DOF arm + hand gripper | `blender.franka_fr3.v1` |
| `open_manipulator_x/` | ROBOTIS OpenManipulator-X | small 4-DOF educational arm | `blender.open_manipulator_x.v1` |
| `turtlebot3/` | ROBOTIS TurtleBot3 (burger/waffle/waffle_pi) | differential-drive mobile base | `blender.turtlebot3.v1` |
| `realsense_d435/` | Intel RealSense D435/D435i | depth camera | `blender.realsense_d435.v1` |
| `robotiq_2f85/` | Robotiq 2F-85 | 2-finger gripper (mountable on arm end effectors) | `blender.robotiq_2f85.v1` |
| `livox_mid360/` | Livox Mid-360 / Mid-360S | LiDAR | `blender.livox_mid360.v1` |
| `ouster_os1/` | Ouster OS1 | LiDAR | `blender.ouster_os1.v1` |
| `ouster_os0/` | Ouster OS0 | LiDAR | `blender.ouster_os0.v1` |
| `ouster_osdome/` | Ouster OSDome | LiDAR | `blender.ouster_osdome.v1` |
| `zed2i/` | Stereolabs ZED 2i | stereo depth camera | `blender.zed2i.v1` |
| `raspberry_pi5/` | Raspberry Pi 5 (With Graphics) | single-board computer | `blender.raspberry_pi5.v1` |

The six entries above are **STEP files, not STL/DAE** — Blender has no native STEP importer. A
FreeCAD executable was not found in the current environment, so these have not been converted or
Blender-validated here. Their folders exist in this worktree but are ignored by Git; they do not
appear in a clean clone. Licensing differs per item: `livox_mid360/`, `ouster_*/`, and `zed2i/`
are proprietary vendor reference CAD with no established public redistribution permission, so
they remain local-use-only. `raspberry_pi5/` contains a local MIT license, but whether it covers
the STEP export was not independently confirmed; that file also remains ignored. See
`docs/assets/EXISTING_ASSET_AUDIT.md` and `docs/assets/SOURCE_LICENSE_MATRIX.md` for the evidence.

## Engineering educational geometry

See [`education/README.md`](education/README.md) for the CC0 procedural Blender library. It
contains six generated assemblies spanning bearings, gears, shaft/coupling, spring/fasteners,
BLDC motor, PCB, battery-cell concept, beam/bracket and fan/heatsink, with separate object names,
metric units, and motion keys where useful. These are educational models with explicit limits,
not product CAD or solver output. See `docs/assets/` for acquisition, licensing, conversion and
Blender validation reports.

## What was deliberately left out
- **PX4 Iris** was kept instead of adding a second drone-only alternative; RotorS Firefly and PX4
  Iris already cover the "xacro-based" vs "SDF-based" drone cases.
- Mesh sets were trimmed to only the requested variant where a repo bundles many robots/cameras
  in one package (e.g. only `ur5e/` meshes out of all UR arms, only `d435` out of all RealSense
  models, only `xarm6`/`xarm7`/`gripper`/`camera` out of all xArm variants, only `2f_85` out of
  `2f_85`/`2f_140`). This kept the total import at ~340MB instead of several GB; each subfolder's
  own README notes what was dropped and why.
- **Not included in the clone**, because a vendor form, forum login, or account is required (each needs a human download)
  form, forum login, or account, which can't be automated here) — tracked as pending work in
  `TODO.md`: Jetson Orin Nano Dev Kit + module, STM32 Nucleo-F446RE, Hailo-8 M.2, and
  BlenderKit's Warehouse Rack / Industrial Assets. Local ignored sensor and Pi assets are tracked
  as audit evidence, but are not included in Git or reported as clone-reproducible.
