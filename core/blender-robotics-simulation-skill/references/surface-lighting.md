# Surface and lighting refinement

Read for an explicit material/lighting refinement request or a demonstrated flat studio image. Keep the established bright studio, faithful robot asset, camera purpose, semantic colors and solver poses. This is a surface treatment task; it does not justify new narration, camera choreography or a new simulation run.

## Start from a visible surface problem

Choose a delivery-size frame showing the named weakness and a second recorded state that changes the visible face or wheel orientation. Record the source samples and baseline image. Name the part and its failure, for example: deck sides merge across layers; tyre tread disappears into the wheel face; a bright plate highlight obscures its rim; contact shadow cannot locate the tyre against the floor. “More polished” alone is not a candidate specification.

Separate causes before changing parameters:

| Observation | First useful probe | Preserve |
| --- | --- | --- |
| Plate layers merge despite different base colors | Move the existing key to rake across the layer edges; compare lower fill with the baseline | Planar faces, actual gaps, bright overall studio |
| Broad uniform highlight flattens the part | Adjust key direction and apparent emitter size; then the part's roughness if needed | Highlight detail, surface identity, no clipped rims |
| Tyre/face reads as one black shape | Seek a soft side highlight across tread/face with enough fill to retain dark detail | Rubber stays dark; phase mark remains an annotation |
| Object floats or its floor boundary disappears | Compare key direction, floor reflectance and shadow softness at the recorded contact view | Actual wheel pose and gap; shadow is not contact-force evidence |
| Floor texture/reflection attracts more attention than the robot | Reduce floor competition locally before raising every light | Useful stationary ground landmarks and path contrast |
| Close-view silhouette or normals are visibly coarse | Inspect the asset/normal treatment separately | Faithful dimensions; light changes cannot repair a coarse silhouette |

A bright studio can still have directional modeling. Use the key to reveal a face-to-side transition, fill to retain shadow detail, and a rim only if a particular silhouette remains unresolved. Equalizing all light directions or raising all powers can erase the very boundaries under review. Black cavities and burnt highlights are not stronger material separation.

## Give materials distinct optical jobs

Identify the actual represented surface before assigning metalness: a painted/coated metal deck can read through its coating; a black plate is not automatically bare metal. Use restrained base values, plausible specular/roughness relationships and the existing component identities. Rubber, sensor housing and plate need distinguishable highlights and edge response, rather than three arbitrary colors or uniformly glossy materials.

Begin with existing geometry and textures. Add fine roughness variation only when the selected view resolves it and it reduces an observed uniform/plastic appearance. Keep its scale and strength restrained; avoid decorative scratches, noisy concrete and fabricated mechanical details. If asset geometry limits a curved silhouette, document that separate limitation instead of claiming that texture or a roughness change fixed it.

## Compare a treatment, not just parameter changes

Keep camera, solver pose, resolution, color management and exposure fixed while diagnosing material/light changes. Reuse the baseline. A compact candidate set can include a material-only probe, a light-only probe, then the promising combination. These are diagnostic choices, not a mandatory number of renders. For lights, direction/emitter size/fill balance often changes the evidence more than another small base-color adjustment; test the named cause first.

Save the effective settings and changed objects with each candidate. For imported/reused scenes, inspect actual material slots, shader links, view-layer overrides and material/node animation only if the expected change does not appear. Verify the requested light was found; a name match that changes no light is not a completed lighting experiment. Use unique output paths and verify the source script/settings so an old render is not selected as a new candidate.

Inspect native images first, then the final size with captions. An RGB difference image or summary can confirm that an edit reached the pixels; it cannot judge attractive shading or establish improvement. Convert RGBA images to RGB for RGB-only difference bounds: zero alpha difference can hide real color changes in an RGBA bounding-box check. Do not impose a global pixel-change threshold.

Choose by the named boundary: deck rim and layer gap, tyre/face/tread, grounded floor edge, and highlight shape. State the observed benefit and any regression. A new material name, plausible roughness, nonzero pixel difference or absence of blockers does not demonstrate surface refinement.

If the first candidates differ only subtly and the named weakness remains, mark the refinement `needs_revision`. Change the diagnosed light/surface cause and make a bounded second comparison. Stop when the target is visibly improved across the selected states without regression. If the bounded comparison remains inconclusive, retain the best supported treatment and report the unresolved target; do not expand into unrelated scene redesign.

## Verify the selected treatment across shots

Check context, pair/component and wheel-ground views where they actually use the changed treatment. Hide-body shots cannot establish improved deck shading: inspect the restored body as well. At each relevant cut, inspect entry, decisive state and exit for consistent plate/tyre/housing identity, visible gaps and shadows, semantic path contrast and safe caption space. Keep exposure stable while comparing shots; per-shot grading must not disguise a material failure.

Use a short moving render around a turn to inspect travelling highlights, shimmer and shadow stability when playback is available. A few sampled frames establish only their visible surface states. Keep motion-dependent polish uninspected if playback is unavailable.

## Record the result

Use the existing episode README and review report: baseline defect, fixed source/camera states, effective candidate settings, selected evidence, remaining asset/playback limits. Keep `acceptable` technical readability separate from `improved` surface craft. Implement missing material/light comparison helpers locally when kits are protected; propose migration only after their benefit is demonstrated.

### R17 evidence that motivates this refinement

`pilots/05_moving_obstacle/revision_17/output/surface_comparison.jpg` compares R16/R17 at the same poses (0 and6 seconds). R17's darker deck treatment gives modest side separation, while the broader studio response stays similar. `output/final_review_report.json` explicitly calls the benefit modest. This supports testing the missing light-response interaction next; it does not establish an optimal light rig or a defect in every studio shot. The wheel-ground view already improved component readability and remains a separate completed target.
