#!/usr/bin/env python3
"""Execute a registered battery solver config and persist validated result files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.simulation_engines.battery.pybamm_adapter import execute_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    try:
        result = execute_config(args.config, args.output_dir, args.run_id)
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"},
                         ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"],
                      "run_id": result["solver_execution"]["run_id"],
                      "pybamm_version": result["solver_execution"]["pybamm_version"],
                      "solver_name": result["solver_execution"]["solver_name"],
                      "execution_seconds": result["solver_execution"]["execution_seconds"],
                      "actual_end_time_s": result["actual_end_time_s"],
                      "termination_reason": result["termination_reason"],
                      "sample_count": result["sample_count"],
                      "result_sha256": result["result_sha256"],
                      "output_dir": str(args.output_dir.resolve())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
