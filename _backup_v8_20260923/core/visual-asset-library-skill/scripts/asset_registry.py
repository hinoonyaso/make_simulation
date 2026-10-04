#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "assets" / "registry.json"

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def save(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--registry", default=str(DEFAULT))
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("list"); q.add_argument("--tool"); q.add_argument("--kind")
    g = sub.add_parser("get"); g.add_argument("id")
    v = sub.add_parser("validate")
    r = sub.add_parser("register"); r.add_argument("json_file")
    a = p.parse_args(); path = Path(a.registry); data = load(path); assets = data.get("assets", [])
    if a.cmd == "list":
        rows = [x for x in assets if (not a.tool or x.get("tool") == a.tool) and (not a.kind or x.get("kind") == a.kind)]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif a.cmd == "get":
        row = next((x for x in assets if x.get("id") == a.id), None)
        if row is None: raise SystemExit(f"not found: {a.id}")
        print(json.dumps(row, ensure_ascii=False, indent=2))
    elif a.cmd == "validate":
        req = {"id", "tool", "kind", "source", "version", "assumptions", "semantic_role", "provenance"}; ids=set()
        for row in assets:
            miss = req - set(row)
            if miss: raise SystemExit(f"{row.get('id','?')}: missing {sorted(miss)}")
            if row["id"] in ids: raise SystemExit(f"duplicate id: {row['id']}")
            ids.add(row["id"])
        print(f"OK: {len(assets)} assets")
    else:
        row = json.loads(Path(a.json_file).read_text(encoding="utf-8"))
        if any(x.get("id") == row.get("id") for x in assets): raise SystemExit(f"already exists: {row.get('id')}")
        assets.append(row); data["assets"] = assets; save(path, data); print(row["id"])

if __name__ == "__main__": main()
