# Manim Production Rules

## State continuity
Treat each beat as `state_in -> state_out`. Keep persistent objects alive and transform them. Replace an object only when identity truly changes.

## Progressive disclosure
Build the final relation in layers: phenomenon/geometry -> marked quantity -> label -> equation term -> complete equation. Resolved details may dim instead of disappearing.

## Data-driven visuals
When a real algorithm/model/trace exists, load its values first and drive plots, numbers, edge widths, poses, and colors from those values. Keep computation outside the scene when it is reusable or expensive.

## Density control
For dense edges/attention/correspondence, show only top-k or values above a threshold first. Reveal additional structure only when it changes the explanation. Do not render a hairball merely because the full matrix exists.

## Layout and camera
Prefer `.arrange()`, `.next_to()`, grouping, and reusable layout helpers over manual coordinate arithmetic. Move camera for viewpoint/scale changes, not as decoration.

## Timing
Stagger secondary elements. Give the viewer a short pause after a conceptual reveal. Decorative motion should be nearly zero.

## Iteration
Name scene sections and render low-cost previews of the densest beat before final output. Fix the actual rendered frame, not the imagined code.

## Validated patterns (pilots/01_teb_reference)
- Colour data by the model's own threshold (e.g. clearance < 0.20 m -> red), blended over a thin band, so colour is evidence.
- Log-height stacked cost bar: total on a log scale, segment shares linear. Labels fade with segment height.
- Ghost replay at real time along the optimised schedule shows "time is part of the plan" without extra text.
- Focus transitions by a tracker (dim the rest to ~22%) instead of removing and re-adding mobjects.
- Push the camera in after the handoff hold; hero + key structure should fill ~60-75% of the frame.
