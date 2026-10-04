# unitree_h1

19-joint humanoid robot for humanoid-locomotion/whole-body episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.unitree_h1.v1`) for the machine-readable entry.

## Contents
urdf/ (joint hierarchy) + meshes/ + mjcf/ (alt format, reference only); not pre-rigged; heaviest asset in this set (~82MB)

## Provenance
- Source: `https://github.com/unitreerobotics/unitree_ros.git` @ `robots/h1_description` (branch `master`, commit `ccfc6fd8430a17ba3dacef9a1e2faf64ff3b0aee`)
- License: BSD-3-Clause (per repo LICENSE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
