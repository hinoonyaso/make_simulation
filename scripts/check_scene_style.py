#!/usr/bin/env python3
"""Static gate for slide-style scene code (patterns measured in topics/09 vs pilots/01).

    python scripts/check_scene_style.py <scene.py or directory> ...

Manim  FAIL: self.clear() resets; no state-continuity primitive at all.
       WARN: more FadeOut than continuity primitives (likely fade-replace slides).
Blender FAIL: Workbench engine; render fps below 24.
       WARN: kit not imported (studio_utils / scene_kit); final resolution below 1920 px wide.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

CONTINUITY = re.compile(r"\b(Transform|ReplacementTransform|TransformMatchingTex|TransformMatchingShapes|"
                        r"TransformFromCopy|ValueTracker|always_redraw|add_updater|state_transform|BeatClock)\b|\.animate\b")


def check_manim(src):
    errors, warns = [], []
    if re.search(r"self\.clear\(\)", src):
        errors.append("self.clear() wipes the scene between beats; transform persistent objects instead")
    cont = len(CONTINUITY.findall(src))
    fades = len(re.findall(r"\bFadeOut\(", src))
    if cont == 0:
        errors.append("no state-continuity primitive (Transform/ValueTracker/updater/.animate)")
    elif fades > cont:
        warns.append(f"FadeOut x{fades} > continuity primitives x{cont}: check for fade-replace slides")
    return errors, warns


def check_blender(src):
    errors, warns = [], []
    if "BLENDER_WORKBENCH" in src:
        errors.append("Workbench is a viewport preview engine; use EEVEE/Cycles via studio_utils/scene_kit")
    for m in re.finditer(r"render\.fps\s*=\s*(\d+)", src):
        if int(m.group(1)) < 24:
            errors.append(f"render.fps={m.group(1)}: render natively at >=24 fps instead of time-stretching")
    if not re.search(r"\b(studio_utils|scene_kit)\b", src):
        warns.append("kit not imported: reuse studio_utils/scene_kit before custom infrastructure")
    for m in re.finditer(r"resolution_x\s*=\s*(\d+)", src):
        if int(m.group(1)) < 1920:
            warns.append(f"resolution_x={m.group(1)} < 1920 (fine for previews only)")
    return errors, warns


def files(args):
    for a in args:
        p = Path(a)
        yield from (sorted(p.rglob("*.py")) if p.is_dir() else [p])


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    failed = False
    for path in files(argv):
        if "__pycache__" in path.parts or "archive" in path.parts:
            continue
        src = path.read_text(encoding="utf-8", errors="ignore")
        kinds = []
        if re.search(r"^\s*from manim import|^\s*import manim", src, re.M):
            kinds.append(("manim", check_manim))
        if re.search(r"^\s*import bpy", src, re.M) and re.search(r"render\.|bpy\.ops\.render", src):
            kinds.append(("blender", check_blender))
        for kind, fn in kinds:
            errors, warns = fn(src)
            status = "FAIL" if errors else ("WARN" if warns else "PASS")
            failed |= bool(errors)
            print(f"{status} [{kind}] {path}")
            for e in errors:
                print(f"  - {e}")
            for w in warns:
                print(f"  ~ {w}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
