"""Thin adapter over the existing V10 RAG execution/trace contract."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from core.mechanism.protocol import MechanismRequest


def _load(path: Path, name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RAGAdapter:
    def __init__(self, capability: dict[str, Any] | None = None):
        self.capability = capability or {}
        self.root = Path(__file__).resolve().parents[3]

    def describe_capability(self): return self.capability
    def prepare(self, request: MechanismRequest): return {"topic": request.topic, **request.options}

    def execute(self, config: dict[str, Any]):
        if config.get("trace_path"):
            trace_path = Path(config["trace_path"])
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            errors = self.validate(trace)
            if errors:
                raise ValueError("invalid RAG trace: " + "; ".join(errors))
            return trace
        if not config.get("document") or not config.get("question"):
            raise ValueError("RAG execution requires both document and question, or trace_path for replay")
        module = _load(self.root / "core/ai-mechanism/execute_local_rag.py", "execute_local_rag")
        return module.execute_lexical_rag(config["document"], config["question"],
            chunk_size=int(config.get("chunk_size", 500)), overlap=int(config.get("overlap", 60)),
            top_k=int(config.get("top_k", 3)))

    def validate(self, trace):
        return _load(self.root / "core/ai-mechanism/rag_trace.py", "rag_trace").validate_trace(trace)

    def build_visual_plan(self, trace):
        module = _load(self.root / "core/ai-mechanism/rag_visual_data.py", "rag_visual_data")
        return module.prepare_rag_visual_data(trace)

    def render(self, plan, manifest, output: Path):
        import subprocess
        import sys
        output = Path(output).resolve()
        manifest_path = Path(manifest["_path"]).resolve()
        beats = manifest.get("beats", [])
        trace_refs = {(manifest_path.parent / beat["trace"]).resolve()
                      for beat in beats if beat.get("trace")}
        if len(trace_refs) != 1 or sum(bool(beat.get("trace")) for beat in beats) != len(beats):
            raise ValueError("RAG manifest beats must all reference the same validated trace")
        mode = manifest.get("render_mode", "preview")
        command = [sys.executable, str(self.root / "pilots/v10_rag_poc/build_video.py"), mode,
                   "--trace", str(next(iter(trace_refs))), "--manifest", str(manifest_path),
                   "--output-dir", str(output.parent), "--silent"]
        subprocess.run(command, cwd=self.root, check=True)
        rendered = output.parent / ("rag_video_preview.mp4" if mode == "preview" else "rag_video.mp4")
        if not rendered.is_file():
            raise FileNotFoundError(f"RAG renderer produced no media at {rendered}")
        if rendered != output:
            output.write_bytes(rendered.read_bytes())
        return output
