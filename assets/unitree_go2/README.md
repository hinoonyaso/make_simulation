# unitree_go2

quadruped legged robot (base->hip->thigh->calf x4) for legged-locomotion episodes.

Raw reference geometry/kinematics import, not wired into any topic by default. See
`../README.md` for the shared usage pattern and `core/visual-assets/registry.json`
(id `blender.unitree_go2.v1`) for the machine-readable entry.

## Contents
urdf/ + xacro/ (joint hierarchy, axis/limit) + meshes/ + dae/; not pre-rigged

## Provenance
- Source: `https://github.com/unitreerobotics/unitree_ros.git` @ `robots/go2_description` (branch `master`, commit `ccfc6fd8430a17ba3dacef9a1e2faf64ff3b0aee`)
- License: BSD-3-Clause (per repo LICENSE)
- Point-in-time copy, not a live link. Re-copy and bump the registry `version` if the
  upstream source changes materially.
