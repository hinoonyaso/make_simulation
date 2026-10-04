# raspberry_pi5

Single-board computer (Raspberry Pi 5), for edge_ai/edge-compute episodes needing a real board
instead of an abstract box. Raw reference geometry import, not wired into any topic by default.
See `../README.md` for the shared usage pattern and `core/visual-assets/registry.json` (id
`blender.raspberry_pi5.v1`) for the machine-readable entry.

## Contents
- `raspberry_pi5.step` — the "With Graphics" variant (silkscreen/connector detail included;
  chosen over the smaller "No Graphics" variant for video use). STEP format — Blender has no
  native STEP importer; convert via FreeCAD (import, then export to STL/OBJ) or a Blender
  STEP-import addon before use. 136MB uncompressed — the largest single asset in this folder.
- `LICENSE.txt` — the MIT license text as shipped in the vendor ZIP.

## Provenance
- Downloaded directly from:
  `https://pip-assets.raspberrypi.com/categories/892-raspberry-pi-5/documents/RP-010082-CA-1-rpi-5%203D%20STEP%20-%20With%20Graphics%20large%20file.zip`
- Vendor page: `https://pip.raspberrypi.com/categories/892-raspberry-pi-5`
- **License: MIT, (c) Raspberry Pi Ltd.** Unlike the LiDAR/camera CAD in sibling folders
  (`livox_mid360/`, `ouster_*/`, `zed2i/`), which are proprietary vendor reference-only, this one
  is genuinely OSS — see the included `LICENSE.txt`.
- A smaller "No Graphics" variant (13MB zip) also exists at the same vendor page if the 136MB
  file becomes a problem.
- This is a point-in-time download, not a live link. Re-download and bump the registry `version`
  if the vendor updates the model.
