# crazyflie

small/simple educational quadrotor for lightweight drone episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.crazyflie.v1`) for the machine-readable entry.

## Contents
urdf/crazyflie2.urdf.xacro + urdf/crazyflie.urdf.xacro; meshes/; community ROS1 package (not official Bitcraze repo)

## Provenance
- Source: `https://github.com/whoenig/crazyflie_ros.git` @ `crazyflie_description` (branch `master`, commit `df3ce76f700953cfa2794b8fd4628ea6b93c92c4`)
- License: per repo LICENSE
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
