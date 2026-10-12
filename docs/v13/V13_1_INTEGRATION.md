# V13.1 Asset Accuracy and Education Pipeline Integration

## Scope and decisions

The V13.1 integration keeps the procedural Blender assets self-authored and
CC0-1.0. The education renderer loads models only through `AssetFactory` and
the registered collection, checks the registry hash and license, then applies
lesson transforms and animation. The legacy bearing renderer remains available
for specs without `asset_id`.

Missing optional vendor CAD is reported as `MISSING_LOCAL_ASSET`; a missing
model does not make a fresh clone invalid. Broken paths, hash mismatches, or
invalid present assets still fail validation. This addresses the clean-clone
CI failure from workflow run `38051355645`, whose old test assumed the local
Livox CAD file was tracked. No vendor CAD was downloaded or redistributed.

Gear origins are at their axes, and the 20:40 gear pair is driven at a -2
angular-speed ratio around the declared 60 mm center distance. The BLDC asset
has separate fixed stator and rotating rotor assemblies; its coils stay fixed,
and exposed magnets rotate with the rotor. The fan rotor is separated from its
fixed frame. The bearing cage and rolling elements are animated from the
declared ideal no-slip kinematics; Blender does not solve contact dynamics.
These are educational kinematic models, not electromagnetic, CFD, or contact
solver results.

The shared Blender loader and scene primitives are local to `core/education`
and `pilots/v13_education/blender`; the kit is unchanged. The lesson planner
validates asset/blueprint compatibility and sends asset-backed lessons to the
generic Blender scene. Existing robotics routing is untouched.

## Verification evidence

- Blender 5.2.1 LTS regenerated all six procedural assets and reopened them.
- `scripts/validate_blender_education_assets.py`: all six assets pass geometry,
  hierarchy, keyframe, and selected-frame kinematic checks.
- `scripts/validate_education_asset_loader.py`: bearing, BLDC, and PCB append,
  transform, material override, and static-freeze smoke checks pass in Blender.
- The full local suite and a detached clean worktree with the tracked patch both
  pass: 159 tests.
- The BLDC lesson preview at
  `pilots/v13_education/output/lessons/bldc-asset-integration-v2/preview.mp4`
  is 20 seconds, 960x540, 30 fps, silent, and fully decodes. Frames were
  inspected at 2, 6, and 13 seconds; the first shows the stator/rotor separated
  and later frames show the rotor assembly rotating. This is a preview, not a
  narrated delivery.
- The PCB lesson preview at
  `pilots/v13_education/output/lessons/pcb-asset-integration-v3/preview.mp4`
  is 20 seconds, 960x540, 30 fps, silent, and fully decodes. Frame review caught
  and drove a fix for missing `separate_layers` animation; corrected frames
  show the copper stack separating and returning to the assembled board.
- The 24-second Bearing integration preview is at
  `pilots/v13_education/output/lessons/bearing-asset-integration-v2/preview.mp4`.
  It uses the registered `edu.bearing_6204.v1` collection at 960x540/30 fps.
  Full decode passed. Sampled frames still show overly dark cut faces and
  bright metal highlights; this is a technical integration smoke preview, not
  a visual-quality pass or a full-motion review.
- The previous remote CI run failed on the local-only CAD assumption. A new
  Actions run for this uncommitted revision is **NOT_RUN**; it requires a
  pushed revision, which has not been authorized here.

## Limits and follow-up

The preview path is concept-only and deliberately runs no electromagnetic,
thermal, or fluid solver. No external CAD file was downloaded. KiCad is an
identified official source, but this WSL environment has no FreeCAD or STEP
conversion executable; the candidate is documented without claiming
acquisition or conversion. Other CAD acquisition remains manual where
redistribution and media-use rights are not established in
`docs/assets/SOURCE_LICENSE_MATRIX.md`.
