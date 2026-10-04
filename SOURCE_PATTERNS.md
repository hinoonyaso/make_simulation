# Public-source production patterns integrated into V9

This file is provenance/reference only. Do **not** preload it during normal generation.
V9 reimplements general production patterns; it does not copy creator scene code or imitate a creator's distinctive voice/branding.

## 3Blue1Brown / 3b1b/videos
Observed reusable patterns:
- persistent visual objects instead of slide replacement;
- rapid preview/checkpoint iteration before final render;
- reusable custom components and declarative layout helpers;
- staged scene assembly;
- trackers/updaters and staggered reveals for continuous visual reasoning;
- high-resolution masters and visual testing by preview/render.
Source license for `3b1b/videos`: CC BY-NC-SA 4.0. Manim engine itself is MIT. V9 contains no copied scene code.

## Welch Labs / WelchLabs/videos
Observed reusable patterns:
- separate exploratory/data-generation notebooks/scripts from final animation scenes;
- drive visuals from actual generated data rather than decorative fake curves;
- domain-specific visual components with parameterized style;
- reduce dense network/attention visual clutter by showing only meaningful connections.
Repository license: MIT.

## Reducible / nipunramk/Reducible
Observed reusable patterns:
- use a domain computation library when geometry/algorithm correctness matters instead of hand-faking intersections/results;
- keep the animation layer close to the underlying algorithm state;
- use Manim Community when its tooling/support is the practical choice.
V9 uses patterns only; no repository code is copied.

## Primer / PrimerTools and archived primerpython
Observed reusable patterns:
- high-level reusable 3D objects with state/keyframe methods;
- reusable asset library instead of rebuilding hero objects per video;
- camera, LaTeX, simulation and state-change animation as first-class systems;
- separate simulation state from visual presentation.
The archived Blender 2.79 implementation is not copied; V9 provides original modern Blender helpers.

## Sebastian Lague public simulation projects
Observed reusable patterns:
- animate real implemented simulation state, not explanatory keyframes labeled as simulation;
- parameterized simulation/rendering systems produce both correctness and visual richness;
- preserve a clean separation between simulation logic and presentation.
Several referenced repositories are MIT/GPL depending on project. V9 contains no copied project code.

## Not used as code sources
Targeted searches did not surface comparable official production-source repositories for Veritasium, Two Minute Papers, or Kurzgesagt. Third-party projects claiming their style are not treated as authoritative production sources.

## Coding Train / public tutorial source ecosystem
Observed useful pattern: keep a working parameterized implementation close to the explanation, and expose a small number of meaningful parameter changes so the viewer can form a causal model. V9 uses this only when it reduces abstraction rather than adding controls for their own sake.

## Acerola / public graphics projects
Observed useful pattern: when explaining a rendering/shader phenomenon, let the actual renderer/material/shader generate the visual evidence. V9 prefers real render-state demonstrations over fake post-hoc overlays when the rendering mechanism itself is the topic.
