# V11 test results

This file records only commands actually run in the current working tree. Update the status after the remaining test/render pass. Never treat a preview as final delivery.

| Check | Status | Evidence |
|---|---|---|
| Full repository unit suite | PASS | `uv run python -m unittest discover -s tests -v` — 36 tests |
| New V11 mechanism adapter tests | PASS | Included in full suite: 6 tests across registry, envelope, quantization, NMS and PID |
| OpenMANIPULATOR-X URDF/mesh validation | PASS | `uv run python scripts/manage_assets.py validate --asset blender.open_manipulator_x.v1`; see asset report |
| OpenMANIPULATOR-X local fetch/hash check | PASS | `uv run python scripts/manage_assets.py fetch --asset blender.open_manipulator_x.v1` (already present; no download) |
| Scene style | PASS | `uv run python scripts/check_scene_style.py core/mechanism/manim_scene.py`; same check passed for `pilots/v10_rag_poc/rag_mechanism_scene.py` |
| Quantization preview | PASS | 12.0s, 960×540, 30fps, H.264, no audio; full decode passed |
| Weight+activation quantization preview | PASS | Supplied distinct tensors; separate numerical results and visual error labels; 12.0s, 960×54030 full decode passed |
| NMS preview | PASS | 12.0s, 960×540, 30fps, H.264, no audio; full decode passed |
| MCU PID preview | PASS | 12.0s, 960×540, 30fps, H.264, no audio; full decode passed; PID label overlap found in first frame review and corrected |
| MuJoCo H1 adapter preview | PASS | 12.0s, 960×540, 30fps, H.264, no audio; full decode passed |
| V10 short-beat regression | PASS | Four 0.4s beats rendered to 1.6s 960×54030 MP4; full decode passed |
| Python compile check | PASS | `python -m compileall -q` across changed Python modules and scripts |
| Clean source-copy reproduction | PASS | After the final weight+activation update, exported `HEAD` to `/tmp`, overlaid only this task's changed/new source files (no pilot 07/08 dependencies), then ran all 36 tests, checked-in AI trace validation, OpenMANIPULATOR-X asset validation, and capability inspection using the installed Python environment |
| GitHub Actions workflow | NOT RUN | Workflow file updated; remote Actions was not triggered |
| Three.js integrated render | PASS | Local Playwright capture produced the 8.5s 1080p30 segment; trace/query IDs, chunk IDs and Top-K match the source trace; 34s 960×54030 silent composite passed full decode. A separate 1s capture to `/tmp` verified external output paths and passed 1080p30 full decode |

The first auto-render attempt exposed two environmental/implementation failures: sandboxed loopback prevented the local HTTP server from starting, and an external `--output-dir` placed the projection outside the server root. The output-path bug is fixed by staging the temporary projection under the served project directory and copying it to the requested output. The final render ran with authorized local loopback and the renderer report records Manim and Three.js success.
