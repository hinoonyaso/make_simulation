# px4_iris

quadrotor MAV (3DR Iris) for drone/aerial episodes; base_link + 4 rotors.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.px4_iris.v1`) for the machine-readable entry.

## Contents
SDF (iris.sdf), not URDF; meshes/ (mostly .dae); no LICENSE file in this repo, license is BSD per package.xml

## Provenance
- Source: `https://github.com/PX4/PX4-SITL_gazebo-classic.git` @ `models/iris` (branch `main`, commit `807b67bb3007113ea52fd36ec2cefae4a5fa3f85`)
- License: BSD (per repo package.xml, no LICENSE file present)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
