"""Copy the static educational costmap fields into a compact V9 trace (source is read-only)."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "topics/08_nav2/output/trace.json"


def main():
    src = json.loads(SOURCE.read_text(encoding="utf-8"))
    # Only the static map, its world axes/obstacle boxes, and the first baseline plan.
    # No dynamic-person branch, lidar returns, or controller candidate data is copied.
    sample = {
        "t": 0,
        "costmap": src["static_costmap"],
        "path": src["baseline"]["plans"][0]["path"],
    }
    trace = {
        "schema": "robotics-visual-trace/v1",
        "source": "topics/08_nav2/output/trace.json static_costmap + baseline.plans[0].path only; read-only",
        "evidence": "trace_playback of a custom educational model; not Nav2 execution",
        "units": {
            "time": "one static snapshot (1)",
            "costmap": "custom model cost 0..255 (1)",
            "path": "world x,y metres",
        },
        "resolution_m": src["resolution"],
        "robot_radius_m": src["robot_radius"],
        "x_min_m": src["xs"][0],
        "y_min_m": src["ys"][0],
        "width_cells": len(src["xs"]),
        "height_cells": len(src["ys"]),
        "xs_m": src["xs"],
        "ys_m": src["ys"],
        "obstacle_boxes_m": src["boxes"],
        "samples": [sample],
    }
    out = HERE / "data/costmap_trace.json"
    out.write_text(json.dumps(trace, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "core/shared-data/validate_trace.py"), str(out)], check=True)
    print(f"Copied {len(src['ys'])}x{len(src['xs'])} static cost grid, {len(sample['path'])}-pose baseline path")


if __name__ == "__main__":
    main()
