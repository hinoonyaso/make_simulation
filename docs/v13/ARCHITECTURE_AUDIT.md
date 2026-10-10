# V13 Architecture Audit and Decisions

## Starting point and Git boundary

- V13 work branch: `v13-education-first`.
- Start commit: local V12.1 final fix `c9bc690`, whose parent is the open PR #2 head `5a6ba27`.
- Remote PR #2 is still open and unmerged; its base was `main` at `2af957f`. V13 work is local and has not been pushed or merged.
- The working tree already contained untracked earlier pilot/media folders. They were left untouched.

## Existing production architecture

| Stage | Existing implementation | Audit finding |
|---|---|---|
| Director | `core/robotics-ai-visual-director-skill/templates/visual_manifest.json` and `validate_visual_manifest.py` | The V9 manifest owns narration, beat duration, object identity, one state change, focus, renderer tool and evidence. Keep it the sole beat source. |
| Execution evidence | `core/mechanism/adapters/`, `trace_contract.py`, `execution_cache.py`, V12 engineering adapters | Existing deterministic calculations and trace validation should remain topic adapters; concept lessons do not require an execution trace. |
| Storyboard | `core/mechanism/storyboard.py` | `_phases()` is topic keyed and does not support arbitrary education topics. V13 planning therefore consumes author-supplied, validated V9 beats rather than expanding the topic switch. |
| Timeline | `core/mechanism/timeline.py` (`mechanism-timeline/v1`) | Integer-frame timeline accepts the V9 beat contract and is reused directly at 30 fps. |
| Render routing | `scripts/produce_video.py`, `core/mechanism/renderer_routing.py`, `core/mechanism/renderer.py` | Existing renderer registry is executable-topic oriented; `illustration` mode is intentionally rejected. New lesson CLI is isolated to avoid changing existing topic routes. |
| Narration | `core/narration/prepare_audio.py` | Existing per-beat Edge TTS and forced-alignment caption workflow is reusable; no fresh audio is sent by the plan-only path. |
| Rendering kits | `core/manim-robotics-education-skill/templates/manim_kit.py`; `core/blender-robotics-simulation-skill/templates/scene_kit.py` and `studio_utils.py` | Reuse Manim theme and renderer discovery/launch conventions. Educational blueprint registry is metadata and routes to general primitives; it is not a second story format. |
| Final validation | `scripts/validate_delivery.py`, `core/render-reviewer-skill` | Full decode and frame/fps checks are available. Educational review still requires watching the complete render and documenting learning tests separately. |

### Reused and newly added modules

Reused: V9 manifest schema and Director validator, V12 timeline builder, Manim kit theme, Blender runtime discovery and V9 narration entry point. New: import-light `core/education` lesson validation/planning/evidence/solver contract, blueprint registry, shared Manim/Blender primitive packages, `scripts/produce_lesson.py`, plus a bearing pilot. Existing topic execution and rendering paths were not rewritten.

## Design decisions

1. **One beat source:** a lesson input carries the lesson metadata and `beats`; the planner emits the familiar V9 `visual_manifest.json`. The planner does not create a second storyboard or shot list. `phase_id` and educational blueprint/evidence metadata extend each beat without replacing its V9 fields.
2. **Three lesson modes are beat aware:** concept, mathematical and computed engineering modes are explicit in lesson metadata; each beat records evidence class. Concept-only planning does not load or invoke a solver. Computed mode requires an explicitly named solver, and a solver declaration without a trace remains `PLANNED` rather than silently fabricating results.
3. **Conservative solver status:** the plugin contract and status enum are infrastructure only. V13 does not claim PyBaMM, FEMM/Elmer, CalculiX or OpenFOAM support. Existing SciPy/SymPy, motulator and MuJoCo adapters remain in their current execution paths.
4. **Bearing geometry:** the selected type is a single-row deep-groove ball bearing. Rings, balls and cage are procedural teaching geometry; dimensions and ball motion are illustrative. The animation has no contact solver and does not measure friction, force or deformation. No external CAD is downloaded.
5. **Renderer selection:** each V9 beat's `tool` chooses Blender (`B`) or Manim (`M`); the current pilot uses Blender for assembly/motion/load-path and Manim for comparison/limitations. The shared timeline determines cuts, so presentation time does not drift between renderers.
6. **Narration/privacy boundary:** the default preview is silent and includes sentence-level VTT beat captions. `--with-tts` reuses the existing Edge TTS + Whisper stages and sends only the lesson narration text to the configured service; this flag is opt-in. A silent render is never reported as a narrated final.

## Solver roadmap and environment strategy

| Milestone | Domain | Planned validation | Environment boundary |
|---|---|---|---|
| V13.1 PyBaMM | Battery discharge at two rates; voltage/SOC trace and validation | Isolated optional Python environment; record model, parameters, units, provenance and solver version | Do not add to base dependencies; check Python/OS and example compatibility before installation |
| V13.2 FEMM or Elmer | Motor cross-section field map and flux visualization | Compare against a documented example and boundary conditions; validate mesh/result exports | Compare platform support and license first; isolate native dependencies and GUI/kernel needs |
| V13.3 CalculiX | Small bracket displacement/stress case | Mesh convergence/checks, units and boundary conditions; verify result files and benchmark values | Optional isolated solver image/environment; keep small cases outside normal PR CI |
| V13.4 OpenFOAM | Small verified flow case | Mesh and boundary-condition checks; compare against reference values; export velocity/pressure | Separate system environment/container; document WSL support, runtime, disk and license provenance |

All future adapters should implement environment check, input validation, execution, result validation and visual-data export. Solver result metadata must preserve solver/version, model/input, units, assumptions, boundary conditions, provenance, status, output paths, validation summary and limitations. A package being installed is at most `ENVIRONMENT_CHECKED`; rendering and production readiness require their own evidence.

## Current V13 evidence and limits

- `examples/education/bearing.json` validates as concept-only and produces a V12 30-fps timeline without a solver or trace.
- The repo's Blender discovery helper resolves Windows Blender 5.2 in this WSL workspace; the actual bearing render is a separate required runtime check.
- No learner study has been run. Educational effectiveness remains unverified until beginner viewers are tested.
- TTS, full narration alignment and final audio mux are opt-in and require an explicit `--with-tts` invocation for this new lesson.
- CI uses a short Manim-only smoke lesson; Blender runtime rendering is checked locally and is not claimed by Ubuntu CI.
