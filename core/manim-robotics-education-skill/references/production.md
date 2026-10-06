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

## Readable transitions

Preserve geometry and semantic identity while changing the explanation. A new sentence does not need to morph unrelated Korean glyphs into each other. Keep persistent words/quantity tokens in place when they retain meaning; use a brief fade or replacement for a changed sentence. After replacement, update the scene's reference to the displayed label so subsequent animations address the live object. Do not fade/reset the whole scene to solve a text transition.

Inspect the transition's beginning, midpoint and end at delivery size, plus normal-speed playback when available. Reject distracting scattered glyphs, duplicate labels, disappearing anchors or a label colliding with a moving arrow. Keep the object/target visible while the viewer reads the new relation. Choose timing from measured phrases and the reading task; do not add a universal pause duration. Verify the final composited caption/diagram combination, since a clean raw scene can still become crowded in the edit.

## Visual links between discoveries

For requested narrative refinement, carry the prior conclusion as visible input to the next rule: a selected reference becomes the source of the target point; the target and current heading become the direction difference; that difference becomes a correcting command; measured response then replaces the illustrative command cue. Source each relation from the implemented model. Keep the relevant object anchored while locally dimming context and revealing the next relation. Use an orienting cut when coordinates or evidence time change, with the existing source-time disclosure.

Distinguish a drawn relation from a sentence that names it. If removing the explanatory sentence makes the decisive relation invisible, expose the target selection, comparison, direction or measured consequence in geometry before adding more text. Local labels may establish meaning; subtitles should not be the only evidence for the central inference. At each handoff, inspect the previous resolved state and the next input together at delivery size. Avoid piling all earlier relations into the final view; retire emphasis after its role is complete while retaining orientation anchors.
