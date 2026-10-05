# Codex orchestration — Robotics / AI Visual Video V9 Source-Informed Lite

Read `ROUTING.md` first. Optimize **visual quality first** (bar: `pilots/01_teb_reference`), then tokens.

Ignore `_backup_*/`, `CHANGELOG_V7.md`, `CHANGELOG_V8*.md`: superseded history, never current rules. Each `topics/<NN>_*` is a finished episode; reuse its ideas, not its per-topic scripts (shared versions live in `core/` and `scripts/`).

## Core rules
1. `director` owns story + narration timing + visual state transitions in one compact manifest.
2. Each beat has one persistent object, one meaningful state change, and one attention target. Do not design slide decks.
3. For simulation/data-driven visuals, generate or load one shared trace/config first. Manim and Blender must not independently invent values.
4. Manim/Blender use existing production primitives before new infrastructure. Repeated patterns become helpers, not longer prompts.
5. Asset lookup, trace validation, manifest validation, and sequence staging are deterministic scripts; do not spend LLM calls on them.
6. Reviewer runs only after a real preview; one pass by default, up to three targeted passes for flagship shots. Inspect the central cause/comparison/consequence and narration timing, not only technical defects. Missing decisive explanation is high severity. Patch blocker/high issues for acceptance; requested craft polishing may also address documented observations. Report incomplete inspection separately from PASS.
7. Astra is escalation, never default. Use hero agents for flagship scenes, hard central defects, or failed normal patches.
8. Resolve runs after visual approval; YouTube only when explicitly requested.
9. Final delivery >=1920x1080; prefer 2560x1440 for line/text-heavy masters when practical.
10. No persistent dashboard chrome, SCENE badges, opaque subtitle boxes, decorative zooms, or tiny secondary text by default.
11. Pass compact artifacts rather than conversation history.

## Source-informed production rules
- Iterate via cheap previews before final render.
- Preserve object identity and show state transitions continuously.
- Separate computation/data generation from rendering when a real algorithm/model/simulation exists.
- For dense networks/attention/graphs, display a thresholded/top-k subset first; reveal more only when it teaches something.
- In Blender, use reusable stateful objects/assets and frame the subject automatically from bounds before manual camera tweaking.
- Never copy scene code from reference creators; implement the underlying general technique in this project's own helpers.

For full narrated explainers, validate the hardest inference in a cheap moving excerpt with measured narration before costly full rendering. Use the existing manifest IDs. Final educational acceptance includes actual motion and voice inspection when relevant; sampled frames and signal checks alone leave those checks incomplete.

For this user’s robotics episodes where physical motion/contact is relevant, retain the discovery explanation and use an actual capable physics engine for Blender setup/consequence. Share the same run with Manim; keep reference plans distinct from physical response. Do not relabel old trace playback or prescribed robot poses as physical simulation. Verify run provenance and physical checks separately from schema/media validation.
