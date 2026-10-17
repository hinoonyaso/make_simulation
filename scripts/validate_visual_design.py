#!/usr/bin/env python3
"""Validate shared visual tokens and optionally check scene style/fonts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.visual_primitives.design_tokens import (
    TOKEN_PATH,
    contrast_ratio,
    load_tokens,
)
from core.visual_primitives.font_support import discover_korean_font, discover_manim_korean_font


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", action="append", default=[], help="scene source to pass to check_scene_style.py")
    parser.add_argument("--all-scenes", action="store_true", help="check Blender/Manim sources under pilots")
    parser.add_argument("--blender-text", help="verify an installed Blender font covers this Hangul text")
    parser.add_argument("--manim-text", help="verify an installed Manim family covers this Hangul text")
    parser.add_argument("--report", type=Path, help="optional JSON report path")
    args = parser.parse_args()

    results = []
    tokens = load_tokens(TOKEN_PATH)
    for name, profile in tokens["visual_profiles"].items():
        primary = contrast_ratio(profile["primary_text"], profile["background"])
        secondary = contrast_ratio(profile["secondary_text"], profile["background"])
        if min(primary, secondary) < 4.5:
            raise SystemExit(f"FAIL: {name} text contrast below 4.5:1")
        results.append({"check": "profile_contrast", "profile": name,
                        "primary_ratio": round(primary, 3), "secondary_ratio": round(secondary, 3),
                        "status": "PASS"})
    typography = tokens["typography_1080p"]
    if typography["minimum_critical_preview_px"] < 14:
        raise SystemExit("FAIL: critical preview text floor below 14px")
    results.append({"check": "token_schema", "schema": tokens["schema"], "status": "PASS"})

    if args.blender_text:
        path = discover_korean_font(args.blender_text)
        results.append({"check": "blender_font_coverage", "font_path": path, "status": "PASS"})
    if args.manim_text:
        family = discover_manim_korean_font(args.manim_text)
        results.append({"check": "manim_font_coverage", "family": family, "status": "PASS"})

    scenes = list(args.scene)
    if args.all_scenes:
        scenes.extend(str(path) for path in sorted((ROOT / "pilots").glob("**/*.py"))
                      if any(part in {"blender", "manim"} for part in path.parts))
    if scenes:
        command = [sys.executable, str(ROOT / "scripts/check_scene_style.py"), *scenes]
        completed = subprocess.run(command, cwd=ROOT, check=False)
        results.append({"check": "scene_style", "files": scenes,
                        "status": "PASS" if completed.returncode == 0 else "FAIL"})
        if completed.returncode:
            return completed.returncode

    report = {"status": "PASS", "tokens": str(TOKEN_PATH.relative_to(ROOT)), "results": results,
              "scope_note": "Token/static checks do not establish render readability, motion quality or comprehension."}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
