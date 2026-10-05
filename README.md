# Robotics / AI Visual Video V9 — Source-Informed Lite

High-quality, low-token Codex pipeline for robotics/AI educational videos.

Default route: `Director -> optional shared trace -> Manim/Blender -> one real-render review -> Resolve -> optional YouTube`.

V9 keeps V8 Lite's small agent graph, but strengthens **production primitives** using general patterns found in public source repositories from 3Blue1Brown, Welch Labs, Reducible, Primer, and Sebastian Lague. No creator scene code is copied. `SOURCE_PATTERNS.md` is provenance only and should not be preloaded.

Key upgrades:
- state-transition storytelling instead of slide replacement;
- shared computed traces for data/model/simulation visuals;
- selective-density helpers for networks/attention/graphs;
- reusable stateful Blender objects + `.blend` assets;
- automatic camera framing from object bounds;
- deterministic manifest/trace/delivery gates;
- 1080p minimum, 1440p preferred for line/text-heavy masters.

Start with `ROUTING.md`.

## Explanation craft

Director now plans the visible cause, decisive comparison/constraint, and consequence of the central question. Manim/Blender expose that evidence with purposeful framing and phrase timing; Reviewer reports educational inspection separately from technical PASS. Narration guidance includes deliberate pauses and Korean terminology pronunciation. The next real preview must demonstrate these changes; existing published videos are unchanged. Reference sources, access limits, decisions, and tradeoffs are in [SOURCE_PATTERNS.md](SOURCE_PATTERNS.md#2026-10-explanation-craft-update-user-selected-references).

## Discovery and critical-preview update

Full explainers now validate their hardest inference as a short moving excerpt with measured narration before full rendering. Director plans expectation, visible test, mechanism and supported transfer in existing manifest fields. Reviewer records interpretation before consulting source data, and separates comprehension, motion and voice inspection. Unavailable playback/listening remains incomplete, even with technical PASS. This preserves the single-manifest interface and uses local implementations when shared kits are protected.

The change addresses observed pilot limitations: detached 3D/2D presentation, insufficiently tested inference, and frame/timing checks being mistaken for full audio/motion acceptance. It does not establish creator parity. Tradeoff: an extra small preview/listening pass before the expensive render; it can reuse previously approved equivalent media. Shared kits, original episodes and existing video outputs are not changed by this skill update. Behavioral effectiveness still requires the next real production and viewer feedback.

Validation for this update: five skill folders pass `skill-creator/scripts/quick_validate.py`; Director/Reviewer TOML and review-template YAML parse; `scripts/validate_codex_setup.py` passes all 10 agent configurations; `git diff --check` passes. Skill validation used system Python because the project environment lacks PyYAML; no dependency was added. These checks establish format and wiring, not the educational quality of a future video.

## Physics-backed robotics production

The user's selected next direction preserves the current discovery explanation and adds physics-backed Blender setup/consequence. A capable installed engine computes actuation/contact first; Manim and Blender then explain/render the same recorded run. Blender may be the renderer for another simulator. Reference plans and actual body trajectories remain separate; pose replay, kinematic integration and contact-resolving physics are explicitly distinguished.

The detailed run contract is in [Blender evidence rules](core/blender-robotics-simulation-skill/references/evidence.md). Existing manifest evidence enums and V9 schema are unchanged. Physics acceptance now has a separate review field: solver provenance and relevant physical checks cannot be replaced by realistic rendering or schema PASS. Shared kits and finished episodes are untouched. This update supplies production/review instructions; it does not execute or validate a new physical simulation. Engine choice, model fidelity and solver stability still require the next episode's environment inspection and experiment.

Physics skill update validation: four affected skill folders pass `quick_validate.py`; updated agent TOML and review YAML parse; `validate_codex_setup.py` passes all 10 agent configs; `git diff --check` passes. Cross-skill evidence links were corrected to their actual bundle paths after the wiring check identified unresolved references. These checks validate instructions/configuration only, not a physics engine or runtime experiment.
