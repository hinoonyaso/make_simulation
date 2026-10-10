# Engineering Educational Assets

This folder contains original, procedural Blender teaching assemblies, metadata,
and a deterministic generator. The generated geometries and previews are released
under CC0 1.0; see [LICENSE](LICENSE). Each model JSON records its dimensions,
animation status and educational limitations. These files do not claim product
accuracy or physics-solver evidence unless a field explicitly says otherwise.

Generate all native Blender assets and PNG previews:

```bash
blender --background --factory-startup --python-exit-code 1 \
  --python assets/education/generate_assets.py -- \
  --output-root assets/education/generated --render
```

Validate the saved `.blend` files by opening them in Blender:

```bash
blender --background --factory-startup --python-exit-code 1 \
  --python scripts/validate_blender_education_assets.py
```

Export a registered Blender assembly as a cached GLB via `AssetFactory` (the
converter re-imports the output to check that meshes survive):

```bash
uv run python scripts/acquire_education_assets.py --convert --allow-convert \
  --asset edu.bearing_6204.v1 --target glb
```

The catalog includes a 6204 boundary envelope, estimated bearing internals with
ideal rolling speed ratios computed from stated contact radii (outer race fixed;
no contact solver), stylized 20:40 spur gears, a 9-slot/6-pole motor concept, layered PCB, shaft and
coupling, spring, fasteners, battery-cell concept, beam/bracket, heatsink and fan.
Some are grouped into six compact `.blend` scenes so the files stay manageable;
objects remain separately named/selectable. These scenes are educational visual
geometry, not parametric CAD or analysis meshes.

Registry integration lives in `core/visual-assets/registry.json`. `scripts/
acquire_education_assets.py` audits existing assets and maintains acquisition and
license status. It plans by default; actual download has a separate explicit flag
and still requires pinned hashes, exact sizes, approved hosts, and rights metadata.
No gated vendor downloads are automated.

Existing vendor sensor STEP files in the local worktree are ignored by Git and
remain local-use-only pending explicit redistribution/video permissions. A clean
clone does not contain them.
