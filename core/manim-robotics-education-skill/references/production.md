# Manim Production Rules

## State continuity
Treat each beat as `state_in -> state_out`. Keep persistent objects alive and transform them. Replace an object only when identity truly changes.

## Progressive disclosure
Build the final relation in layers: phenomenon/geometry -> marked quantity -> label -> equation term -> complete equation. Resolved details may dim instead of disappearing.

## Data-driven visuals
When a real algorithm/model/trace exists, load its values first and drive plots, numbers, edge widths, poses, and colors from those values. Keep computation outside the scene when it is reusable or expensive.

## Density control
For dense edges/attention/correspondence, start with the cell, pair, row, column or subset needed for the current inference. Expand to the whole when its structure matters. A display subset must preserve the full computation: do not renormalize probabilities over visible top-k terms unless that is the implemented algorithm. Indicate omitted terms or mass when relevant. Do not render a hairball merely because the full matrix exists.

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

## Carry one example into notation

Keep the same sample, axes, roles and units across geometry, components and equations. Map each equation term to a quantity the viewer has already seen; highlight its source before compressing the relation into notation. Preserve semantic color across views, with only the currently competing relations emphasized. Avoid morphing unrelated shapes merely to appear continuous.

Use one sourced numerical example after establishing spatial meaning, then a supported different condition to reveal the general rule. Displayed command targets and measured response must have distinct labels/time anchors. Subtitles may name a relation but should not be its only visible evidence. For reference-level work, inspect the central inference with subtitles hidden and check the resulting diagram against the source before adding detail.

## Animate a quantity into its equation term

For requested correspondence repair, build a formula from addressable term mobjects rather than one paragraph of text. Keep source labels/values attached to their geometry. `TransformFromCopy(source_value, term_slot)` preserves the measured example; reveal the operator after its operands are located, then the computed result. A copied value retains units and semantic role; only omit repeated units when the surrounding expression establishes them. Use geometric correspondence rather than unrelated glyph morphs.

For wheel conversion, reuse the same left/right numeric tokens in both `(vL + vR)/2` and `(vR − vL)/b`. Show the measured/configured spacing b as an axle span before moving its value into the denominator. The second formula reverses operand order; keep left/right identification explicit. When the condition changes, update the source tokens and dependent term/result objects together from one calculation. Do not tween through values as if they were additional recorded samples; label hypothetical conversion states. Inspect source, moving-copy midpoint and completed formula after captions are composited. A still equation or animated result alone is insufficient evidence of this repair.

## Give the inference room to be read

For a reported dense equation section, plan three viewer tasks within the existing measured beat: locate the quantity at its source, follow the copy to the operand, inspect the relation/result. Introduce one necessary relation at a time. For wheel conversion, settle the average before revealing the difference/spacing relation, with source roles and units still identifiable. Show the next active relation while retiring emphasis from the previous one; avoid having moving tokens cross a still-readable prior expression when a clear path or temporary retirement is available.

Inspect the composed caption, diagram and equation together. While a value is moving, keep narration/caption focused on that same correspondence; show a new explanatory sentence after the active mapping settles when this reduces competition. A raw equation's readable size is insufficient when the viewer must simultaneously read long captions. Use a settled pose for the changed-condition comparison and distinguish command goals from recorded response with short local labels.

If the measured narration leaves no room for the required reading task, return that exact interval to Director/narration for phrase or duration revision. Recompute speech timing and captions before adjusting scene timing. Do not silently stretch video away from speech or claim that a particular hold duration guarantees novice comprehension. Recheck the changed voiced interval and, when available, a first-time viewer's explanation.

## Geometric rotation and legible term changes

For an ideal differential-drive geometry explanation, derive heading change with a persistent axle/body and wheel travel arcs: at equal elapsed time, the outer minus inner distance is bθ. Preserve left/right roles, sign and units when copying those distances into the difference, span into b, and heading sweep into θ. The same construction should support straight and spin limiting cases without division by a zero turning radius. Label it as ideal/no-slip; measured solver motion remains sourced separately. Do not imply that displacement bars or the final ω formula already demonstrate the angular relation.

Keep formula operands, operators, units and results as separately addressable objects during updates. A generic group-to-paragraph `Transform` can fragment glyphs between otherwise readable endpoints. Prefer matching semantic tokens or replacing only the changed value in its fixed slot, with an intentional short fade when correspondence is absent. Keep unchanged operators and the governing relation readable. Inspect early/middle/late composited transition frames and the settled result; do not let decorative number tweens appear to be measured samples.

For prediction overlays, test text against the arrows' swept bounds and caption area, not only their initial positions. Remove a duplicated question or move it to a clear region; preserve useful direction cues. Change layout only to expose the active inference while retaining identity and orientation. Prototype missing arc/slot/layout helpers locally and document kit candidates when kits are protected.

## Show the equality and changed geometry

When a derivation is the requested repair, expose its intermediate relation. For ideal differential drive, draw the shared center, inner/outer radii and the same heading sweep; mark rR−rL=b. Attach sL and sR to the respective arcs, reveal rLθ/rRθ, then subtract to obtain bθ. Preserve term colors and addressable operators; do not replace this step with a whole equation FadeIn. A center trajectory halfway between wheel trajectories explains the forward average. Handle straight motion without dividing by a zero turning rate.

For a track-width comparison, derive both motions from the same wheel travel and elapsed time. Alter the axle span and show the resulting heading sweeps at the same scale before revealing the ratio. Label this ideal/no-slip construction; keep it distinct from recorded slip/contact response. Carry the span value from geometry into the denominator. Use source, transition and final frame checks, including final captions.

For feedback, use one world-to-screen transform for recorded body pose, actual lookahead, current heading and history. Freeze a sourced state to expose error/command, replay its actual response, then highlight the next comparison. Preserve per-sample source times and distinguish held explanatory snapshots from the measured timeline. Relative diagrams are useful after world context is established, but a changing error label beside an unchanged body does not show the return from response to input.

Adapt composition to the inference: geometry can occupy the center during derivation, matched trajectories during comparison, world context during feedback. Retire resolved text; do not reset persistent subjects or change layout merely for variety. Missing helpers stay local while shared kits are protected.
