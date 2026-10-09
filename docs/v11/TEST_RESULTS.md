# V11.1 validation results

Run from `/home/sang/make_simulation` on 2026-10-09. These are local results; GitHub Actions has not run.

| Check | Status | Evidence |
|---|---|---|
| Full unit/regression suite | PASS | `uv run python -m unittest discover -s tests -v` — 48 tests |
| Quantization one-sided/constant/INT4/INT8/per-channel regression | PASS | `tests.test_v11_mechanism`; affine reconstruction and tampered-code rejection |
| Korean aliases / ambiguity | PASS | Korean mappings resolve; generic `attention` prints 3 choices and does not choose one |
| NMS and PID stored trace integrity | PASS | tampered IoU and plant samples rejected; PID validates controller equation and encoder values |
| Self-Attention arithmetic and replay validation | PASS | Q/K/V, scaling, causal mask, row softmax and outputs; corrupted output rejected by both adapter and manifest validator |
| Environment preflight and safe archive pipeline | PASS | candidates stay not-ready; path traversal, symlink and expanded-size tests rejected; mocked HTTPS fetch verifies hash, atomic extraction and cache reuse |
| V10 AI trace and V9-compatible manifest | PASS | `scripts/validate_ai_trace.py .../ai_trace.json`; `validate_visual_manifest.py .../visual_manifest.json` |
| Manim style gate | PASS | `uv run python scripts/check_scene_style.py core/mechanism/manim_scene.py` |
| Python compile | PASS | `uv run python -m compileall -q core/ai-mechanism core/mechanism core/visual-assets core/simulation scripts/produce_video.py scripts/manage_assets.py` |
| Quantization preview | PASS | `/tmp/v11_quantization_final_smoke/quantization/preview.mp4`, 12.00s, 960×540, H.264, 30fps, silent, full decode |
| Positive-only asymmetric quantization preview | PASS | `/tmp/v11_quant_positive/quantization/preview.mp4`, 12.00s, 960×540, H.264, 30fps, silent, full decode; trace: scale `2/255`, zero point `0`, codes `128` and `255` |
| NMS preview | PASS | `/tmp/v11_nms_final_smoke/nms/preview.mp4`, 12.00s, 960×540, H.264, 30fps, silent, full decode |
| MCU PID preview | PASS | `/tmp/v11_pid_final_smoke/mcu_pid/preview.mp4`, 12.00s, 960×540, H.264, 30fps, silent, full decode |
| Self-Attention preview | PASS | `/tmp/v11_attention_final/self_attention/preview.mp4`, 15.97s, 960×540, H.264, 30fps, silent, full decode |
| Sampled render frame review | PASS, scoped | Render Reviewer frame extraction + real frame inspection; zero blocker/high in inspected frames. Whole-video motion pacing and novice comprehension remain incomplete. |
| Clearpath/Gazebo environment load | BLOCKED | `ros2` and `gz` are absent |
| ManiSkill/SAPIEN environment load/render | BLOCKED | `sapien` absent; project matrix lists WSL rendering unsupported; GPU access blocked |
| robosuite Lift load | BLOCKED | robosuite absent; `uv run --with robosuite==1.5.2 ...` failed on PyPI DNS before installation |
| Environment downloads/dependency closure | NOT_RUN | no source candidates yet satisfy revision/hash/size/model license gate |
| YOLO model inference | NOT_RUN | no detector adapter or pinned model; NMS preview remains synthetic |
| Narrated full production / delivery | NOT_RUN | common mechanism CLI remains silent technical render |
| Remote CI | NOT_RUN | workflow definitions updated but not triggered |

The active V9/V10 tests and checked-in trace checks passed. This suite result does not convert simulator, model, full production or whole-video review blockers into passes.
