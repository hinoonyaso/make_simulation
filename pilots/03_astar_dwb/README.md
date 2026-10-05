# Pilot 03 — A* global path and DWB local choice

Final episode: `output/astar_dwb_ko.mp4` (1920×1080, 30 fps, Korean narration, sentence-aligned Korean captions, 76.90 s).

The episode connects two roles: A* proposes a route through a grid; a DWB-style local model compares short velocity rollouts and applies only the next 0.2 s before reevaluating. The final narration and closing card state that these are **separate trace-backed teaching examples**, and that the DWB-style example is **not a Nav2 DWB execution**.

## Decision record

- **Use the A* source trace and DWB source trace as separate examples.** The available A* trace is a 12×9 cell grid from topic 07. The DWB candidate trace comes from a metric corridor example in topic 09. Their maps and coordinate systems differ, so presenting one as the other's single continuous run would invent a correspondence. Topic 08 has an integrated navigation example, but its local controller is not the topic 09 DWB-style selection being explained. The video labels the handoff as separate examples, and uses each source only for its own values.
- **Keep calculation in one continuous Manim scene; reuse the established studio clips for physical context.** The grid, candidate rollouts, selected command and 0.2 s update are clearest in a stable top-down animation. The opening and execution beat reuse already-rendered TurtleBot3/corridor/drum shots from Pilot 02 to retain the bright studio look without changing that finished episode. No Blender scene was needed for this conceptual bridge; no kit file was modified.
- **A* example:** source `topics/07_astar/output/trace.json`, `astar` result only. The path has 17 cells / 16 grid steps and the recorded cost is 16. **DWB example:** source `topics/09_dwb_teb/output/trace.json`, `hero.dwb` records only. It contains 119 candidates, 80 valid candidates, selected score 7.334952691, command `v=0.53 m/s`, `ω=0.375 rad/s`, and a 2 s prediction. The next 0.2 s state is read from that selected candidate's trajectory. These values describe the educational source model, not Nav2 defaults or an executed Nav2 plugin.
- **Trace boundary:** `extract_traces.py` reads both topic outputs without writing to `topics/`. It copies only A* result fields and DWB hero candidate fields into `data/astar_trace.json` and `data/dwb_trace.json`, each validated with `core/shared-data/validate_trace.py`. The separately rendered physical clips are visual context, not a claim that both source traces came from that footage.

## Director and local helper notes

- The Director manifest is the single beat contract. Narration timing is set from measured audio; captions use the narration alignment output. Story transitions retain the grid, candidate traces and robot identity until their role changes.
- The Director skill defines a single trace per computed beat, but does not prescribe how to disclose a conceptual bridge between two independent traces. This episode marks the independence both in narration and on screen. A reusable manifest convention for multi-trace conceptual comparisons is a candidate for the Director skill.
- TTS originally read the literal spelling cue `A 별표` aloud. Both narration entries now use `에이스타`, while their viewer captions retain the standard `A*` notation. This keeps pronunciation natural without changing the written technical term.
- The kit supplies `turtlebot3_top`, `world_window`, palette and beat timing, but no grid-route renderer or velocity-rollout comparison primitive. `grid_group()` and `rollout()` are pilot-local helpers in `manim_shot.py`; if reused in another episode, consider moving these general forms to `manim_kit.py`. The kit was not changed.
- `edge-tts` required network access to generate narration. Manim reports that SoX is absent in this environment; this scene does not use Manim voiceover/SoX, and rendering completed. Whisper forced alignment produced sentence-level caption cues.
- The first reviewer pass found three high visual defects: a Korean title glyph transform, an overlapping A*→DWB transition, and a label collision. The scene now replaces Korean titles by sequencing fade-out/fade-in and explicitly removes outgoing objects after transitions. The visual targeted follow-up passed with no blocker/high defects. After the pronunciation correction and rerender, reviewer rechecked the final frames and again passed with zero blocker/high defects.

## Acceptance gates

- `validate_visual_manifest.py --require-media`: PASS.
- `scripts/check_scene_style.py pilots/03_astar_dwb`: PASS (Manim scene; no Blender scene was required).
- `scripts/validate_delivery.py --require-audio --fps 30 --audio-manifest ... --caption-timing ... --full-decode`: PASS; 1920×1080 H.264, 30 fps, 76.90 s, one audio stream, 12 timed caption cues, complete decode.
- Render-reviewer: final pronunciation-fix review PASS; blocker/high defects 0.
- Topic outputs remain read-only. Studio footage is reused from the completed Pilot 02 renders.
- YouTube upload: [watch corrected video `AbGKm_WOv64`](https://youtu.be/AbGKm_WOv64). Remote status confirmed `public`, processing `succeeded`, Korean caption track `serving`, `madeForKids=false`. The superseded pronunciation version `ZMfmJeSVgy4` was deleted after replacement verification. Its prior local receipt is preserved as `publish/receipt_superseded.json`. No custom thumbnail was attached.

## Reproduction

From `/home/sang/make_simulation`:

```bash
uv run python pilots/03_astar_dwb/extract_traces.py
uv run python core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py pilots/03_astar_dwb/visual_manifest.json
uv run python core/narration/prepare_audio.py tts pilots/03_astar_dwb/visual_manifest.json
uv run python core/narration/prepare_audio.py captions pilots/03_astar_dwb/visual_manifest.json
uv run manim -qh --fps 30 --disable_caching --media_dir pilots/03_astar_dwb/output/manim pilots/03_astar_dwb/manim_shot.py AStarDWB
uv run python pilots/03_astar_dwb/assemble.py
```
