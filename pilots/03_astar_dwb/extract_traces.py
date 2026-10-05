"""Convert read-only A* and DWB episode outputs into compact V9 visual traces."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def main():
    astar_src = json.loads((ROOT / "topics/07_astar/output/trace.json").read_text(encoding="utf-8"))
    detail = astar_src["astar"]
    astar = {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/07_astar/output/trace.json astar only; source output read-only",
        "units": {"time": "one recorded plan (1)", "width": "cells", "height": "cells",
                  "start": "grid cells", "goal": "grid cells", "blocked": "grid cells",
                  "path": "grid cells", "cost": "grid steps", "expanded_before_goal": "grid cells"},
        "width": astar_src["width"], "height": astar_src["height"],
        "start": astar_src["start"], "goal": astar_src["goal"],
        "blocked": astar_src["blocked"],
        "samples": [{"t": 0, "path": detail["path"], "cost": detail["cost"],
                     "expanded_before_goal": detail["expanded_before_goal"]}],
    }
    dwb_src = json.loads((ROOT / "topics/09_dwb_teb/output/trace.json").read_text(encoding="utf-8"))
    hero = dwb_src["hero"]["dwb"]
    samples = []
    for i, c in enumerate(hero["detail"]["candidates"]):
        samples.append({"t": i, "candidate": i, "cmd": [c["v"], c["w"]],
                        "valid": int(c["valid"]), "score": float(c["score"] or 0),
                        "selected": int(i == hero["detail"]["selected"]),
                        "clearance": c["minimum_clearance"], "trajectory": c["trajectory"]})
    dwb = {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/09_dwb_teb/output/trace.json hero.dwb only; source output read-only",
        "units": {"time": "candidate index (1)", "candidate": "1", "cmd": "m/s,rad/s",
                  "valid": "1 (boolean 0/1)", "score": "weighted educational-model cost (1)",
                  "selected": "1 (boolean 0/1)", "clearance": "m",
                  "trajectory": "21 poses in m,m,rad; 0.1 s spacing over 2 s"},
        "pose": hero["pose"], "dt": dwb_src["dt"],
        "prediction_horizon": 2.0, "obstacle": dwb_src["obstacle"],
        "obstacle_radius": dwb_src["obstacle_radius"],
        "corridor_half_width": dwb_src["corridor_half_width"],
        "candidate_count": len(samples), "valid_count": sum(s["valid"] for s in samples),
        "selected_index": hero["detail"]["selected"], "samples": samples,
    }
    (HERE / "data").mkdir(exist_ok=True)
    for name, data in (("astar_trace.json", astar), ("dwb_trace.json", dwb)):
        path = HERE / "data" / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "core/shared-data/validate_trace.py"), str(path)], check=True)
    print(f"A*: {len(detail['path'])} path cells, cost {detail['cost']}; DWB: {len(samples)} candidates")

if __name__ == "__main__":
    main()
