#!/usr/bin/env python3
"""Validate/execute a supported AI trace and produce a RAG mechanism video."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots/v10_rag_poc"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True,
                        help="supported topic: rag (other AI topics are not implemented yet)")
    parser.add_argument("--trace", type=Path, default=PILOT / "data/ai_trace.json",
                        help="validated AI execution trace to replay")
    parser.add_argument("--document", type=Path, help="new UTF-8 document for local lexical execution")
    parser.add_argument("--question", help="query for --document")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=60)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--render", choices=("auto", "manim"), default="auto")
    parser.add_argument("--preview-only", action="store_true", help="stop after preview technical QA")
    parser.add_argument("--silent", action="store_true", help="render without narration and captions")
    parser.add_argument("--output-root", type=Path, default=PILOT / "output/runs")
    parser.add_argument("--durations", nargs=4, type=float,
                        metavar=("CHUNK", "VECTOR", "RETRIEVAL", "CONTEXT"),
                        help="optional V9 manifest beat durations in seconds")
    args = parser.parse_args()

    if args.topic.casefold() != "rag":
        raise SystemExit(f"unsupported topic {args.topic!r}; implemented topics: rag")
    if bool(args.document) != bool(args.question):
        raise SystemExit("--document and --question must be supplied together")
    if args.document:
        execute = load_module("execute_local_rag", ROOT / "core/ai-mechanism/execute_local_rag.py")
        trace = execute.execute_lexical_rag(args.document.read_text(encoding="utf-8"),
            args.question, chunk_size=args.chunk_size, overlap=args.overlap, top_k=args.top_k)
        trace["provenance"]["source_document"] = str(args.document.resolve())
        trace["provenance"]["source_document_sha256"] = trace["inputs"][0]["sha256"]
        trace_path = None
        mode = "fresh local lexical RAG execution"
    else:
        trace_path = args.trace.resolve()
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        mode = "validated trace replay"
    validator = load_module("rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
    errors = validator.validate_trace(trace)
    if errors:
        raise SystemExit("trace validation failed: " + "; ".join(errors))

    if args.document:
        run_key = json.dumps({"document_sha256": trace["inputs"][0]["sha256"],
                              "question": args.question, "chunk_size": args.chunk_size,
                              "overlap": args.overlap, "top_k": args.top_k},
                             ensure_ascii=False, sort_keys=True).encode("utf-8")
    else:
        run_key = trace_path.read_bytes()
    digest = hashlib.sha256(trace.get("trace_id", "").encode() + run_key).hexdigest()[:10]
    run_dir = args.output_root.resolve() / f"rag-{digest}"
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.document:
        stable_trace = run_dir / "ai_trace.json"
        stable_trace.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        trace_path = stable_trace

    manifest = json.loads((PILOT / "visual_manifest.json").read_text(encoding="utf-8"))
    durations = args.durations or [float(beat["sec"]) for beat in manifest["beats"]]
    if any(value <= 0 or value > 60 for value in durations):
        raise SystemExit("each beat duration must be >0 and <=60 seconds")
    relative_trace = Path(os.path.relpath(trace_path, run_dir)).as_posix()
    lexical = trace.get("system", {}).get("vector_representation", "").startswith("lexical TF-IDF")
    for index, beat in enumerate(manifest["beats"]):
        beat["sec"] = durations[index]
        beat["trace"] = relative_trace
    if lexical:
        manifest["beats"][1]["text"] = "청크와 질문을 단어별 TF-IDF 특징 벡터로 바꿉니다."
        manifest["beats"][1]["caption"] = "단어별 TF-IDF 특징 벡터입니다. 의미 임베딩은 아닙니다."
        manifest["beats"][3]["text"] = "상위로 선택된 원문 조각을 컨텍스트로 묶습니다. 이 실행에는 답변 생성 모델이 없습니다."
        manifest["beats"][3]["caption"] = "검색 컨텍스트를 조립합니다. 답변 생성은 실행하지 않았습니다."
    manifest_path = run_dir / "visual_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_validator = load_module("visual_manifest_validator", ROOT /
        "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py")
    manifest_errors, warnings = manifest_validator.validate(str(manifest_path))
    if manifest_errors:
        raise SystemExit("manifest validation failed: " + "; ".join(manifest_errors))
    for warning in warnings:
        print(f"WARN {warning}")

    render_args = ["--auto-threejs"] if args.render == "auto" else []
    if args.silent:
        render_args.append("--silent")
    build = PILOT / "build_video.py"
    build_args = ["--trace", str(trace_path), "--manifest", str(manifest_path),
                  "--output-dir", str(run_dir), *render_args]
    def reported_path(path):
        try:
            return str(path.resolve().relative_to(ROOT))
        except ValueError:
            return str(path.resolve())
    report = {"topic": "rag", "run_mode": mode, "trace_id": trace["trace_id"],
              "trace": reported_path(trace_path),
              "manifest": reported_path(manifest_path),
              "renderer_policy": "Manim; add Three.js for recorded vectors when locally available"
                  if args.render == "auto" else "Manim only",
              "preview": {"status": "NOT_RUN"}, "final": {"status": "NOT_RUN"}}
    report_path = run_dir / "production_report.json"
    try:
        subprocess.run([sys.executable, str(build), "preview", *build_args], cwd=ROOT, check=True)
        report["preview"] = {"status": "PASS", "media": reported_path(run_dir / "rag_video_preview.mp4"),
                             "technical_qa": "validate_delivery.py: 540p30, full decode",
                             "renderer_selection": json.loads((run_dir / "renderer_selection.json").read_text(encoding="utf-8"))}
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.preview_only:
            subprocess.run([sys.executable, str(build), "final", *build_args], cwd=ROOT, check=True)
            report["final"] = {"status": "PASS", "media": reported_path(run_dir / "rag_video.mp4"),
                               "technical_qa": "validate_delivery.py: 1080p30, full decode"}
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, subprocess.CalledProcessError) as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    print(f"PASS: {mode} -> {report_path}")


if __name__ == "__main__":
    main()
