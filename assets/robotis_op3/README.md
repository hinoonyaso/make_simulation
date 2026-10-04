# robotis_op3

small humanoid robot (ROBOTIS OP3) for humanoid-locomotion episodes, simpler rig than Unitree H1.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.robotis_op3.v1`) for the machine-readable entry.

## Contents
urdf/ + meshes/; not pre-rigged

## Provenance
- Source: `https://github.com/ROBOTIS-GIT/ROBOTIS-OP3-Common.git` @ `op3_description/` (branch `master`, commit `0780e54c2064a42089b0cf970d716ae44fec9233`)
- License: Apache-2.0 (per repo LICENSE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
