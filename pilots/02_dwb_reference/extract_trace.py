"""Project only the DWB records from the completed topic 09 trace into V9 traces.

The topic trace is read-only. This script does not run or modify the DWB model.
"""
from __future__ import annotations

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


def advance(pose, command, seconds):
    x, y, theta = pose
    v, w = command
    if abs(w) < 1e-8:
        x += v * seconds * math.cos(theta)
        y += v * seconds * math.sin(theta)
    else:
        x += v / w * (math.sin(theta + w * seconds) - math.sin(theta))
        y += v / w * (-math.cos(theta + w * seconds) + math.cos(theta))
    theta = (theta + w * seconds + math.pi) % (2 * math.pi) - math.pi
    return [x, y, theta]


def hero_candidates(src):
    hero = src["hero"]["dwb"]
    detail = hero["detail"]
    selected = detail["selected"]
    samples = []
    for i, candidate in enumerate(detail["candidates"]):
        samples.append({
            "t": i,
            "candidate": i,
            "cmd": [candidate["v"], candidate["w"]],
            "valid": int(candidate["valid"]),
            # Invalid candidates have no score in the source; represent that as zero
            # only alongside valid=0 so the fixed numeric V9 sample shape is preserved.
            "score": float(candidate["score"] or 0.0),
            "costs": candidate["costs"],
            "minimum_clearance": candidate["minimum_clearance"],
            "selected": int(i == selected),
            "trajectory": candidate["trajectory"],
        })
    return {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/09_dwb_teb/output/trace.json hero.dwb only; source output read-only",
        "units": {
            "time": "candidate index (1)", "candidate": "1", "cmd": "m/s,rad/s",
            "valid": "1 (boolean as 0/1)", "score": "weighted toy cost (1; zero when valid=0)",
            "costs": "weighted toy cost components (1): path, goal, obstacle, speed, turn",
            "minimum_clearance": "m", "selected": "1 (boolean as 0/1)",
            "trajectory": "21 poses in m,m,rad; 0.1 s spacing over 2 s",
        },
        "pose": hero["pose"],
        "control_dt": src["dt"],
        "prediction_horizon": 2.0,
        "robot_radius": src["robot_radius"],
        "obstacle": src["obstacle"],
        "obstacle_radius": src["obstacle_radius"],
        "corridor_half_width": src["corridor_half_width"],
        "candidate_count": len(samples),
        "selected_index": selected,
        "valid_count": sum(s["valid"] for s in samples),
        "samples": samples,
    }


def drive_trace(src):
    run = src["runs"]["dwb_obstacle"]
    rows = run["rows"]
    step = src["dt"]
    end = run["metrics"]["duration_s"]
    samples = []
    for i in range(round(end * FPS) + 1):
        t = i / FPS
        k = min(int(t / step + 1e-9), len(rows) - 1)
        row = rows[k]
        tau = min(t - row["time"], step)
        samples.append({
            "t": t,
            "pose": advance(row["pose"], row["cmd"], tau),
            "cmd": row["cmd"],
            "clearance": row["clearance"],
            "step": k,
            "selected": row["detail"]["selected"] if row["detail"]["selected"] is not None else -1,
        })
    decisions = []
    for row in rows:
        candidates = row["detail"]["candidates"]
        index = row["detail"]["selected"]
        chosen = candidates[index] if index is not None else None
        prediction = chosen["trajectory"] if chosen else [row["pose"]] * 21
        decisions.append({
            "t": row["time"],
            "pose": row["pose"],
            "next_pose": row["next_pose"],
            "cmd": row["cmd"],
            "clearance": row["clearance"],
            "step": row["k"],
            "selected": index if index is not None else -1,
            "selected_cmd": chosen and [chosen["v"], chosen["w"]] or [0.0, 0.0],
            "selected_score": float(chosen["score"] or 0.0) if chosen else 0.0,
            "candidate_count": len(candidates),
            "valid_count": sum(int(c["valid"]) for c in candidates),
            "prediction": prediction,
        })
    return {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/09_dwb_teb/output/trace.json runs.dwb_obstacle only; source output read-only",
        "units": {"time": "s", "pose": "m,m,rad", "cmd": "m/s,rad/s", "clearance": "m",
                  "step": "1 (source 0.2 s DWB decision index)", "selected": "candidate index; -1 after source selection ends"},
        "fps": FPS,
        "control_dt": step,
        "robot_radius": src["robot_radius"],
        "obstacle": src["obstacle"],
        "obstacle_radius": src["obstacle_radius"],
        "corridor_half_width": src["corridor_half_width"],
        "start": src["start"],
        "goal": src["goal"],
        "metrics": run["metrics"],
        "decisions": decisions,
        "samples": samples,
    }


def main():
    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    DATA.mkdir(exist_ok=True)
    out = {
        "candidate_trace.json": hero_candidates(src),
        "drive_trace.json": drive_trace(src),
    }
    for name, trace in out.items():
        target = DATA / name
        target.write_text(json.dumps(trace, ensure_ascii=False), encoding="utf-8")
        subprocess.run([sys.executable, str(BUNDLE / "core/shared-data/validate_trace.py"), str(target)], check=True)

    # Prove that the first displayed 0.2 s movement is the chosen source command.
    candidate = out["candidate_trace.json"]
    chosen = candidate["samples"][candidate["selected_index"]]
    assert chosen["valid"] == 1 and chosen["selected"] == 1
    first = src["hero"]["dwb"]["detail"]["candidates"][candidate["selected_index"]]
    expected = advance(candidate["pose"], [first["v"], first["w"]], src["dt"])
    observed = first["trajectory"][2]
    assert max(abs(a - b) for a, b in zip(expected, observed)) < 1e-9
    print(f"DWB-only traces: {len(candidate['samples'])} candidates, {len(out['drive_trace.json']['samples'])} drive frames")


if __name__ == "__main__":
    main()
