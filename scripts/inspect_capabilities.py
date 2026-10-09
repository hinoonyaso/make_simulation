#!/usr/bin/env python3
"""List the verified mechanism capability catalog and execution support levels."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.mechanism.registry import MechanismRegistry


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
        print(json.dumps(row, ensure_ascii=False, indent=2))
        return 0
    rows = registry.list_capabilities()
    if args.domain:
        rows = [row for row in rows if row["domain"] == args.domain]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"{'TOPIC':32} {'DOMAIN':23} {'LEVEL':6} {'STATUS':20} ADAPTER")
        for row in rows:
            print(f"{row['topic']:32} {row['domain']:23} {row['support_level']:6} "
                  f"{row['implementation_status']:20} {row['adapter'] or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
