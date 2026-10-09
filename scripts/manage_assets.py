#!/usr/bin/env python3
"""Inspect and validate local assets; remote fetch requires a pinned archive contract."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core/visual-assets"))
from asset_factory import AssetFactory
from core.simulation.environments.registry import EnvironmentRegistry


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
    environments = EnvironmentRegistry().list()
    if args.command in {"list", "search"}:
        rows = catalog + environments
        if getattr(args, "category", None) and args.category.casefold() == "environment":
            rows = [row for row in rows if row.get("asset_type") == "environment"]
        for field in ("category", "tool", "kind"):
            value = getattr(args, field, None)
            if value and not (field == "category" and value.casefold() == "environment"):
                rows = [row for row in rows if value.casefold() in str(row.get(field, row.get("robot_family", ""))).casefold()]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    if args.command == "fetch":
        entry = next((row for row in catalog if row.get("id") == args.asset), None)
        if entry is None:
            env = next((row for row in environments if row["id"] == args.asset), None)
            if env is None:
                raise SystemExit(f"unknown asset or environment: {args.asset}")
            missing = [name for name, value in (("source_revision", env.get("source_revision")),
                       ("source archive URL", env.get("source_archive_url")),
                       ("source archive SHA-256", env.get("source_archive_sha256")),
                       ("archive size", env.get("source_archive_size_bytes"))) if not value]
            if missing:
                raise SystemExit(f"environment download refused: {args.asset}; missing verified metadata: {', '.join(missing)}. "
                                 "No archive was downloaded; dependencies and model licenses must be audited first.")
            from safe_archive import fetch_pinned_archive
            if not env.get("archive_install_path"):
                raise SystemExit("environment has no reviewed archive_install_path; refusing to choose an install location")
            destination = (ROOT / env["archive_install_path"]).resolve()
            if not destination.is_relative_to(ROOT):
                raise SystemExit("environment archive_install_path escapes project root")
            report = fetch_pinned_archive(url=env["source_archive_url"], destination=destination,
                sha256=env["source_archive_sha256"], size_bytes=env["source_archive_size_bytes"],
                allowed_hosts=env.get("allowed_hosts", []), allow_large=False)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        path = factory.resolve_asset(args.asset)
        if path.exists():
            report = factory.validate_asset(args.asset)
            print(f"PRESENT: {args.asset}; SHA-256 {report['sha256']}; no duplicate download performed")
            return 0
        if not entry.get("source_archive_url") or not entry.get("source_archive_sha256"):
            raise SystemExit("no pinned archive URL and SHA-256 are registered; remote fetch refused")
        required = {"source_commit": entry.get("source_commit"),
                    "source_archive_size_bytes": entry.get("source_archive_size_bytes"),
                    "archive_install_path": entry.get("archive_install_path")}
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SystemExit("remote fetch refused; missing reviewed metadata: " + ", ".join(missing))
        from safe_archive import fetch_pinned_archive
        destination = (ROOT / entry["archive_install_path"]).resolve()
        if not destination.is_relative_to(ROOT):
            raise SystemExit("asset archive_install_path escapes project root")
        report = fetch_pinned_archive(url=entry["source_archive_url"], destination=destination,
            sha256=entry["source_archive_sha256"], size_bytes=entry["source_archive_size_bytes"],
            allowed_hosts=entry.get("allowed_hosts", []), allow_large=False)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
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
