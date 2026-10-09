"""Manim preview/final rendering for plans emitted by registered adapters."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def render_plan(plan: dict, manifest_path: Path, output: Path, mode: str = "preview") -> Path:
    if mode not in {"preview", "final"}:
        raise ValueError("render mode must be preview or final")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    plan_path = output.with_suffix(".visual_plan.json")
    import json
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    resolution, quality = (("960,540", "-ql") if mode == "preview" else ("1920,1080", "-qh"))
    media_dir = output.parent / f"{output.stem}_manim"
    env = os.environ.copy()
    env["V11_VISUAL_PLAN"] = str(plan_path)
    env["V11_VISUAL_MANIFEST"] = str(Path(manifest_path).resolve())
    subprocess.run(["uv", "run", "manim", quality, "--fps", "30", "--resolution", resolution,
                    "--disable_caching", "--media_dir", str(media_dir),
                    str(ROOT / "core/mechanism/manim_scene.py"), "MechanismTraceScene"],
                   cwd=ROOT, env=env, check=True)
    size = "540p30" if mode == "preview" else "1080p30"
    rendered = media_dir / "videos/manim_scene" / size / "MechanismTraceScene.mp4"
    if not rendered.is_file():
        # Manim derives the scene folder from the module basename.
        rendered = media_dir / "videos/mechanism_scene" / size / "MechanismTraceScene.mp4"
    if not rendered.is_file():
        matches = list(media_dir.rglob("MechanismTraceScene.mp4"))
        if len(matches) != 1:
            raise FileNotFoundError(f"Manim output missing or ambiguous below {media_dir}")
        rendered = matches[0]
    output.write_bytes(rendered.read_bytes())
    minimum = "540" if mode == "preview" else "1920"
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(output),
                    "--min-width", minimum, "--min-height", "540" if mode == "preview" else "1080",
                    "--fps", "30", "--full-decode"],
                   cwd=ROOT, check=True)
    return output
