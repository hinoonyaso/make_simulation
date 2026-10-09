# Codex orchestration — Robotics / AI Visual Video V9 Source-Informed Lite

Read `ROUTING.md` first. Optimize **visual quality first** (bar: `pilots/01_teb_reference`), then tokens.

Ignore `_backup_*/`, `CHANGELOG_V7.md`, `CHANGELOG_V8*.md`: superseded history, never current rules. Each `topics/<NN>_*` is a finished episode; reuse its ideas, not its per-topic scripts (shared versions live in `core/` and `scripts/`).

## Core rules
1. `director` owns story + narration timing + visual state transitions in one compact manifest.
2. Each beat has one persistent object, one meaningful state change, and one attention target. Do not design slide decks.
3. For simulation/data-driven visuals, generate or load one shared trace/config first. Manim and Blender must not independently invent values.
4. For V11 robotics/AI mechanisms, inspect `scripts/inspect_capabilities.py` and the Mechanism Registry before routing; resolve Korean/English aliases, require a unique canonical topic, then check support level and implementation status. Do not route unsupported topics through RAG or a generic slide path.
5. Manim/Blender use existing production primitives before new infrastructure. Repeated patterns become helpers, not longer prompts.
6. Asset lookup, trace validation, manifest validation, and sequence staging are deterministic scripts; do not spend LLM calls on them.
7. Reviewer runs only after a real preview; one pass by default, up to three targeted passes for flagship shots. Inspect the central cause/comparison/consequence and narration timing, not only technical defects. Missing decisive explanation is high severity. Patch blocker/high issues for acceptance; requested craft polishing may also address documented observations. Report incomplete inspection separately from PASS.
8. Astra is escalation, never default. Use hero agents for flagship scenes, hard central defects, or failed normal patches.
9. Resolve runs after visual approval; YouTube only when explicitly requested.
10. Final delivery >=1920x1080; prefer 2560x1440 for line/text-heavy masters when practical.
11. No persistent dashboard chrome, SCENE badges, opaque subtitle boxes, decorative zooms, or tiny secondary text by default.
12. Pass compact artifacts rather than conversation history.

## Source-informed production rules
- Iterate via cheap previews before final render.
- Preserve object identity and show state transitions continuously.
- Separate computation/data generation from rendering when a real algorithm/model/simulation exists.
- For dense networks/attention/graphs, display a thresholded/top-k subset first; reveal more only when it teaches something.
- In Blender, use reusable stateful objects/assets and frame the subject automatically from bounds before manual camera tweaking.
- Never copy scene code from reference creators; implement the underlying general technique in this project's own helpers.

For full narrated explainers, validate the hardest inference in a cheap moving excerpt with measured narration before costly full rendering. Use the existing manifest IDs. Final educational acceptance includes actual motion and voice inspection when relevant; sampled frames and signal checks alone leave those checks incomplete.

For this user’s robotics episodes where physical motion/contact is relevant, retain the discovery explanation and use an actual capable physics engine for Blender setup/consequence. Share the same run with Manim; keep reference plans distinct from physical response. Do not relabel old trace playback or prescribed robot poses as physical simulation. Verify run provenance and physical checks separately from schema/media validation.

## V11 mechanism runs

- Use `scripts/produce_video.py` only after checking the Mechanism Registry. Ready topics support `--mode executable`; validated traces can use `--mode replay --trace <path>` where the registry schema matches.
- Each invocation writes to `output/runs/<topic>-<run-id>/`. The run ID includes input/config/trace, renderer mode, code fingerprint, adapter contract, and model provenance. Completed matching media is reused only after full decode; failed/colliding run folders stay intact. `--force` creates a timestamped sibling; it never overwrites.
- Replay must validate the schema, topic or legacy model identity, and the topic-specific equations before storyboard or render. Do not execute the mechanism again to replace replayed values.
- The storyboard is derived from trace content. Estimated visual timing and measured narration timing are distinct. `--narration-duration` distributes an existing measured duration; it does not generate audio.
- Production reports separate technical decode from visual and educational review. Silent preview decode does not imply audio, caption, reviewer, learner, 3D mesh, or L4 completion.
- Existing robotics/AI assets and traces are preferred. Do not change old pilot outputs to make run management pass. Do not acquire new maps/worlds in this V11.2 scope.

## V11.3 integration notes

- The RAG dispatcher selects `preview.media` or `final.media` from the matching successful subreport, then verifies the file, exact requested dimensions, 30 fps and full decode before copying it.
- Every generated common storyboard beat has a `phase_id`; the Manim scene rejects missing, duplicate, unused or unmapped phases. Dynamic NMS can omit IoU comparison when the validated trace has no selected candidates, but must still show its final result.
- Cache reuse requires the expected in-run output path, identity, preview/final render spec, recorded media metadata, matching media SHA-256 and a fresh full decode. Fingerprints cover render-input code paths rather than the Git commit/README.
- `object_detection` is actual, local YOLO11n inference only with the verified checkpoint hash. It is separate from synthetic `nms`; replay verifies the source image hash and performs no inference. Ultralytics is optional and its runtime hooks run in a child process.
- `robot_kinematics --render blender` uses the existing H1 MJCF and Blender trace pilot. The exporter checks source hash, joint order/limits and FK; Blender renders interpolated MuJoCo states and does not integrate physics again. Set `BLENDER_BIN` when automatic executable discovery does not work; explicit Blender failure is never downgraded to Manim.
- Render Integration CI remains manual. A local PASS is not a remote Actions PASS; report remote dispatch as NOT_RUN when no dispatch credential/UI is available.

## V11.4 renderer routing and timeline

- Route from the requested visual goal, trace evidence, renderer capabilities, local assets, and a process-level runtime preflight. Inspect with `uv run python scripts/inspect_capabilities.py --topic <topic> --preflight`.
- H1 `motion_3d` requires Blender; numerical/comparative H1 analysis uses Manim. An explicit Blender request stays BLOCKED on failure. Automatic 2D fallback must report its feature loss.
- Renderers consume the run's `mechanism-timeline/v1`. Integer frame ranges define presentation boundaries; source trace time remains a separate mapping.
- YOLO phases consume the timeline ranges. RAG keeps its four phase IDs, and the Three.js projection replaces the embedding phase's exact frame range.
- Run identity includes effective renderer, goal, timeline, renderer version, relevant code fingerprint and model/asset hash. A Git commit change by itself is not a render-input change.
- Full decode and frame count do not prove motion continuity or educational review; report those checks separately.
