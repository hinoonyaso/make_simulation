"""Manim preview/final rendering for plans emitted by registered adapters."""
from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def _blender_binary() -> str:
    configured = os.environ.get("BLENDER_BIN")
    if configured:
        if len(configured) >= 3 and configured[1:3] in {":\\", ":/"}:
            converted = subprocess.run(["wslpath", "-u", configured], capture_output=True,
                                       text=True, check=True).stdout.strip()
            if Path(converted).is_file():
                return converted
        if not Path(configured).is_file() and not shutil.which(configured):
            raise FileNotFoundError(f"BLENDER_BIN does not exist or is not on PATH: {configured}")
        return configured
    found = shutil.which("blender")
    if found:
        return found
    # WSL can launch a Windows installation. Discover it without pinning a user/version path.
    for base in (Path(os.environ.get("ProgramFiles", "/mnt/c/Program Files")) / "Blender Foundation",
                 Path("/mnt/c/Program Files/Blender Foundation")):
        if base.is_dir():
            candidates = sorted(base.glob("Blender */blender.exe"), reverse=True)
            if candidates:
                return str(candidates[0])
    raise FileNotFoundError("Blender runtime not found; install Blender or set BLENDER_BIN to its executable")


def _blender_path_arg(path: Path, executable: str) -> str:
    """Use Windows paths when the selected executable is a Windows Blender under WSL."""
    if executable.casefold().endswith(".exe"):
        converted = subprocess.run(["wslpath", "-w", str(path)], capture_output=True,
                                   text=True, check=True).stdout.strip()
        return converted
    return str(path)


def render_h1_blender(trace_path: Path, output: Path, model_path: Path, mode: str = "preview",
                      timeline_path: Path | None = None) -> Path:
    """Render an already validated MuJoCo H1 trace with the existing pilot Blender scene."""
    if mode not in {"preview", "final"}:
        raise ValueError("render mode must be preview or final")
    from core.mechanism.run_management import media_metadata

    trace_path, model_path, output = Path(trace_path).resolve(), Path(model_path).resolve(), Path(output).resolve()
    if not trace_path.is_file() or not model_path.is_file():
        raise FileNotFoundError("H1 trace and source MJCF must both exist for Blender rendering")
    pilot = ROOT / "pilots/v11_2_h1_blender"
    backend_dir = output.parent / "blender_backend"
    backend_dir.mkdir(parents=True, exist_ok=True)
    export_command = [sys.executable, str(pilot / "export_trace.py"), "--trace", str(trace_path),
                      "--model", str(model_path), "--out", str(backend_dir), "--fps", "30"]
    if timeline_path is not None:
        export_command.extend(["--timeline", str(Path(timeline_path).resolve())])
    subprocess.run(export_command, cwd=ROOT, check=True)
    width, height = (960, 540) if mode == "preview" else (1920, 1080)
    blender = _blender_binary()
    script_arg = _blender_path_arg(pilot / "render_trace.py", blender)
    payload_arg = _blender_path_arg(backend_dir / "blender_payload.json", blender)
    output_arg = _blender_path_arg(backend_dir, blender)
    subprocess.run([blender, "--background", "--factory-startup", "--python", script_arg, "--",
                    "--payload", payload_arg, "--output", output_arg,
                    "--width", str(width), "--height", str(height), "--fps", "30"],
                   cwd=ROOT, check=True)
    rendered = backend_dir / "h1_trace_blender.mp4"
    if not rendered.is_file():
        raise FileNotFoundError(f"Blender did not produce expected media: {rendered}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rendered, output)
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(output),
                    "--min-width", str(width), "--min-height", str(height), "--fps", "30", "--full-decode"],
                   cwd=ROOT, check=True)
    actual = media_metadata(output)
    if actual["width"] != width or actual["height"] != height:
        raise RuntimeError(f"Blender produced {actual['width']}x{actual['height']}; expected {width}x{height}")
    payload = json.loads((backend_dir / "blender_payload.json").read_text(encoding="utf-8"))
    if actual["frame_count"] != len(payload.get("frames", [])):
        raise RuntimeError("Blender frame count does not match exported timeline payload")
    version = subprocess.run([blender, "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    from core.mechanism.run_management import file_hash
    (backend_dir / "renderer_provenance.json").write_text(json.dumps({
        "backend": "Blender H1 trace playback", "version": version, "mode": mode,
        "fps": 30, "width": width, "height": height, "codec": actual["codec"],
        "trace_sha256": file_hash(trace_path), "model_sha256": file_hash(model_path),
        "physics_integrated_by_blender": False,
        "state_source": "validated MuJoCo trace; interpolated qpos and FK at presentation frame source times",
        "timeline": payload.get("timeline"),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def render_yolo_trace(trace_path: Path, output: Path, manifest_path: Path, mode: str = "preview") -> Path:
    """Render the existing image-space YOLO scene from a validated trace."""
    if mode not in {"preview", "final"}:
        raise ValueError("render mode must be preview or final")
    trace_path, output = Path(trace_path).resolve(), Path(output).resolve()
    width, height = (960, 540) if mode == "preview" else (1920, 1080)
    media_dir = output.parent / "yolo_manim"
    env = os.environ.copy()
    env["YOLO_TRACE_PATH"] = str(trace_path)
    env["YOLO_MANIFEST_PATH"] = str(Path(manifest_path).resolve())
    timeline_path = Path(manifest_path).with_name("timeline.json")
    env["YOLO_TIMELINE_PATH"] = str(timeline_path.resolve())
    runner = shlex.split(os.environ.get("V11_MANIM_BIN", "uv run manim"))
    subprocess.run([*runner, "-ql" if mode == "preview" else "-qh", "--fps", "30",
                    "--resolution", f"{width},{height}", "--disable_caching", "--media_dir",
                    str(media_dir), str(ROOT / "pilots/v11_2_yolo/render_scene.py"),
                    "YoloInferenceScene"], cwd=ROOT, env=env, check=True)
    matches = list(media_dir.rglob("YoloInferenceScene.mp4"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one YOLO Manim video below {media_dir}, found {len(matches)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(matches[0], output)
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(output),
                    "--min-width", str(width), "--min-height", str(height), "--fps", "30", "--full-decode"],
                   cwd=ROOT, check=True)
    from core.mechanism.run_management import media_metadata
    actual = media_metadata(output)
    if actual["width"] != width or actual["height"] != height:
        raise RuntimeError(f"YOLO renderer produced {actual['width']}x{actual['height']}; expected {width}x{height}")
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    if actual["frame_count"] != timeline["total_frames"]:
        raise RuntimeError(f"YOLO produced {actual['frame_count']} frames; timeline requires {timeline['total_frames']}")
    return output


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
    timeline_path = Path(manifest_path).with_name("timeline.json").resolve()
    if not timeline_path.is_file():
        raise ValueError(f"shared timeline file is required for common Manim rendering: {timeline_path}")
    env["V11_TIMELINE_PATH"] = str(timeline_path)
    runner = shlex.split(os.environ.get("V11_MANIM_BIN", "uv run manim"))
    if not runner:
        raise ValueError("V11_MANIM_BIN must name a Manim executable")
    subprocess.run([*runner, quality, "--fps", "30", "--resolution", resolution,
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
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    from core.mechanism.run_management import media_metadata
    actual = media_metadata(rendered)
    if actual["frame_count"] != timeline["total_frames"]:
        raise RuntimeError(f"Manim produced {actual['frame_count']} frames; timeline requires {timeline['total_frames']}")
    output.write_bytes(rendered.read_bytes())
    minimum = "540" if mode == "preview" else "1920"
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(output),
                    "--min-width", minimum, "--min-height", "540" if mode == "preview" else "1080",
                    "--fps", "30", "--full-decode"],
                   cwd=ROOT, check=True)
    return output
