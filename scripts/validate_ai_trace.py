#!/usr/bin/env python3
"""Validate ai-mechanism-trace/v1 without touching the robotics trace contract."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    errors = module.validate_trace(trace)
    if errors:
        print("FAIL\n" + "\n".join(f"- {e}" for e in errors))
        raise SystemExit(1)
    print(f"PASS {trace['schema']}: {len(trace['operations'])} operations, "
          f"{len(trace['intermediate_values'])} values")


if __name__ == "__main__":
    main()
