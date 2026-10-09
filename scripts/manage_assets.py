#!/usr/bin/env python3
"""Inspect and validate local assets; remote fetch requires a pinned archive contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core/visual-assets"))
from asset_factory import AssetFactory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=ROOT / "core/visual-assets/registry.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    search = sub.add_parser("search"); search.add_argument("--category"); search.add_argument("--tool"); search.add_argument("--kind")
    for name in ("fetch", "validate", "convert"):
        command = sub.add_parser(name); command.add_argument("--asset", required=True)
        if name == "convert": command.add_argument("--target", required=True)
    args = parser.parse_args()
    factory = AssetFactory(ROOT, registry=args.registry)
    catalog = json.loads(args.registry.read_text(encoding="utf-8"))["assets"]
    if args.command in {"list", "search"}:
        rows = catalog
        for field in ("category", "tool", "kind"):
            value = getattr(args, field, None)
            if value:
                rows = [row for row in rows if value.casefold() in str(row.get(field, row.get("robot_family", ""))).casefold()]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if args.command == "fetch":
        entry = next((row for row in catalog if row.get("id") == args.asset), None)
        if entry is None:
            raise SystemExit(f"unknown asset: {args.asset}")
        path = factory.resolve_asset(args.asset)
        if path.exists():
            report = factory.validate_asset(args.asset)
            print(f"PRESENT: {args.asset}; SHA-256 {report['sha256']}; no duplicate download performed")
            return 0
        if not entry.get("source_archive_url") or not entry.get("source_archive_sha256"):
            raise SystemExit("no pinned archive URL and SHA-256 are registered; remote fetch refused")
        raise SystemExit("pinned remote archive fetching is not implemented; asset remains unchanged")
    if args.command == "validate":
        report = factory.validate_asset(args.asset)
        entry = next(row for row in catalog if row.get("id") == args.asset)
        if entry.get("root_file", "").endswith(".urdf"):
            from validators.urdf import validate_urdf_asset
            report["urdf_validation"] = validate_urdf_asset(ROOT, entry)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "convert":
        output = factory.convert_asset(args.asset, args.target)
        print(output)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
