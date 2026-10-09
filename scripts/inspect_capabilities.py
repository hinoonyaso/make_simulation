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
    args = parser.parse_args()
    registry = MechanismRegistry()
    if args.topic:
        row = registry.resolve(args.topic)
        if row is None:
            raise SystemExit(f"unknown topic or alias: {args.topic}")
        row["current_machine_runtime"] = environment_status(row)
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
