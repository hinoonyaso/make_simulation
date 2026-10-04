# turtlebot3

differential-drive mobile robot (burger/waffle/waffle_pi variants) for navigation/SLAM/TF2 episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.turtlebot3.v1`) for the machine-readable entry.

## Contents
urdf/ + meshes/{bases,sensors,wheels}/ covering all 3 chassis variants

## Provenance
- Source: `https://github.com/ROBOTIS-GIT/turtlebot3.git` @ `turtlebot3_description/` (branch `humble`, commit `90a68bd2e3c61c12966779da89d8eeaec82730e9`)
- License: Apache-2.0 (per repo LICENSE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
