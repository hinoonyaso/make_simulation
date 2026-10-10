"""Deterministic run identity and collision-safe output directories."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import math
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_VERSION = "mechanism-adapter-contract/v1"


def media_metadata(path: Path) -> dict[str, Any]:
    result = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_read_frames,nb_frames",
        "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if len(streams) != 1:
        raise ValueError("media must contain exactly one video stream")
    stream = streams[0]
    rate_text = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    numerator, denominator = (int(part) for part in rate_text.split("/", 1))
    fps = numerator / denominator if denominator else 0
    duration = float(data.get("format", {}).get("duration", 0))
    frames = stream.get("nb_read_frames") or stream.get("nb_frames")
    return {"codec": stream.get("codec_name"), "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0)), "fps": fps, "duration_sec": duration,
            "frame_count": int(frames) if frames and frames != "N/A" else None}


def _validate_cached_media(path: Path, spec: dict[str, Any], reported: dict[str, Any]) -> bool:
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(path),
                        "--min-width", str(spec["width"]), "--min-height", str(spec["height"]), "--fps", "30",
                        "--full-decode"], cwd=ROOT,
                       capture_output=True, text=True, check=True)
        actual = media_metadata(path)
        return (actual["width"] >= spec["width"] and actual["height"] >= spec["height"]
                and math.isclose(actual["fps"], 30.0, abs_tol=.01)
                and actual["codec"] == (reported.get("codec") or spec["codec"])
                and actual["width"] == int(reported["width"])
                and actual["height"] == int(reported["height"])
                and math.isclose(actual["fps"], float(reported["fps"]), abs_tol=.01)
                and math.isclose(actual["duration_sec"], float(reported["duration_sec"]), abs_tol=.04)
                and (reported.get("frame_count") is None or actual["frame_count"] == int(reported["frame_count"])))
    except (OSError, KeyError, TypeError, ValueError, subprocess.CalledProcessError):
        return False


def _cache_identity_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Git revision is report metadata; render inputs are already fingerprinted."""
    actual_render_inputs = {key: value for key, value in actual.items() if key != "code_revision"}
    expected_render_inputs = {key: value for key, value in expected.items() if key != "code_revision"}
    return actual_render_inputs == expected_render_inputs


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timeline_digest(timeline: dict[str, Any] | None) -> str | None:
    if timeline is None:
        return None
    stored = timeline.get("timeline_sha256")
    return stored if isinstance(stored, str) and stored else canonical_hash(timeline)


def file_hash(path: Path | None) -> str | None:
    if path is None:
        return None
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def asset_tree_hash(root: Path) -> str:
    """Hash a local model bundle by relative paths and file content."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"model asset directory does not exist: {root}")
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if not files:
        raise ValueError(f"model asset directory is empty: {root}")
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big")); digest.update(relative)
        digest.update(bytes.fromhex(file_hash(path)))
    return digest.hexdigest()


def validate_replay_trace(topic: str, expected_schema: str, trace: dict[str, Any], adapter: Any) -> list[str]:
    """Check replay identity and delegate domain/integrity checks without executing the mechanism."""
    if not isinstance(trace, dict):
        return ["trace root must be a JSON object"]
    errors = []
    recorded_topic = trace.get("topic")
    if recorded_topic is not None and recorded_topic != topic:
        errors.append(f"trace topic mismatch: expected {topic}, got {recorded_topic!r}")
    if trace.get("schema") != expected_schema:
        errors.append(f"trace schema mismatch: expected {expected_schema}, got {trace.get('schema')!r}")
    if recorded_topic is None and topic == "rag":
        if trace.get("system", {}).get("family", "").casefold() != "rag":
            errors.append("legacy AI trace does not identify the RAG mechanism")
    if recorded_topic is None and topic == "robot_kinematics":
        if trace.get("model", {}).get("asset_id") != "blender.unitree_h1.v1":
            errors.append("legacy robotics trace is not for the registered Unitree H1 model")
    if not errors:
        errors.extend(adapter.validate(trace))
    return errors


def git_revision() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def code_fingerprint() -> str:
    paths = [ROOT / "scripts/produce_video.py", ROOT / "core/mechanism/renderer.py",
             ROOT / "core/mechanism/manim_scene.py", ROOT / "core/mechanism/storyboard.py",
             ROOT / "core/mechanism/run_management.py", ROOT / "core/mechanism/registry.py",
             ROOT / "core/mechanism/catalog.json", ROOT / "scripts/produce_ai_video.py",
             ROOT / "scripts/run_yolo_inference.py", ROOT / "scripts/validate_delivery.py",
             ROOT / "core/mechanism/trace_contract.py", ROOT / "core/shared-data/validate_trace.py",
             ROOT / "core/robotics-simulation/mujoco_adapter.py",
             ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py",
             ROOT / "pilots/v10_rag_poc/build_video.py", ROOT / "pilots/v10_rag_poc/rag_mechanism_scene.py",
             ROOT / "pilots/v11_2_yolo/render_scene.py", ROOT / "pilots/v11_2_h1_blender/export_trace.py",
             ROOT / "pilots/v11_2_h1_blender/render_trace.py",
             ROOT / "core/manim-robotics-education-skill/templates/manim_kit.py",
             ROOT / "core/blender-robotics-simulation-skill/templates/studio_utils.py",
             ROOT / "pilots/v10_threejs_rag/index.html", ROOT / "pilots/v10_threejs_rag/src/main.js",
             ROOT / "pilots/v10_threejs_rag/src/style.css", ROOT / "pilots/v10_threejs_rag/scripts/build_projection.py",
             ROOT / "pilots/v10_threejs_rag/scripts/capture_video.js",
             ROOT / "pilots/v10_threejs_rag/package-lock.json",
             ROOT / "core/mechanism/joint_motion.py", ROOT / "core/mechanism/pid_playback.py",
             ROOT / "core/mechanism/timeline.py", ROOT / "core/mechanism/renderer_routing.py",
             *sorted((ROOT / "core/mechanism/adapters").glob("*.py"))]
    return canonical_hash({str(path.relative_to(ROOT)): file_hash(path)
                          for path in paths if path.is_file()})


def make_run_identity(*, topic: str, config: dict[str, Any], trace: dict[str, Any],
                      mode: str, renderer: str, config_path: Path | None = None,
                      trace_path: Path | None = None, request: dict[str, Any] | None = None,
                      asset_revision: str | None = None, visual_goal: str | None = None,
                      timeline: dict[str, Any] | None = None, asset_hash: str | None = None,
                      renderer_version: str | None = None) -> dict[str, str]:
    input_hash = canonical_hash({"request": request or {}, "config": config,
                                 "source_file_sha256": file_hash(config_path)})
    render_mode = "preview" if renderer.endswith(":preview") else "final"
    render_spec = {"mode": render_mode, "width": 960 if render_mode == "preview" else 1920,
                   "height": 540 if render_mode == "preview" else 1080, "fps": 30, "codec": "h264"}
    config_hash = canonical_hash({"config": config, "mode": mode, "renderer": renderer,
                                  "render_spec": render_spec, "visual_goal": visual_goal,
                                  "timeline_hash": _timeline_digest(timeline),
                                  "renderer_version": renderer_version, "asset_hash": asset_hash})
    trace_hash = canonical_hash(trace)
    renderer_hash = canonical_hash({"renderer": renderer, "mode": mode, "fps": 30})
    material = {"topic": topic, "input_hash": input_hash, "config_hash": config_hash,
                "trace_hash": trace_hash, "adapter_version": ADAPTER_VERSION,
                "asset_revision": asset_revision or "local-registry-default",
                "visual_goal": visual_goal,
                "timeline_hash": _timeline_digest(timeline),
                "asset_hash": asset_hash,
                "renderer_version": renderer_version,
                "renderer_hash": renderer_hash,
                "code_fingerprint": code_fingerprint()}
    run_id = f"{topic}-{canonical_hash(material)[:20]}"
    return {"run_id": run_id, **material, "code_revision": git_revision(),
            "render_spec": render_spec, "renderer": renderer, "mode": mode,
            "trace_sha256": trace_hash, "config_sha256": config_hash,
            "visual_goal": visual_goal, "timeline_hash": _timeline_digest(timeline),
            "asset_hash": asset_hash, "renderer_version": renderer_version}


def prepare_run_dir(root: Path, run_id: str, *, reuse: bool = True,
                    force: bool = False,
                    expected_identity: dict[str, str] | None = None) -> tuple[Path, bool]:
    """Return (directory, cache_hit); never deletes or overwrites existing runs."""
    root = Path(root).resolve()
    candidate = root / run_id
    if candidate.exists():
        report = candidate / "production_report.json"
        if reuse and not force and report.is_file():
            try:
                data = json.loads(report.read_text(encoding="utf-8"))
                media = Path(data["media"])
                media = media.resolve()
                expected_media = (candidate / ("preview.mp4" if data.get("identity", {}).get("render_spec", {}).get("mode") == "preview" else "final.mp4")).resolve()
                spec = data.get("identity", {}).get("render_spec", {})
                actual_hash = file_hash(media) if media.is_file() else None
                trace_path = Path(data.get("trace", ""))
                if not trace_path.is_absolute():
                    trace_path = candidate / trace_path
                trace_path = trace_path.resolve()
                trace_value = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None
                stored_trace_hash = canonical_hash(trace_value) if trace_value is not None else None
                timeline_valid = True
                if data.get("identity", {}).get("timeline_hash"):
                    from core.mechanism.timeline import validate_timeline
                    timeline_path = candidate / "timeline.json"
                    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
                    timeline_valid = (not validate_timeline(timeline)
                                      and timeline.get("timeline_sha256") == data["identity"]["timeline_hash"]
                                      and timeline.get("total_frames") == data["media_metadata"]["frame_count"])

                if (timeline_valid and media == expected_media and media.is_file() and media.stat().st_size > 0
                        and data.get("technical_decode") == "PASS"
                        and data.get("topic") == data.get("identity", {}).get("topic")
                        and data.get("render_mode") == spec.get("mode")
                        and data.get("renderer")
                        and data.get("renderer") == str(data.get("identity", {}).get("renderer", "")).split(":", 1)[0]
                        and data.get("renderer_settings") == spec
                        and data.get("media_sha256") == actual_hash
                        and data.get("output_path") == str(media)
                        and data.get("media_metadata")
                        and trace_path.parent == candidate
                        and stored_trace_hash == data.get("identity", {}).get("trace_hash")
                        and (expected_identity is None or
                             _cache_identity_matches(data.get("identity", {}), expected_identity))
                        and _validate_cached_media(media, spec, data["media_metadata"])):
                    return candidate, True
            except (OSError, KeyError, TypeError, ValueError):
                pass
        raise FileExistsError(
            f"run directory already exists and is not reusable: {candidate}; "
            "existing output was preserved. Choose another --run-id or output root.")
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate, False
