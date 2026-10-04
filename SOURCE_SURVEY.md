# Relevant educational/technical YouTube source survey

Provenance only. Do not preload during production.

## Full or near-full video production source available — integrated strongly
- 3Blue1Brown — https://github.com/3b1b/videos — actual Manim scene repository and development workflow. Patterns integrated: persistent visual state, fast preview/checkpoint iteration, custom reusable components, staged scene assembly, trackers/updaters, declarative layout.
- Welch Labs — https://github.com/WelchLabs/videos — supporting data notebooks/scripts + final animation scenes. Patterns integrated: compute/data first, animation second; real values drive visuals; domain-specific components; density filtering.
- Reducible — https://github.com/nipunramk/Reducible — code for channel videos. Patterns integrated: algorithm state drives animation; use robust domain libraries for geometry rather than hand-faked results; practical Manim CE compatibility.
- Primer — https://github.com/Primer-Learning/PrimerTools and archived https://github.com/Helpsypoo/primerpython — reusable animation/simulation/camera/state-change tooling. Patterns integrated: stateful 3D objects, reusable assets, simulation/presentation separation, camera as a first-class system.

## Project/source code tied closely to technical videos — integrated selectively
- Sebastian Lague — e.g. https://github.com/SebLague/Fluid-Sim , https://github.com/SebLague/Ray-Marching , https://github.com/SebLague/Slime-Simulation. Pattern: real implemented simulation/render state should drive the video; do not label scripted keyframes as simulation.
- The Coding Train / Daniel Shiffman — public tutorial/challenge source ecosystem. Pattern used selectively: working, parameterized examples and visible iterative state are better teaching substrates than decorative diagrams.
- Acerola / Garrett Gunnell — https://github.com/GarrettGunnell — public graphics/shader projects corresponding to technical videos. Pattern used selectively: when a rendering phenomenon is central, demonstrate the real rendering/material/shader behavior rather than a fake overlay.
- Freya Holmér — https://github.com/FreyaHolmer — public math/shader tooling. Used only as reinforcement for reusable math/graphics primitives; not treated as a full video-production-source repository.

## No comparable official production-source repository found in targeted search
- Veritasium
- Two Minute Papers
- Kurzgesagt

Third-party repositories that claim to reproduce those channels' styles are not treated as authoritative production sources and are not copied into this bundle.
