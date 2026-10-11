#!/usr/bin/env python3
"""Validate a saved PyBaMM battery result directory without running a solver."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.simulation_engines.battery.result_validator import load_validated_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    try:
        loaded = load_validated_result(args.result_dir)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    result = loaded["result"]
    print(json.dumps({"status": "PASS", "run_id": result["solver_execution"]["run_id"],
                      "sample_count": result["sample_count"],
                      "actual_end_time_s": result["actual_end_time_s"],
                      "result_sha256": result["result_sha256"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
