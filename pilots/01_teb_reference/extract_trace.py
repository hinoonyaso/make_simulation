"""Convert topic 09's computed TEB-style toy model output into V9 shared traces.

Source (read-only): topics/09_dwb_teb/output/trace.json, produced by topics/09_dwb_teb/model.py.
Both Manim and Blender read only the files written here; neither invents values.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[1]
SOURCE = BUNDLE / "topics/09_dwb_teb/output/trace.json"
DATA = HERE / "data"
FPS = 30


def advance(p, v, w, dt):
    """Exact constant-twist differential-drive step; same equations as topics/09 model.advance."""
    x, y, th = p
    if abs(w) < 1e-8:
        x += v * dt * math.cos(th); y += v * dt * math.sin(th)
    else:
        x += v / w * (math.sin(th + w * dt) - math.sin(th))
        y += v / w * (-math.cos(th + w * dt) + math.cos(th))
    th = (th + w * dt + math.pi) % (2 * math.pi) - math.pi
    return [x, y, th]


def drive_trace(src):
    run = src["runs"]["teb_obstacle"]; rows = run["rows"]; step = src["dt"]
    samples = []
    end = run["metrics"]["duration_s"]
    for i in range(round(end * FPS) + 1):
        t = i / FPS
        k = min(int(t / step + 1e-9), len(rows) - 1)
        row = rows[k]; tau = min(t - row["time"], step)
        v, w = row["cmd"]
        pose = advance(row["pose"], v, w, tau)
        wheel = [a + r * tau for a, r in zip(row["wheel_angles"], row["wheel_rates"])]
        samples.append({"t": t, "pose": pose, "cmd": [v, w], "wheel_angle": wheel, "step": k})
    bands = [[p[:2] for p in r["detail"]["poses"]] for r in rows]
    return {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/09_dwb_teb/model.py teb_obstacle run (TEB-style toy model, not ROS 2 TEB)",
        "units": {"time": "s", "pose": "m,m,rad", "cmd": "m/s,rad/s", "wheel_angle": "rad (model wheel r=0.10 m)", "step": "1"},
        "fps": FPS, "control_dt": step,
        "robot_radius": src["robot_radius"], "obstacle": src["obstacle"], "obstacle_radius": src["obstacle_radius"],
        "corridor_half_width": src["corridor_half_width"], "start": src["start"], "goal": src["goal"],
        "bands": bands, "metrics": run["metrics"], "samples": samples,
    }


def hero_trace(src):
    hero = src["hero"]["teb"]
    samples = []
    for i, it in enumerate(hero["detail"]["iterations"]):
        c = it["costs"]
        samples.append({"t": i, "poses": it["poses"], "dt": it["dt"], "objective": it["objective"],
                        "cost_time": c["time"], "cost_obstacle": c["obstacle"], "cost_kinematics": c["kinematics"],
                        "cost_via": c["via"], "cost_smooth": c["smooth"]})
    return {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/09_dwb_teb/model.py hero TEB-style band optimisation at a fixed what-if pose",
        "units": {"time": "optimizer snapshot index", "poses": "m,m,rad", "dt": "s", "objective": "1",
                  "cost_time": "1", "cost_obstacle": "1", "cost_kinematics": "1", "cost_via": "1", "cost_smooth": "1"},
        "pose": hero["pose"], "cmd": hero["cmd"], "control_dt": src["dt"],
        "robot_radius": src["robot_radius"], "obstacle": src["obstacle"], "obstacle_radius": src["obstacle_radius"],
        "corridor_half_width": src["corridor_half_width"], "samples": samples,
    }


if __name__ == "__main__":
    src = json.loads(SOURCE.read_text())
    DATA.mkdir(exist_ok=True)
    for name, trace in (("drive_trace.json", drive_trace(src)), ("band_trace.json", hero_trace(src))):
        (DATA / name).write_text(json.dumps(trace, ensure_ascii=False))
        subprocess.run([sys.executable, str(BUNDLE / "core/shared-data/validate_trace.py"), str(DATA / name)], check=True)
    drive = json.loads((DATA / "drive_trace.json").read_text())
    last = drive["samples"][-1]["pose"]; ref = src["runs"]["teb_obstacle"]["rows"][-1]
    # Interpolation must land on the model's own next_pose at the run end.
    assert all(abs(a - b) < 1e-9 for a, b in zip(last, advance(ref["pose"], *ref["cmd"], src["dt"])))
    print(f"drive samples {len(drive['samples'])}, bands {len(drive['bands'])}")
