# V11.4 Unified Timeline Contract

Schema: `mechanism-timeline/v1`, implemented in `core/mechanism/timeline.py`.

## Time model

- **Source trace time** is the timestamp attached to recorded simulator samples or events.
- **Presentation time** is the explanatory duration allocated to a storyboard phase.
- **Video time** is the integer frame index divided by the contract FPS.
- **Simulation time** remains the source engine's recorded interval. A longer presentation does not imply a longer simulation.

The contract stores `fps`, `total_frames`, `total_duration_sec`, optional `source_range_sec`, and ordered `phases`. Each phase has a unique `phase_id`, half-open `[presentation_start_frame, presentation_end_frame)` range, optional source start/end, `playback_mode`, and `visual_goal`. Rounding is performed on cumulative phase boundaries to avoid gaps and overlaps. The saved timeline digest is stable and excludes its own digest field.

Validation rejects malformed FPS, invalid/empty durations, duplicate or reordered phases, gaps/overlaps, incomplete or out-of-range source mappings, unsupported playback modes and mismatched total duration. `source_time_for_frame()` applies the phase's hold, analysis hold, forward interpolation or explicit replay semantics.

## Renderer adapters

- Common Manim uses each phase's frame count and rejects a transition longer than its phase.
- YOLO wraps all four existing phases in exact frame boundaries; overrun and missing final frames are errors.
- H1 export maps each presentation frame to the corresponding recorded source time, interpolates qpos and recomputes FK; its scene records source and presentation duration/speed.
- RAG preserves its four V10 IDs. Manim gets durations derived from frame ranges; Three.js occupies exactly the `embeddings` range. The renderer report records the timeline digest and frame interval.

All final artifacts are checked against timeline `total_frames`; FPS/duration and decoded frame count are reported separately from visual continuity review.
