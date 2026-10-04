#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

ALLOWED_BGM = {"off", "low", "normal"}
REQ = {"id", "text", "target_seconds", "pause_after", "emphasis", "visual_cue", "sfx", "bgm"}

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_manifest.py narration_manifest.json")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        raise SystemExit("beats must be a non-empty list")
    seen = set()
    for i, b in enumerate(beats):
        missing = REQ - set(b)
        if missing: raise SystemExit(f"beat {i}: missing {sorted(missing)}")
        if b["id"] in seen: raise SystemExit(f"duplicate beat id: {b['id']}")
        seen.add(b["id"])
        if not isinstance(b["text"], str) or not b["text"].strip(): raise SystemExit(f"{b['id']}: empty text")
        if float(b["target_seconds"]) <= 0 or float(b["pause_after"]) < 0: raise SystemExit(f"{b['id']}: invalid timing")
        if b["bgm"] not in ALLOWED_BGM: raise SystemExit(f"{b['id']}: bgm must be {sorted(ALLOWED_BGM)}")
    print(f"OK: {len(beats)} beats")

if __name__ == "__main__":
    main()
