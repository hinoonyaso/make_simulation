# V11.1 preview review

This is a one-pass review of generated, silent technical previews. The project Render Reviewer skill's deterministic frame extractor sampled each preview around beats; actual spoken-audio review is not applicable because these renders have no audio. Whole-video normal-speed motion review and novice comprehension were not available, so educational review status remains **incomplete**. The claim here is limited to sampled image evidence plus successful full-decode validation.

| Topic | MP4 | Duration | Technical | Sample review |
|---|---|---:|---|---|
| Quantization | `/tmp/v11_quantization_final_smoke/quantization/preview.mp4` | 12.00 s | 960×540, H.264, 30 fps, full decode PASS | Range, scale/zero point, integer code and restored markers visible. No blocker/high in sampled frames. |
| Positive-only asymmetric quantization | `/tmp/v11_quant_positive/quantization/preview.mp4` | 12.00 s | 960×540, H.264, 30 fps, full decode PASS | Trace uses `[1, 2]`, scale `2/255`, zero point `0`, codes `[128, 255]`; the code markers overlap their corresponding calibrated real values as expected. |
| NMS | `/tmp/v11_nms_final_smoke/nms/preview.mp4` | 12.00 s | 960×540, H.264, 30 fps, full decode PASS | Candidate boxes persist; single IoU decision label updates by recorded comparison; kept IDs visible. No blocker/high in sampled frames. |
| MCU PID | `/tmp/v11_pid_final_smoke/mcu_pid/preview.mp4` | 12.00 s | 960×540, H.264, 30 fps, full decode PASS | Sampled motor response is drawn progressively against target, with PWM stage after. No blocker/high in sampled frames. |
| Self-Attention | `/tmp/v11_attention_final/self_attention/preview.mp4` | 15.97 s | 960×540, H.264, 30 fps, full decode PASS | Q/K score matrix, scaled scores, softmax weights, V vectors and output correspondences visible. Matrix transitions are readable at sampled settled states. No blocker/high in sampled frames. |

The first NMS frame review exposed an overlapping multi-label comparison layout; the final frame review showed a single trace-ordered label. The first Self-Attention review exposed unreadable title/numeral interpolation lasting too long during matrix transforms; the transform was shortened, then sampled again at 5, 7, 9 and 11 seconds. The first Quantization review exposed missing quantized/restored objects because opacity was set to zero before `FadeIn`; the final preview shows the code markers and error result. These defects were fixed and regenerated before this review record.

Blocker/high count in reviewed sampled frames: **0**. This is a technical frame review, not a claim of full video pacing approval, novice learning validation, narrated-video quality or reference-creator parity.
