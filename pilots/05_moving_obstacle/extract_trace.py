"""Read-only projection of topics/08_nav2/output/trace.json into a V9 lesson trace."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "topics/08_nav2/output/trace.json"
MODEL = ROOT / "topics/08_nav2/model.py"


def main():
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("nav2_education_model", MODEL)
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    rows = raw["dynamic"]["rows"]
    plans = raw["dynamic"]["plans"]
    snapshots = []
    for t in (0.0, 2.0, 3.0):
        row = min(rows, key=lambda r: abs(r["time"] - t))
        plan = min(plans, key=lambda p: abs(p["time"] - t))
        det = row["detected"]
        snapshots.append({
            "t": float(t), "detected_xy": det or [0.0, 0.0],
            "obstacle_active": int(det is not None),
            "cost": model.costmap(det).round(3).tolist(),
            "path": plan["path"], "plan_reason": plan["reason"],
            "robot_xyyaw": row["pose"], "obstacle_truth_xy": row["person"] or [0.0, 0.0],
        })
    playback = [{k: r[k] for k in ("time", "pose", "next_pose", "person", "detected", "cmd", "path_id")}
                for r in rows]
    result = {
        "schema": "robotics-visual-trace/v9", "source": "topics/08_nav2/output/trace.json",
        "evidence": "trace_playback", "units": {"time": "s", "detected_xy": "m",
        "obstacle_active": "1", "cost": "0..255", "path": "m", "robot_xyyaw": "m,rad",
        "obstacle_truth_xy": "m"}, "resolution_m": raw["resolution"],
        "robot_radius_m": raw["robot_radius"], "circular_obstacle_radius_m": raw["person_radius"],
        "start": raw["start"], "goal": raw["goal"], "boxes": raw["boxes"],
        "xs": raw["xs"], "ys": raw["ys"], "samples": snapshots, "snapshots": snapshots, "playback": playback,
        "metrics": raw["dynamic"]["metrics"],
    }
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "data/trace.json").write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Projected {len(snapshots)} map/plan states and {len(playback)} source playback rows")


if __name__ == "__main__":
    main()
