# V11.2 sampled render review

Review pass: one. This is a scoped still-frame inspection of real rendered MP4s, not a full audiovisual or learner-comprehension acceptance.

## Technical gate

`uv run python scripts/check_scene_style.py core/mechanism/manim_scene.py` exits 0 and emits the heuristic warning `FadeOut x17 > continuity primitives x8`. The warning remains open for motion inspection. All sampled preview MP4s separately passed visual-manifest validation and `scripts/validate_delivery.py --min-width 540 --min-height 540 --fps 30 --full-decode`.

## Sampled frames and findings

| Preview | Inspected time(s) | Visible evidence | Blocker/high |
|---|---:|---|---|
| NMS confidence rejection | 8s | Confidence pass/reject state and candidate count are legible. | None observed in still |
| NMS empty boundary | 5s | Empty input is represented as no candidates and no kept boxes. | None observed in still |
| MCU PID | 8s, 12s | Encoder/PWM markers are distinct; first-sample P/I/D equation panel is explicitly labeled. | None observed in still |
| Self-Attention | 2s, 16s, 25s | Input/projection and score-matrix states are readable at sampled moments. | None observed in still |
| Quantization | 18s | Weight/activation values, integer codes and scale/zero-point values are visually separated. | None observed in still |

The sampled frames support only those local visual observations. They do not show continuous transitions between states or establish that the full central explanation answers a first-time viewer's question. H1 and RAG had technical preview/decode checks, but no sampled-frame review is claimed for them in this pass.

## Acceptance status

- Sampled-frame visual inspection: **completed for the five previews listed above**; no blocker/high defect was visible in the inspected stills.
- Motion continuity and normal-speed pacing: **incomplete**; no full-video motion playback review was performed.
- Audio/narration: **not applicable to these silent previews**; no audio was generated or listened to.
- Learner comprehension: **not assessed**; no human novice first-view study was run.
- Physics: **not accepted by this review**. The H1 preview is a trace visualization and not a Blender mesh/solver visual review.
- Overall educational review: **incomplete**, not PASS.

## Follow-up: actual H1 Blender and YOLO outputs (2026-10-09)

### YOLO image trace

Reviewed the final 12.70-second silent Manim output at 3, 6, 10 and 12 seconds. The first drafts had candidate names drawn across the image and previous-stage labels lingering into the NMS/final state. Those issues were fixed before this review: the rejection is identified in the side panel, NMS has a clean dedicated stage, and final boxes use numbered markers mapped to a score list. The final preview shows the input image, confidence decision, one actual same-class IoU suppression and five model-matched final detections. No blocker/high visual defect was apparent in the sampled final frames. This is sampled-frame review only; it does not establish motion continuity or lesson comprehension.

### H1 Blender mesh excerpt

The rendered asset `/tmp/v112_h1_blender/h1_trace_blender.mp4` was produced with Blender 5.2.1 and actual imported MuJoCo H1 mesh assets. Frames at 0, 1 and 2 seconds were inspected. The controlled left arm is blue and moves with the trace; the other arm remains in its recorded hold pose. A shared studio floor, materials, camera and lighting render successfully. The graph and robot are driven by the same stored trace. No blocker/high rendering defect was seen in the sampled stills. The excerpt is only 2.03 seconds long, so this is technical render evidence, not a full motion/pacing review or evidence of Blender physics execution.

The two excerpts are silent. Audio, narration, caption synchronization, first-view learner comprehension, and full normal-speed educational review remain unassessed.
