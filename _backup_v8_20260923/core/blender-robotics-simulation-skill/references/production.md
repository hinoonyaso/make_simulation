# Blender Production Rules

## Visual hierarchy
Use one hero mechanism per shot. Background geometry should be simpler, darker, lower-contrast, or less saturated. Use material contrast before adding extra lights.

## Geometry
Use clean primitive/parametric forms unless real geometry is required. Apply small bevels to hero hard surfaces so light reveals shape. Avoid micro-detail that does not teach.

## Lighting
Use soft key + weaker fill + subtle rim. Shadows should establish spatial contact, not create drama that hides geometry. Keep overlays/rays brighter than surrounding surfaces.

## Camera
Use 35–50 mm for context, 50–70 mm for mechanism, 70–100 mm for detail. Use orthographic for axis/parallelism comparisons. Move camera only to reveal a relation or viewpoint change.

## Manim compatibility
Maintain the same semantic colors and variable/frame names. Prefer neutral dark world/background. For mixed sequences, render transparent PNG/WebM when compositing is easier than matching backgrounds exactly.

## Animation
Simulation/trace motion follows timestamps. Explanatory keyframes may ease in/out, but do not smooth away meaningful trajectory behavior. Ghost poses are useful for before/after comparison when clearly labeled.
