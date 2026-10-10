#!/usr/bin/env python3
"""Export only selected V12 dependency groups from the committed uv.lock.

The project has a large default media/AI stack. `uv export --only-group` still
includes that project dependency set, so CI uses this small lock graph exporter
to install just the engineering groups. The motulator drive path tested here
does not import torch; its Darwin/Linux torch extra is therefore deliberately
excluded and documented rather than installed in CI.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

try:
    from packaging.markers import Marker, default_environment
except ImportError as exc:  # pragma: no cover - clear bootstrap error for CI
    raise SystemExit("Install packaging==26.3 from uv.lock before running this exporter") from exc

ROOT = Path(__file__).resolve().parents[1]
OMIT = {"torch"}


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def active(item: dict) -> bool:
    marker = item.get("marker")
    return not marker or Marker(marker).evaluate(default_environment())


def export(groups: list[str]) -> list[dict]:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    root = next(p for p in lock["package"] if p["name"] == config["project"]["name"])
    group_roots = root.get("dev-dependencies", {})
    unknown = sorted(set(groups) - group_roots.keys())
    if unknown:
        raise ValueError(f"Unknown locked V12 group(s): {', '.join(unknown)}")

    records = {}
    for item in lock["package"]:
        records.setdefault(canonical(item["name"]), []).append(item)
    selected: dict[str, dict] = {}
    pending = [dep for group in groups for dep in group_roots[group]]
    while pending:
        dep = pending.pop()
        name = canonical(dep["name"])
        if name in OMIT or not active(dep):
            continue
        candidates = records.get(name, [])
        if dep.get("version"):
            candidates = [p for p in candidates if p["version"] == dep["version"]]
        candidates = [p for p in candidates if active(p)]
        if dep.get("source"):
            candidates = [p for p in candidates if p.get("source") == dep["source"]]
        if len(candidates) != 1:
            raise ValueError(f"Could not resolve one locked package for {dep!r}: {len(candidates)} candidates")
        record = candidates[0]
        if name in selected:
            if selected[name]["version"] != record["version"]:
                raise ValueError(f"Conflicting locked versions for {name}")
            continue
        selected[name] = record
        pending.extend(record.get("dependencies", []))
    return sorted(selected.values(), key=lambda p: canonical(p["name"]))


def render(records: list[dict]) -> str:
    lines = [
        "# Generated from uv.lock for the selected V12 groups.",
        "# Install with pip --no-deps --require-hashes; dependency closure is explicit.",
    ]
    for record in records:
        hashes = []
        for item in [record.get("sdist"), *record.get("wheels", [])]:
            if item and item.get("hash"):
                hashes.append(item["hash"])
        if not hashes:
            raise ValueError(f"No artifact hashes in uv.lock for {record['name']}")
        hashes = sorted(set(hashes))
        lines.append(f"{record['name']}=={record['version']} \\")
        lines.extend(f"    --hash={h} \\" for h in hashes[:-1])
        lines.append(f"    --hash={hashes[-1]}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--groups", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--print-packages", action="store_true")
    args = parser.parse_args()
    try:
        selected = export(args.groups)
        output = render(selected)
    except (KeyError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"V12 locked requirements export failed: {exc}", file=sys.stderr)
        return 2
    args.output.write_text(output, encoding="utf-8")
    if args.print_packages:
        print(json.dumps([f"{p['name']}=={p['version']}" for p in selected], indent=2))
    print(f"Wrote {len(selected)} locked requirements for groups: {', '.join(args.groups)}")
    print("Excluded unused optional dependency: torch (motulator drive imports tested without it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
