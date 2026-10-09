"""Build a trace-driven Manim rendering of the MuJoCo arm run."""
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
if mode not in {"preview", "final"}:
    raise SystemExit("usage: build_video.py [preview|final]")
quality, resolution = (("-ql", "960,540") if mode == "preview" else ("-qh", "1920,1080"))
output = HERE / "output"
render_dir = output / f"{mode}_render"
render_dir.mkdir(parents=True, exist_ok=True)
subprocess.run(["uv", "run", "python", "scripts/run_mujoco_arm_poc.py"], cwd=ROOT, check=True)
subprocess.run(["uv", "run", "python", "core/shared-data/validate_trace.py",
                str(HERE / "data/trace.json")], cwd=ROOT, check=True)
subprocess.run(["uv", "run", "manim", quality, "--fps", "30", "--resolution", resolution,
                "--disable_caching", "--media_dir", str(render_dir),
                str(HERE / "arm_trace_scene.py"), "MujocoArmTraceScene"], cwd=ROOT, check=True)
size = "540p30" if mode == "preview" else "1080p30"
source = render_dir / "videos/arm_trace_scene" / size / "MujocoArmTraceScene.mp4"
target = output / ("mujoco_h1_arm_preview.mp4" if mode == "preview" else "mujoco_h1_arm.mp4")
shutil.copy2(source, target)
print(target, target.stat().st_size, "bytes (video-only; no narration)")
