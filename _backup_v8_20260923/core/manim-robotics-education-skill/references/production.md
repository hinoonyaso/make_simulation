# Manim Production Rules

## Continuous visual reasoning
Keep persistent objects alive across beats. A point P should remain P while its representation changes from image pixel -> ray -> 3D point -> transformed point. Replace only when identity truly changes.

## Progressive disclosure
A dense final equation should be built in stages. Reveal the geometric quantity first, then its label, then copy/transform it into the equation. Hide or mute already-resolved details.

## Math-to-visual derivation
Prefer `visible relation -> measured/marked quantity -> symbol -> equation`. Reuse color across the object and its symbol. Do not color every token; color the few variables carrying meaning.

## Attention hierarchy
At one moment: one dominant object, one optional supporting element, everything else muted. Strong motion, bright color, scale change, and camera motion are all attention tools—do not use them simultaneously without reason.

## Camera
Move the camera only for a change in viewpoint or scale of reasoning. Object state changes should usually be expressed by object motion/transformation, not by camera motion.

## Timing
Use short pauses after conceptual reveals. Continuous trackers should move slowly enough that the viewer can predict the trend before the conclusion appears. Keep decorative motion near zero.
