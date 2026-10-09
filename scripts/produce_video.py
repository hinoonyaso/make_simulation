#!/usr/bin/env python3
"""Run-isolated execution or validated trace replay for registered mechanisms."""
from __future__ import annotations

import argparse
from importlib import metadata as importlib_metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import hashlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.mechanism.protocol import MechanismRequest
from core.mechanism.registry import MechanismRegistry
from core.mechanism.run_management import (asset_tree_hash, file_hash, make_run_identity, media_metadata,
                                           prepare_run_dir, validate_replay_trace)
from core.mechanism.storyboard import build_storyboard
from core.mechanism.timeline import build_timeline, validate_timeline
from core.mechanism.renderer_routing import VISUAL_GOALS, decide_renderer


def _load_json(path: Path, label: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{label} root must be a JSON object: {path}")
    return data


def _validate_manifest(path: Path) -> None:
    import importlib.util
    spec = importlib.util.spec_from_file_location("v9_manifest_validator",
        ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors, warnings = module.validate(str(path))
    if errors:
        raise ValueError("generated V9 manifest invalid: " + "; ".join(errors))
    for warning in warnings:
        print(f"WARN {warning}")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_rag(trace_path: Path, run_dir: Path, *, preview: bool, render: str,
             timeline_path: Path | None = None) -> Path:
    render_root = run_dir / "rag_render"
    command = [sys.executable, str(ROOT / "scripts/produce_ai_video.py"), "--topic", "rag",
               "--trace", str(trace_path), "--render", render, "--silent",
               "--output-root", str(render_root)]
    if timeline_path:
        command.extend(["--timeline", str(timeline_path)])
    if preview:
        command.append("--preview-only")
    subprocess.run(command, cwd=ROOT, check=True)
    reports = list(render_root.glob("rag-*/production_report.json"))
    if len(reports) != 1:
        raise RuntimeError(f"RAG renderer report missing or ambiguous in {render_root}")
    report = _load_json(reports[0], "RAG production report")
    key = "preview" if preview else "final"
    media_info = report.get(key, {})
    if media_info.get("status") != "PASS":
        raise RuntimeError(f"RAG {key} render did not pass: status={media_info.get('status')!r}")
    media_value = media_info.get("media")
    if not media_value:
        raise RuntimeError(f"RAG renderer did not report {key} media")
    media = Path(media_value)
    if not media.is_absolute():
        media = ROOT / media
    if not media.is_file() or media.stat().st_size == 0:
        raise RuntimeError(f"RAG {key} media is missing or empty: {media}")
    expected_width = 960 if preview else 1920
    expected_height = 540 if preview else 1080
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(media),
                    "--min-width", str(expected_width), "--min-height", str(expected_height),
                    "--fps", "30", "--full-decode"], cwd=ROOT, check=True)
    metadata = media_metadata(media)
    if metadata["width"] != expected_width or metadata["height"] != expected_height:
        raise RuntimeError(f"RAG {key} dimensions are {metadata['width']}x{metadata['height']}, "
                           f"expected {expected_width}x{expected_height}")
    destination = run_dir / "preview.mp4" if preview else run_dir / "final.mp4"
    shutil.copy2(media, destination)
    if destination.resolve() != media.resolve() and file_hash(destination) != file_hash(media):
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"RAG {key} copy hash mismatch")
    return destination


def _build_run_timeline(topic: str, trace: dict, manifest: dict,
                        visual_goal: str) -> dict:
    fps = 30
    source_range = None
    phase_source = {}
    if topic == "robot_kinematics":
        times = [float(sample["t"]) for sample in trace.get("samples", [])]
        if len(times) < 2:
            raise ValueError("H1 timeline requires at least two source trace timestamps")
        source_range = (times[0], times[-1])
        beats = manifest["beats"]
        phase_durations = {beat["phase_id"]: float(beat["sec"]) for beat in beats}
        motion_duration = phase_durations["joint_state"]
        source_duration = times[-1] - times[0]
        phase_source = {
            "robot_setup": {"source_start_sec": times[0], "source_end_sec": times[0],
                             "playback_mode": "hold", "visual_goal": "spatial_relationship"},
            "joint_state": {"source_start_sec": times[0], "source_end_sec": times[-1],
                            "playback_mode": "slow_motion" if motion_duration > source_duration else "normal_speed",
                            "visual_goal": "motion_3d"},
            "end_effector_motion": {"source_start_sec": times[-1], "source_end_sec": times[-1],
                                    "playback_mode": "hold_and_analysis", "visual_goal": "spatial_relationship"},
        }
    elif topic == "mcu_pid":
        samples = trace.get("payload", {}).get("samples", [])
        times = [float(sample["time_s"]) for sample in samples]
        if len(times) >= 2:
            source_range = (times[0], times[-1])
            for beat in manifest["beats"]:
                phase_source[beat["phase_id"]] = {"source_start_sec": times[0], "source_end_sec": times[-1],
                                                  "playback_mode": "normal_speed",
                                                  "visual_goal": "numerical_explanation"}
    return build_timeline(manifest["beats"], fps=fps, source_range=source_range,
                          phase_source=phase_source, default_visual_goal=visual_goal)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", required=True, help="registered mechanism ID or unique alias")
    parser.add_argument("--mode", choices=("executable", "replay", "illustration"), default="executable")
    parser.add_argument("--render", choices=("auto", "manim", "blender"), default="auto")
    parser.add_argument("--visual-goal", choices=VISUAL_GOALS, default="auto",
                        help="explanation target; auto resolves deterministically from topic/trace")
    parser.add_argument("--preview", action="store_true", help="540p30 technical preview; default is 1080p30")
    parser.add_argument("--config", type=Path, help="JSON adapter options")
    parser.add_argument("--trace", type=Path, help="validated input trace for --mode replay")
    parser.add_argument("--document", type=Path, help="UTF-8 source document for RAG")
    parser.add_argument("--question", help="query paired with --document")
    parser.add_argument("--input", type=Path, help="input data; accepted only by an implementing adapter")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output/runs",
                        help="run collection root; each invocation gets a unique child directory")
    parser.add_argument("--run-id", help="explicit directory ID; an existing run is never overwritten")
    parser.add_argument("--reuse", dest="reuse", action="store_true", default=True,
                        help="reuse a completed identical run (default)")
    parser.add_argument("--no-reuse", dest="reuse", action="store_false",
                        help="refuse an existing run directory instead of reusing it")
    parser.add_argument("--force", action="store_true",
                        help="bypass reuse and create a timestamped sibling; preserves the original run")
    parser.add_argument("--asset", help="asset ID required by a robotics adapter")
    parser.add_argument("--robot", help="robot model ID for robotics adapters")
    parser.add_argument("--model", type=Path, help="local model checkpoint for real object_detection inference")
    parser.add_argument("--narration-duration", type=float,
                        help="measured total TTS duration in seconds for beat timing allocation")
    args = parser.parse_args()
    if args.force and args.run_id:
        parser.error("--force cannot be combined with --run-id; choose a new explicit run ID instead")
    if bool(args.document) != bool(args.question):
        parser.error("--document and --question must be supplied together")
    if args.mode == "replay" and not args.trace:
        parser.error("--mode replay requires --trace")
    if args.mode != "replay" and args.trace:
        parser.error("--trace is accepted only with --mode replay")
    if args.mode == "illustration":
        parser.error("illustration mode is not implemented by V11.2 adapters; no execution will be implied")

    registry = MechanismRegistry()
    capability = registry.resolve(args.topic)
    if capability is None:
        resolution = registry.resolve_detailed(args.topic)
        if resolution["status"] == "ambiguous":
            parser.error(f"ambiguous topic {args.topic!r}; choose: {', '.join(resolution['candidates'])}")
        parser.error(f"unknown topic {args.topic!r}; inspect scripts/inspect_capabilities.py")
    topic = capability["topic"]
    if capability["implementation_status"] != "ready":
        parser.error(f"unsupported: {topic}; status={capability['implementation_status']}")
    if args.input and topic != "object_detection":
        parser.error(f"{topic} has no input-image/data adapter")
    if args.model and topic != "object_detection":
        parser.error(f"{topic} has no model-checkpoint adapter")

    adapter = registry.load_adapter(topic)
    config = _load_json(args.config, "adapter config") if args.config else {}
    if topic == "object_detection":
        if args.mode == "executable":
            if not args.input or not args.model:
                parser.error("actual object_detection inference requires both --input and --model")
            config.update({"image": str(args.input.resolve()), "model": str(args.model.resolve())})
        elif args.input or args.model:
            parser.error("object_detection replay uses image provenance embedded in the trace; omit --input/--model")
    if args.render == "blender" and topic != "robot_kinematics":
        parser.error("--render blender is currently available only for robot_kinematics")
    if topic == "rag":
        rag_manifest = ROOT / "pilots/v10_rag_poc/visual_manifest.json"
        config["manifest_sha256"] = file_hash(rag_manifest)
        if args.mode == "executable" and not args.document and not args.config:
            # Keep the repository's checked-in V10 trace as the explicit default input.
            args.mode = "replay"
            args.trace = ROOT / "pilots/v10_rag_poc/data/ai_trace.json"
        if args.mode == "executable" and args.document:
            config.update({"document": args.document.read_text(encoding="utf-8"), "question": args.question})
        elif args.mode == "replay":
            config["trace_path"] = str(args.trace.resolve())
    simulation_tmp = None
    if topic == "robot_kinematics":
        if args.robot and args.robot != "unitree_h1":
            parser.error("robot_kinematics currently supports only unitree_h1")
        if args.asset and args.asset != "blender.unitree_h1.v1":
            parser.error("robot_kinematics requires asset blender.unitree_h1.v1")

    if args.mode == "replay":
        trace = _load_json(args.trace.resolve(), "trace")
        errors = (adapter.validate(trace) if topic == "object_detection" else
                  validate_replay_trace(topic, capability["trace_schema"], trace, adapter))
        if errors:
            parser.error("trace validation failed: " + "; ".join(errors))
    else:
        if topic == "robot_kinematics":
            simulation_tmp = tempfile.TemporaryDirectory(prefix="v11_h1_trace_")
            config["output_dir"] = simulation_tmp.name
        prepared = adapter.prepare(MechanismRequest(topic=topic, options=config))
        trace = adapter.execute(prepared)
        errors = adapter.validate(trace)
        if errors:
            if simulation_tmp:
                simulation_tmp.cleanup()
            parser.error("adapter trace validation failed: " + "; ".join(errors))
        if simulation_tmp:
            simulation_tmp.cleanup()
            simulation_tmp = None

    plan = adapter.build_visual_plan(trace)
    plan.setdefault("title", {
        "quantization": "실제 수치로 보는 가중치 양자화",
        "nms": "합성 후보로 계산하는 IoU 기반 NMS",
        "mcu_pid": "엔코더 피드백을 사용하는 PID 모터 시뮬레이션",
        "robot_kinematics": "MuJoCo 로봇팔의 관절 상태와 끝단 이동",
        "self_attention": "토큰 관계 점수로 계산하는 Self-Attention",
    }.get(topic, topic))
    mode_name = "preview" if args.preview else "final"
    if topic == "rag":
        manifest = _load_json(ROOT / "pilots/v10_rag_poc/visual_manifest.json", "RAG manifest")
        for beat in manifest.get("beats", []):
            beat["trace"] = "ai_trace.json"
    else:
        manifest = build_storyboard(topic, trace, plan, "trace.json", render_mode=mode_name,
                                    measured_narration_seconds=args.narration_duration)
    model_path = Path(config.get("model", ROOT / "assets/unitree_h1/mjcf/h1_with_hand.xml")) \
        if topic == "robot_kinematics" else None
    try:
        decision = decide_renderer(topic=topic, requested_renderer=args.render,
                                   visual_goal=args.visual_goal, trace=trace, model_path=model_path)
    except ValueError as exc:
        parser.error(str(exc))
    if decision["status"] != "PASS" or not decision.get("selected_renderer"):
        parser.error("renderer preflight blocked: " + json.dumps(decision, ensure_ascii=False))
    effective_renderer = decision["selected_renderer"]
    resolved_goal = decision["visual_goal"]
    timeline = _build_run_timeline(topic, trace, manifest, resolved_goal)
    if (errors := validate_timeline(timeline, expected_phase_ids=[b["phase_id"] for b in manifest["beats"]],
                                    source_range=tuple(timeline["source_range_sec"])
                                    if timeline["source_range_sec"] else None)):
        parser.error("invalid mechanism timeline: " + "; ".join(errors))

    renderer_preflight = decision.get("runtime_preflight", {})
    renderer_version = renderer_preflight.get("version")
    if renderer_preflight.get("manim") and renderer_preflight.get("threejs"):
        renderer_version = (f"{renderer_preflight['manim'].get('version', 'Manim unknown')} + "
                            f"Node {renderer_preflight['threejs'].get('version', {}).get('node', 'unknown')} / "
                            f"Playwright {renderer_preflight['threejs'].get('version', {}).get('playwright', 'unknown')} / "
                            f"{renderer_preflight['threejs'].get('version', {}).get('chromium', 'Chromium unknown')}")
    elif not renderer_version and renderer_preflight.get("manim"):
        renderer_version = renderer_preflight["manim"].get("version")
    asset_hash = None
    if (effective_renderer == "blender_h1_trace_playback" and model_path is not None
            and model_path.is_file()):
        model_root = model_path.resolve().parent.parent
        asset_hash = asset_tree_hash(model_root) if topic == "robot_kinematics" else file_hash(model_path)
    identity_config = {key: value for key, value in config.items() if key != "output_dir"}
    identity_config["visual_goal"] = resolved_goal
    identity_config["timeline_sha256"] = timeline["timeline_sha256"]
    if renderer_version:
        identity_config["renderer_version"] = renderer_version
    if asset_hash:
        identity_config["asset_sha256"] = asset_hash
    if args.narration_duration is not None:
        identity_config["measured_narration_seconds"] = args.narration_duration
    identity = make_run_identity(topic=topic, config=identity_config, trace=trace, mode=args.mode,
        renderer=f"{effective_renderer}:{'preview' if args.preview else 'final'}", config_path=args.config,
        trace_path=args.trace if args.mode == "replay" else None,
        request={"topic": topic, "mode": args.mode, "robot": args.robot, "asset": args.asset,
                 "requested_renderer": args.render, "visual_goal": resolved_goal},
        visual_goal=resolved_goal, timeline=timeline, asset_hash=asset_hash,
        renderer_version=renderer_version)
    run_id = args.run_id or identity["run_id"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", run_id):
        parser.error("run ID must contain 1-128 letters, numbers, dots, underscores or hyphens")
    if args.force:
        run_id = f"{run_id}-rerun-{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}-{time.time_ns() % 1_000_000_000:09d}"
    try:
        run_dir, cache_hit = prepare_run_dir(args.output_dir, run_id, reuse=args.reuse,
                                            force=args.force, expected_identity=identity)
    except FileExistsError as exc:
        parser.error(str(exc))
    if cache_hit:
        cached_report = _load_json(run_dir / "production_report.json", "cached report")
        print(f"REUSED: {cached_report['media']}")
        if simulation_tmp:
            simulation_tmp.cleanup()
        return 0

    _write_json(run_dir / "request.json", {"topic": topic, "mode": args.mode,
        "config_path": str(args.config.resolve()) if args.config else None,
        "trace_path": str(args.trace.resolve()) if args.trace else None,
        "document_path": str(args.document.resolve()) if args.document else None,
        "question": args.question})
    _write_json(run_dir / "config.json", identity_config)
    trace_path = run_dir / ("ai_trace.json" if topic == "rag" else "trace.json")
    _write_json(trace_path, trace)
    timeline_path = run_dir / "timeline.json"
    _write_json(timeline_path, timeline)
    trace_digest = hashlib.sha256(trace_path.read_bytes()).hexdigest()
    if topic == "rag":
        preview = _run_rag(trace_path, run_dir, preview=args.preview,
                           render="auto" if effective_renderer == "manim+threejs" else "manim",
                           timeline_path=timeline_path)
        source_report = next((run_dir / "rag_render").glob("rag-*/production_report.json"))
        _write_json(run_dir / "visual_plan.json", plan)
        manifest = _load_json(source_report.parent / "visual_manifest.json", "RAG manifest")
        for beat in manifest.get("beats", []):
            beat["trace"] = trace_path.name
        _write_json(run_dir / "visual_manifest.json", manifest)
        _validate_manifest(run_dir / "visual_manifest.json")
        selected = _load_json(source_report.parent / "renderer_selection.json", "RAG renderer selection")
        renderer_backend = selected.get("selected") or "unknown"
        if renderer_backend != effective_renderer:
            if args.render != "auto" or effective_renderer != "manim+threejs" or renderer_backend != "manim":
                raise RuntimeError("RAG renderer changed after preflight and no recorded fallback is allowed: "
                                   + str(selected.get("reason")))
            from core.mechanism.renderer_routing import preflight
            fallback_preflight = preflight("manim", trace=trace)
            if fallback_preflight.get("status") != "PASS":
                raise RuntimeError("Three.js failed and Manim fallback preflight is unavailable: "
                                   + str(fallback_preflight))
            fallback_version = fallback_preflight.get("version")
            fallback_config = {key: value for key, value in identity_config.items()
                               if key != "renderer_version"}
            if fallback_version:
                fallback_config["renderer_version"] = fallback_version
            fallback_identity = make_run_identity(topic=topic, config=fallback_config, trace=trace,
                mode=args.mode, renderer=f"manim:{'preview' if args.preview else 'final'}",
                config_path=args.config, trace_path=args.trace if args.mode == "replay" else None,
                request={"topic": topic, "mode": args.mode, "robot": args.robot, "asset": args.asset,
                         "requested_renderer": args.render, "visual_goal": resolved_goal},
                visual_goal=resolved_goal, timeline=timeline, asset_hash=asset_hash,
                renderer_version=fallback_version)
            fallback_dir, fallback_cache = prepare_run_dir(args.output_dir, fallback_identity["run_id"],
                reuse=args.reuse, force=False, expected_identity=fallback_identity)
            if fallback_cache:
                cached = _load_json(fallback_dir / "production_report.json", "fallback cached report")
                print(f"REUSED fallback: {cached['media']}")
                return 0
            old_dir = run_dir
            old_preview = preview
            run_dir, identity, run_id = fallback_dir, fallback_identity, fallback_identity["run_id"]
            trace_path = run_dir / "ai_trace.json"
            shutil.copy2(old_dir / "ai_trace.json", trace_path)
            timeline_path = run_dir / "timeline.json"
            shutil.copy2(old_dir / "timeline.json", timeline_path)
            _write_json(run_dir / "config.json", fallback_config)
            _write_json(run_dir / "request.json", {"topic": topic, "mode": args.mode,
                "config_path": str(args.config.resolve()) if args.config else None,
                "trace_path": str(args.trace.resolve()) if args.trace else None,
                "document_path": str(args.document.resolve()) if args.document else None,
                "question": args.question})
            _write_json(run_dir / "visual_plan.json", plan)
            manifest = _load_json(source_report.parent / "visual_manifest.json", "fallback RAG manifest")
            for beat in manifest.get("beats", []):
                beat["trace"] = trace_path.name
            _write_json(run_dir / "visual_manifest.json", manifest)
            _validate_manifest(run_dir / "visual_manifest.json")
            destination = run_dir / ("preview.mp4" if args.preview else "final.mp4")
            shutil.copy2(old_preview, destination)
            if file_hash(old_preview) != file_hash(destination):
                raise RuntimeError("RAG fallback media copy hash mismatch")
            preview = destination
            renderer_backend = "manim"
            effective_renderer = "manim"
            resolved_goal = decision["visual_goal"]
            decision["rejected_candidates"].append({"renderer": "manim+threejs",
                "reason": selected.get("reason", "Three.js renderer failed during capture")})
            decision.update({"selected_renderer": "manim",
                "selection_reason": "Three.js capture failed at runtime; Manim fallback registered under its own identity",
                "capabilities": {"supported_topics": ["rag"],
                    "visual_goals": ["numerical_explanation", "algorithm_flow", "spatial_relationship", "comparative_analysis"],
                    "dimensions": "2d", "runtime": "manim", "supports_timeline": True},
                "runtime_preflight": fallback_preflight,
                "feature_loss": ["3D embedding projection; retained trace-ranked Manim view"],
                "status": "PASS"})
            selected["selected"] = "manim"
            selected["reason"] = decision["selection_reason"]
        renderer_details = selected
    else:
        _write_json(run_dir / "visual_plan.json", plan)
        for beat in manifest.get("beats", []):
            beat["trace"] = trace_path.name
        manifest_path = run_dir / "visual_manifest.json"
        _write_json(manifest_path, manifest)
        _validate_manifest(manifest_path)
        manifest["_path"] = str(manifest_path)
        manifest["render_mode"] = mode_name
        manifest["_trace_path"] = str(trace_path)
        manifest["_timeline_path"] = str(timeline_path)
        media_name = "preview.mp4" if args.preview else "final.mp4"
        if effective_renderer == "blender_h1_trace_playback":
            from core.mechanism.renderer import render_h1_blender
            preview = render_h1_blender(trace_path, run_dir / media_name, model_path,
                                         "preview" if args.preview else "final", timeline_path=timeline_path)
            renderer_details = _load_json(run_dir / "blender_backend/renderer_provenance.json",
                                          "Blender renderer provenance")
        else:
            preview = adapter.render(plan, manifest, run_dir / media_name)
        renderer_backend = effective_renderer
        if topic == "object_detection":
            renderer_details = {"backend": renderer_backend, "runtime": trace["model"]["runtime"],
                "runtime_version": trace["model"]["runtime_version"], "device": trace["model"]["device"],
                "model_sha256": trace["model"]["sha256"], "input_image_sha256": trace["input_image"]["sha256"],
                "raw_predictions": trace["raw_prediction_count"], "trace_candidates": trace["trace_candidate_count"],
                "confidence_pass": trace["confidence_pass_count"], "final_detections": len(trace["kept_ids"])}
        elif effective_renderer != "blender_h1_trace_playback":
            try:
                renderer_version = importlib_metadata.version("manim")
            except importlib_metadata.PackageNotFoundError:
                renderer_version = "unknown"
            renderer_details = {"backend": renderer_backend, "version": renderer_version,
                                "requested_renderer": args.render}
    media = Path(preview).resolve()
    actual_meta = media_metadata(media)
    if actual_meta["frame_count"] != timeline["total_frames"]:
        raise RuntimeError(f"render produced {actual_meta['frame_count']} frames; timeline requires {timeline['total_frames']}")
    report = {"topic": topic, "run_id": run_id, "base_run_id": identity["run_id"],
        "identity": identity, "mode": "trace_replay" if args.mode == "replay" else "executable_simulation",
        "render_mode": "preview" if args.preview else "final",
        "trace": str(trace_path), "trace_sha256": trace_digest,
        "manifest": str(run_dir / "visual_manifest.json"),
        "renderer": renderer_backend,
        "renderer_requested": args.render,
        "renderer_details": renderer_details,
        "renderer_decision": decision,
        "visual_goal": resolved_goal,
        "renderer_settings": identity["render_spec"],
        "timeline": str(timeline_path), "timeline_sha256": timeline["timeline_sha256"],
        "timeline_frame_count": timeline["total_frames"],
        "storyboard_phase_ids": [beat.get("phase_id") for beat in manifest.get("beats", [])],
        "media": str(media), "output_path": str(media), "media_sha256": file_hash(media),
        "media_metadata": actual_meta,
        "media_mode": "silent technical preview" if args.preview else "silent technical render",
        "narration": "NOT_GENERATED", "captions": "manifest text only; burned-in/audio sync NOT_RUN",
        "review": "NOT_RUN", "technical_decode": "PASS",
        "qa": {"technical": {"trace_schema_and_domain_validation": "PASS",
                              "trace_sha256": trace_digest, "manifest_validation": "PASS",
                              "media_full_decode_30fps": "PASS", "audio_track": "NOT_PRESENT"},
               "visual": "NOT_RUN", "educational": "NOT_RUN"},
        "limitations": trace.get("limitations", trace.get("model", {}).get("assumptions", []))}
    _write_json(run_dir / "production_report.json", report)
    _write_json(run_dir / "review_report.json", {
        "status": "NOT_RUN", "technical_review": "covered by production_report.qa.technical",
        "visual_review": "NOT_RUN", "educational_review": "NOT_RUN",
        "whole_video_motion_and_audio_playback": "NOT_RUN",
        "reason": "The common mechanism CLI has no connected Reviewer orchestration; do not infer review from decode or sampled frames."})
    print(f"PASS: {topic} {report['mode']} → {trace_path} → {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
