#!/usr/bin/env python3
"""List the verified mechanism capability catalog and execution support levels."""
from __future__ import annotations

import argparse
import importlib.util
from importlib import metadata as importlib_metadata
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.mechanism.registry import MechanismRegistry
from core.mechanism.renderer_routing import VISUAL_GOALS, decide_renderer
from core.mechanism.run_management import asset_tree_hash


def environment_status(row: dict) -> str:
    if row["implementation_status"] != "ready":
        return "not executable"
    topic = row["topic"]
    required = ["numpy", "manim"]
    if topic == "robot_kinematics":
        required.append("mujoco")
    if topic == "object_detection":
        required.extend(["ultralytics", "torch", "PIL"])
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    if topic == "object_detection" and "ultralytics" not in missing:
        try:
            version = importlib_metadata.version("ultralytics")
            if version != "8.3.0":
                missing.append(f"Ultralytics version {version} (requires 8.3.0)")
        except importlib_metadata.PackageNotFoundError:
            missing.append("Ultralytics metadata unavailable")
    if topic == "robot_kinematics":
        try:
            from core.mechanism.renderer import _blender_binary
            _blender_binary()
        except (FileNotFoundError, OSError):
            missing.append("Blender (optional for --render blender)")
    return "available" if not missing else "missing: " + ", ".join(missing)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain")
    parser.add_argument("--topic")
    parser.add_argument("--json", action="store_true", help="print full capability records")
    parser.add_argument("--preflight", action="store_true", help="execute lightweight renderer process checks")
    parser.add_argument("--render", choices=("auto", "manim", "blender"), default="auto")
    parser.add_argument("--visual-goal", choices=VISUAL_GOALS, default="auto")
    parser.add_argument("--trace", type=Path, help="optional validated trace JSON for topic-specific routing")
    parser.add_argument("--model", type=Path, help="optional local model asset path for Blender preflight")
    args = parser.parse_args()
    registry = MechanismRegistry()
    if args.topic:
        row = registry.resolve(args.topic)
        if row is None:
            raise SystemExit(f"unknown topic or alias: {args.topic}")
        row["current_machine_runtime"] = environment_status(row)
        if args.preflight:
            trace = json.loads(args.trace.read_text(encoding="utf-8")) if args.trace else {}
            model_path = args.model
            if row["topic"] == "robot_kinematics" and model_path is None:
                model_path = ROOT / "assets/unitree_h1/mjcf/h1_with_hand.xml"
            try:
                if args.trace:
                    adapter = registry.load_adapter(row["topic"])
                    errors = adapter.validate(trace)
                    if errors:
                        row["renderer_decision"] = {"status": "BLOCKED",
                            "reason": "trace validation failed: " + "; ".join(errors)}
                        print(json.dumps(row, ensure_ascii=False, indent=2))
                        return 0
                decision = decide_renderer(topic=row["topic"], requested_renderer=args.render,
                    visual_goal=args.visual_goal, trace=trace, model_path=model_path)
                row["renderer_decision"] = decision
                if model_path and Path(model_path).is_file():
                    model_root = Path(model_path).resolve().parent.parent
                    row["model_asset_preflight"] = {"status": "PRESENT",
                        "model_path": str(Path(model_path).resolve()),
                        "asset_tree_sha256": asset_tree_hash(model_root)}
                elif model_path:
                    row["model_asset_preflight"] = {"status": "BLOCKED",
                        "reason": f"model file is missing: {model_path}"}
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                row["renderer_decision"] = {"status": "BLOCKED", "reason": str(exc)}
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0
    rows = registry.list_capabilities()
    if args.domain:
        rows = [row for row in rows if row["domain"] == args.domain]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"{'TOPIC':32} {'DOMAIN':23} {'LEVEL':6} {'SUPPORT':20} {'RUNTIME':38} ADAPTER")
        for row in rows:
            print(f"{row['topic']:32} {row['domain']:23} {row['support_level']:6} "
                  f"{row['implementation_status']:20} {environment_status(row):38} {row['adapter'] or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
