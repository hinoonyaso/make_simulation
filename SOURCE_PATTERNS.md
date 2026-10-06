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

## 2026-10 explanation-craft update: user-selected references

Goal: address the moving-obstacle pilot's weak decision explanation, low overlay contrast, and padded pacing through skill instructions, without changing kits, trace schemas, finished topics, or delivered media.

- [3Blue1Brown official production advice](https://www.3blue1brown.com/about/): concrete examples before abstractions/definitions; movement has an identifiable teaching purpose; visuals reinforce narration. [Linear transformations lesson](https://www.3blue1brown.com/lessons/linear-transformations/) is a primary reference for building an abstraction from visible transformations. Applied here to persistent comparisons, phrase anchors, and an observable answer to the opening question. These are original project adaptations, not copied scenes.
- User-selected Korean channel: https://www.youtube.com/@3Blue1BrownKR . The advice above comes from the original creator's official site, not a verified claim about this Korean channel's production process.
- User-selected spatial/mechanical reference: https://www.youtube.com/@bRd3D ; example link https://www.youtube.com/watch?v=d7RfB4Gf02Y . This session could not play the original video (channel page exposed only boilerplate; video open failed). Close-up mechanism views, settled comparisons, and physical-to-diagram handoffs are therefore project design choices for this requested reference direction, not claimed observations of bRd's exact methods. Verify actual excerpts before making more specific creator claims.

Decision: strengthen existing Director, renderer, narration and reviewer instructions rather than add agents or a second storyboard/schema. Existing `state_change`/`focus` carry causal evidence and phrase anchors. `sec` from the audio helper includes `min_sec` padding, so timing review must distinguish speech from purposeful pause. Reviewer now distinguishes educational inspection from deterministic media PASS.

Tradeoff: these checks require judgment and real excerpts; markdown/frontmatter validation cannot prove teaching quality. No universal video length, palette, camera pattern or creator-parity score is imposed. Re-evaluate on the next actual production; the previous pilot is not retroactively improved or reapproved by these edits.

Compatibility finding: the existing top-level `version` frontmatter is rejected by Codex skill-creator's `quick_validate.py`. Updated skills retain the version under supported `metadata.version`; no version reader was found in bundle Python scripts. The project venv lacks PyYAML, so the skill-format checker uses the already-installed system PyYAML without adding a project dependency. Bundle wiring still uses `uv run`.

Validation: Codex quick_validate passed for all five changed skills; the review YAML parsed with educational status defaulting to incomplete; `uv run python scripts/validate_codex_setup.py` passed for 10 agent configs; `git diff --check` passed. These are format/wiring checks, not a rendered-video demonstration of better teaching. No new render, behavioral agent evaluation, or upload was performed in this update.

Follow-up from actual pilot re-review: plans and poses can come from one trace yet show different source times. Director/Manim/Blender now require time coherence or explicit historical-snapshot labeling. The moving-obstacle revision uses the latter because it preserves the encoded playback and makes its existing presentation truthful. This addresses the tested timing ambiguity; it does not reconstruct missing candidate-cost evidence.

## Deeper mechanism study (2026-10-06)

`research/channel_craft_2026_10/STUDY.md` records eight selected bRd/3Blue1BrownKR works, actual storyboard inspection and 1080p audiovisual excerpts. The new route succeeded where earlier web access was limited; this does not retrospectively establish normal-speed listening. Production references now connect faithful components, one sourced example, notation and recorded response. Reviewer comparison distinguishes mechanism depth, correspondence, visual craft, rhythm/voice and transfer instead of deriving creator parity from technical gates.

## R11 gap-driven production repair

R11 added a faithful static part inset and wheel command equations, but did not yet show the part operating or move source quantities into equation terms. The production references now specify trace-driven articulation with observable phase and operand-level correspondence animation. These are requested craft targets; normal-speed playback and first-view learner evidence remain separate. See `pilots/05_moving_obstacle/revision_11/COMPARISON.md` locally for the baseline finding.
