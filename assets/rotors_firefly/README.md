# rotors_firefly

hexrotor MAV (AscTec Firefly) with separately-defined rotors for drone/aerial episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.rotors_firefly.v1`) for the machine-readable entry.

## Contents
urdf/firefly.xacro (+ multirotor_base.xacro, other MAV variants kept as text-only reference); meshes/ trimmed to firefly.dae + propeller_ccw/cw.dae only (other MAV bodies dropped, ~104MB->6MB)

## Provenance
- Source: `https://github.com/ethz-asl/rotors_simulator.git` @ `rotors_description` (branch `master`, commit `cd813b7a8c375d677352aa20ad20047feb661126`)
- License: Apache-2.0 (per rotors_description/package.xml)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
