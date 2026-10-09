"""Deterministic run identity and collision-safe output directories."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_VERSION = "mechanism-adapter-contract/v1"


def _validate_cached_media(path: Path) -> bool:
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(path),
                        "--min-width", "540", "--min-height", "540", "--fps", "30",
                        "--full-decode"], cwd=ROOT,
                       capture_output=True, text=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path | None) -> str | None:
    if path is None:
        return None
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
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
             ROOT / "core/mechanism/trace_contract.py", ROOT / "core/shared-data/validate_trace.py",
             ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py",
             *sorted((ROOT / "core/mechanism/adapters").glob("*.py"))]
    return canonical_hash({str(path.relative_to(ROOT)): file_hash(path)
                          for path in paths if path.is_file()})


def make_run_identity(*, topic: str, config: dict[str, Any], trace: dict[str, Any],
                      mode: str, renderer: str, config_path: Path | None = None,
                      trace_path: Path | None = None, request: dict[str, Any] | None = None,
                      asset_revision: str | None = None) -> dict[str, str]:
    input_hash = canonical_hash({"request": request or {}, "config": config,
                                 "source_file_sha256": file_hash(config_path)})
    config_hash = canonical_hash({"config": config, "mode": mode, "renderer": renderer,
                                  "resolution": "540p30" if mode == "preview" else "1080p30"})
    trace_hash = canonical_hash(trace)
    renderer_hash = canonical_hash({"renderer": renderer, "mode": mode, "fps": 30})
    material = {"topic": topic, "input_hash": input_hash, "config_hash": config_hash,
                "trace_hash": trace_hash, "adapter_version": ADAPTER_VERSION,
                "asset_revision": asset_revision or "local-registry-default",
                "renderer_hash": renderer_hash, "code_revision": git_revision(),
                "code_fingerprint": code_fingerprint()}
    run_id = f"{topic}-{canonical_hash(material)[:20]}"
    return {"run_id": run_id, **material}


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
                if (data.get("technical_decode") == "PASS" and media.is_file() and media.stat().st_size > 0
                        and (expected_identity is None or data.get("identity") == expected_identity)
                        and _validate_cached_media(media)):
                    return candidate, True
            except (OSError, KeyError, TypeError, json.JSONDecodeError):
                pass
        raise FileExistsError(
            f"run directory already exists and is not reusable: {candidate}; "
            "existing output was preserved. Choose another --run-id or output root.")
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate, False
