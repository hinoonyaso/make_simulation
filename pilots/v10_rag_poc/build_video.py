"""Render one validated AI execution trace through the V9 beat manifest."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEFAULT_MANIFEST = HERE / "visual_manifest.json"
THREE = ROOT / "pilots/v10_threejs_rag"
RAG_PHASE_IDS = ("chunking", "embeddings", "retrieval", "context")
sys.path.insert(0, str(ROOT))
from core.mechanism.timeline import build_timeline, timeline_hash, validate_timeline


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_trace(path: Path) -> dict:
    trace = json.loads(path.read_text(encoding="utf-8"))
    validator = load_module("rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
    errors = validator.validate_trace(trace)
    if errors:
        raise SystemExit("invalid AI execution trace: " + "; ".join(errors))
    return trace


def run(command: list[str], *, cwd: Path = ROOT, env=None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def load_manifest(path: Path, trace_path: Path) -> tuple[dict, list[float]]:
    validator = load_module("visual_manifest_validator", ROOT /
        "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py")
    errors, warnings = validator.validate(str(path))
    if errors:
        raise SystemExit("invalid V9 visual manifest: " + "; ".join(errors))
    for warning in warnings:
        print(f"WARN {warning}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if len(data["beats"]) != 4:
        raise SystemExit("RAG scene currently requires four manifest beats: chunking, vectors, retrieval, context")
    phase_ids = [beat.get("phase_id") for beat in data["beats"]]
    if phase_ids != list(RAG_PHASE_IDS):
        raise SystemExit(f"RAG manifest phases must match renderer transitions {list(RAG_PHASE_IDS)}; got {phase_ids}")
    declared = {(path.parent / beat["trace"]).resolve()
                for beat in data["beats"] if beat.get("trace")}
    if len(declared) != 1 or declared != {trace_path.resolve()} or any(not beat.get("trace") for beat in data["beats"]):
        raise SystemExit("manifest trace path does not resolve to the selected --trace input")
    return data, [float(beat["sec"]) for beat in data["beats"]]


def load_timeline(manifest: dict, timeline_path: Path | None) -> dict:
    if timeline_path:
        timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    else:
        timeline = build_timeline(manifest["beats"], fps=30, default_visual_goal="algorithm_flow")
    errors = validate_timeline(timeline, expected_phase_ids=list(RAG_PHASE_IDS))
    if errors:
        raise SystemExit("invalid shared RAG timeline: " + "; ".join(errors))
    if timeline["fps"] != 30:
        raise SystemExit("RAG renderers currently require a 30 fps shared timeline")
    timeline.setdefault("timeline_sha256", timeline_hash(timeline))
    durations = [(phase["presentation_end_frame"] - phase["presentation_start_frame"]) / timeline["fps"]
                 for phase in timeline["phases"]]
    for beat, duration in zip(manifest["beats"], durations):
        beat["sec"] = duration
    return timeline


def render_manim(mode: str, trace_path: Path, manifest_path: Path,
                 durations: list[float], timeline_path: Path, out_dir: Path) -> Path:
    size = "960,540" if mode == "preview" else "1920,1080"
    quality = "-ql" if mode == "preview" else "-qh"
    folder = out_dir / f"{mode}_manim"
    folder.mkdir(parents=True, exist_ok=True)
    log = out_dir / f"{mode}_manim.log"
    env = os.environ.copy()
    env["V10_AI_TRACE"] = str(trace_path.resolve())
    env["V10_RAG_DURATIONS"] = json.dumps(dict(zip(RAG_PHASE_IDS, durations)))
    env["V10_RAG_PHASE_IDS"] = json.dumps(RAG_PHASE_IDS)
    env["V10_RAG_TIMELINE_PATH"] = str(timeline_path.resolve())
    manim_bin = env.get("V10_MANIM_BIN")
    command = ([manim_bin] if manim_bin else ["uv", "run", "manim"])
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run([*command, quality, "--fps", "30", "--resolution", size,
                        "--disable_caching", "--media_dir", str(folder),
                        str(HERE / "rag_mechanism_scene.py"), "RAGMechanismPoC"],
                       cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True)
    resolution = "540p30" if mode == "preview" else "1080p30"
    return folder / f"videos/rag_mechanism_scene/{resolution}/RAGMechanismPoC.mp4"


def threejs_runtime_info() -> dict:
    if not (THREE / "node_modules/three").exists() or not (THREE / "node_modules/playwright").exists():
        return {"status": "BLOCKED", "reason": "local Three.js or Playwright package is missing"}
    try:
        script = ("(async()=>{const {chromium}=require('playwright');"
                  "const b=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader']});"
                  "console.log(JSON.stringify({node:process.version,playwright:require('playwright/package.json').version,"
                  "chromium:b.version()}));await b.close()})().catch(e=>{console.error(e);process.exit(1)})")
        result = subprocess.run(["node", "-e", script], cwd=THREE, capture_output=True,
                                text=True, check=True, timeout=25)
        # The capture process serves local trace projection JSON to Chromium.
        # Verify loopback binding before routing instead of discovering a blocked
        # WSL/container network namespace after a full Manim render.
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
        versions = json.loads(result.stdout.strip().splitlines()[-1])
        return {"status": "PASS", "version": versions}
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
            IndexError, json.JSONDecodeError) as exc:
        detail = getattr(exc, "stderr", None)
        return {"status": "BLOCKED", "reason": str(detail).strip() if detail else str(exc)}


def threejs_available() -> bool:
    return threejs_runtime_info().get("status") == "PASS"


def scene_digest() -> str:
    digest = hashlib.sha256()
    for relative in ("index.html", "src/main.js", "src/style.css", "scripts/build_projection.py",
                     "scripts/capture_video.js", "package-lock.json"):
        path = THREE / relative
        digest.update(relative.encode()); digest.update(path.read_bytes())
    return digest.hexdigest()


def render_threejs(trace_path: Path, duration: float, out_dir: Path, mode: str,
                   timeline_hash_value: str, phase_start_frame: int, phase_end_frame: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    projection_path = out_dir / "embedding_space_3d.json"
    video_path = out_dir / "embedding_threejs.mp4"
    served_dir = THREE / "output"
    served_dir.mkdir(parents=True, exist_ok=True)
    fd, served_name = tempfile.mkstemp(prefix="rag-projection-", suffix=".json", dir=served_dir)
    os.close(fd)
    served_projection = Path(served_name)
    env = os.environ.copy()
    env.update({"V10_AI_TRACE": str(trace_path.resolve()),
                "V10_THREE_PROJECTION": str(served_projection.resolve()),
                "V10_THREE_VIDEO": str(video_path.resolve()),
                "V10_THREE_DURATION": str(duration), "V10_THREE_FPS": "30",
                "V10_THREE_TIMELINE_HASH": timeline_hash_value,
                "V10_THREE_START_FRAME": str(phase_start_frame),
                "V10_THREE_END_FRAME": str(phase_end_frame)})
    try:
        run(["npm", "run", "build:data"], cwd=THREE, env=env)
        projection = json.loads(served_projection.read_text(encoding="utf-8"))
        shutil.copyfile(served_projection, projection_path)
        manifest = video_path.with_suffix(".manifest.json")
        current = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
        expected = {"source_trace_sha256": projection["source_trace_sha256"],
                    "scene_sha256": scene_digest(), "duration_sec": duration,
                    "fps": 30, "width": 1920, "height": 1080}
        fresh = video_path.is_file() and all(current.get(key) == value for key, value in expected.items())
        if fresh:
            print("Reusing Three.js capture with matching trace, scene code and render options")
        else:
            run(["npm", "run", "render:video"], cwd=THREE, env=env)
        if not video_path.is_file():
            raise RuntimeError(f"Three.js capture did not produce {video_path}")
        return video_path
    finally:
        served_projection.unlink(missing_ok=True)


def has_vectors(trace: dict) -> bool:
    vector_inputs = [item for item in trace.get("inputs", []) if item.get("kind") == "query"]
    vector_values = [item for item in trace.get("intermediate_values", [])
                     if item.get("kind") in {"embedding", "feature_vector"}]
    return bool(vector_inputs and vector_values and
                isinstance(vector_inputs[0].get("embedding", vector_inputs[0].get("features")), list))


def integrate_threejs(base_video: Path, segment: Path, mode: str, start: float,
                      segment_duration: float, total: float, out_dir: Path,
                      timeline: dict) -> Path:
    target = out_dir / f"{mode}_with_threejs.mp4"
    width, height = (960, 540) if mode == "preview" else (1920, 1080)
    phase = next(item for item in timeline["phases"] if item["phase_id"] == "embeddings")
    start_frame = phase["presentation_start_frame"]
    end_frame = phase["presentation_end_frame"]
    total_frames = timeline["total_frames"]
    segment_frames = end_frame - start_frame
    filters = []
    labels = []
    split_base = start_frame > 0 and end_frame < total_frames
    before_source = "[base0]" if split_base else "[0:v]"
    after_source = "[base1]" if split_base else "[0:v]"
    if start_frame > 0:
        filters.append(f"{before_source}trim=start_frame=0:end_frame={start_frame},setpts=N/(30*TB),fps=30,"
                       f"scale={width}:{height},setsar=1[v0];")
        labels.append("[v0]")
    filters.append(f"[1:v]trim=start_frame=0:end_frame={segment_frames},setpts=N/(30*TB),fps=30,"
                   f"scale={width}:{height},setsar=1[v1];")
    labels.append("[v1]")
    if end_frame < total_frames:
        filters.append(f"{after_source}trim=start_frame={end_frame}:end_frame={total_frames},setpts=N/(30*TB),fps=30,"
                       f"scale={width}:{height},setsar=1[v2];")
        labels.append("[v2]")
    if split_base:
        filters.insert(0, "[0:v]split=2[base0][base1];")
    graph = "".join(filters) + f"{''.join(labels)}concat=n={len(labels)}:v=1:a=0[outv]"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(base_video), "-i", str(segment),
         "-filter_complex", graph, "-map", "[outv]", "-frames:v", str(total_frames), "-r", "30",
         "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)])
    from core.mechanism.run_management import media_metadata
    actual = media_metadata(target)
    if actual["frame_count"] != total_frames:
        raise RuntimeError(f"RAG Manim/Three.js output has {actual['frame_count']} frames; timeline requires {total_frames}")
    projection = json.loads((out_dir / "embedding_space_3d.json").read_text(encoding="utf-8"))
    out_dir.joinpath("embedding_segment_manifest.json").write_text(json.dumps({
        "schema": "v10-rag-embedding-segment/v1", "trace_id": projection["trace_id"],
        "query_id": projection["query_id"],
        "chunk_ids": [point["id"] for point in projection["points"] if point["kind"] == "chunk"],
        "retrieval": projection["retrieval"],
        "video_timeline": {"start_frame": phase["presentation_start_frame"],
                            "end_frame": phase["presentation_end_frame"],
                            "start_sec": phase["presentation_start_sec"],
                            "end_sec": phase["presentation_end_sec"],
                            "source_start_sec": 0, "source_end_sec": segment_duration,
                            "hold_last_frame_sec": 0, "fps": timeline["fps"],
                            "timeline_sha256": timeline["timeline_sha256"]},
        "timestamp_semantics": "presentation time; AI trace contains no per-operation execution timestamps",
        "source_trace_sha256": projection["source_trace_sha256"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def validate_video(path: Path, mode: str) -> None:
    if not path.is_file():
        raise SystemExit(f"render did not produce video: {path}")
    min_width, min_height = ((960, 540) if mode == "preview" else (1920, 1080))
    run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(path),
         "--min-width", str(min_width), "--min-height", str(min_height),
         "--fps", "30", "--full-decode"])


def compose_audio(video: Path, source: Path, audio_manifest: Path, captions_path: Path,
                  total: float, out_dir: Path, mode: str) -> Path:
    records = json.loads(audio_manifest.read_text(encoding="utf-8"))
    cues = json.loads(captions_path.read_text(encoding="utf-8"))
    if not records or abs(float(records[-1]["end"]) - total) > .12:
        raise SystemExit("audio timing manifest end must match the V9 video timeline")
    audio_cues = []
    for cue in cues:
        if cue["end"] > total or cue["start"] < 0 or cue["end"] <= cue["start"]:
            raise SystemExit("caption timing contains a cue outside the configured V9 timeline")
        audio_cues.append(cue)
    srt = out_dir / "subtitles.ko.srt"
    def stamp(seconds):
        ms = round(seconds * 1000); hh, ms = divmod(ms, 3600000)
        mm, ms = divmod(ms, 60000); ss, ms = divmod(ms, 1000)
        return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
    srt.write_text("\n\n".join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['caption']}"
                                  for i, c in enumerate(audio_cues)) + "\n", encoding="utf-8")
    target = out_dir / ("rag_video_preview.mp4" if mode == "preview" else "rag_video.mp4")
    subtitle_size = 12 if mode == "preview" else 18
    style = (f"FontName=NanumGothic,FontSize={subtitle_size},PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00202020,BorderStyle=1,Outline=1,Shadow=0,MarginV=18")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(source),
         "-filter_complex", f"[0:v]subtitles='{srt}':force_style='{style}'[v]",
         "-map", "[v]", "-map", "1:a:0", "-t", str(total), "-r", "30", "-c:v", "libx264",
         "-threads", "2", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(target)])
    (out_dir / "caption_timing.json").write_text(json.dumps(audio_cues, ensure_ascii=False, indent=2)+"\n",
                                                   encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preview", "final"), nargs="?", default="preview")
    parser.add_argument("--trace", type=Path, default=HERE / "data/ai_trace.json")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=HERE / "output")
    parser.add_argument("--timeline", type=Path, help="shared mechanism-timeline/v1 contract")
    parser.add_argument("--silent", action="store_true", help="skip narration and caption assembly")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--with-threejs", action="store_true", help="require the 3D embedding renderer")
    group.add_argument("--auto-threejs", action="store_true", help="use 3D projection when useful and available")
    parser.add_argument("--audio-source", type=Path)
    parser.add_argument("--audio-manifest", type=Path)
    parser.add_argument("--caption-timing", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trace_path, manifest_path = args.trace.resolve(), args.manifest.resolve()
    trace = validate_trace(trace_path)
    top_k = max((len(item.get("retrieved_ids", [])) for item in trace.get("outputs", [])
                 if isinstance(item, dict)), default=0)
    if top_k > 5:
        raise SystemExit("current Manim context view supports Top-K up to 5; trace ranking itself remains valid")
    manifest, _ = load_manifest(manifest_path, trace_path)
    timeline = load_timeline(manifest, args.timeline)
    durations = [(phase["presentation_end_frame"] - phase["presentation_start_frame"]) / timeline["fps"]
                 for phase in timeline["phases"]]
    total = sum(durations)
    timeline_path = args.timeline.resolve() if args.timeline else args.output_dir / "timeline.json"
    if not args.timeline:
        timeline_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    embeddings_phase = next(item for item in timeline["phases"] if item["phase_id"] == "embeddings")
    env = os.environ.copy()
    env["V10_AI_TRACE"] = str(trace_path)
    env["V10_RAG_DURATIONS"] = json.dumps(durations)
    print(f"Trace validated: {trace['trace_id']} · {len(trace['intermediate_values'])} values")
    print(f"V9 manifest: {len(durations)} beats · {total:g}s · tools={','.join(b['tool'] for b in manifest['beats'])}")

    use_three = args.with_threejs
    selection_reason = "Three.js explicitly required" if args.with_threejs else "Manim only"
    attempts = []
    if args.auto_threejs and has_vectors(trace) and threejs_available():
        use_three = True
        selection_reason = "recorded query/chunk vectors and local browser runtime available"
    elif args.auto_threejs:
        selection_reason = ("recorded vector representation unavailable" if not has_vectors(trace)
                            else "local Three.js/browser dependency unavailable")
        attempts.append({"renderer": "threejs", "status": "skipped", "reason": selection_reason})
        print("Three.js fallback: useful vector view unavailable or browser dependencies missing; using Manim")
    if use_three and not has_vectors(trace):
        if args.with_threejs:
            raise SystemExit("Three.js requires recorded query and chunk vectors; use the Manim score view")
        use_three = False
        selection_reason = "trace has no query/chunk vectors"
        attempts.append({"renderer": "threejs", "status": "skipped", "reason": selection_reason})
        print("Three.js fallback: trace has no vector representation; using Manim")

    manim_attempt = {"renderer": "manim", "status": "started"}
    attempts.append(manim_attempt)
    try:
        manim_video = render_manim(args.mode, trace_path, manifest_path, durations, timeline_path, args.output_dir)
        if not manim_video.is_file():
            raise RuntimeError(f"Manim render missing: {manim_video}")
        manim_attempt.update({"status": "success", "output": str(manim_video)})
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        manim_attempt.update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
        (args.output_dir / "renderer_selection.json").write_text(json.dumps({
            "requested": "threejs_required" if args.with_threejs else "auto" if args.auto_threejs else "manim_only",
            "selected": None, "reason": "base Manim render failed", "trace_id": trace["trace_id"],
            "renderer_attempts": attempts,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise
    video = manim_video
    if use_three:
        beat_start = sum(durations[:1])
        segment = None
        try:
            attempts.append({"renderer": "threejs", "status": "started"})
            segment = render_threejs(trace_path, durations[1], args.output_dir, args.mode,
                                     timeline["timeline_sha256"], embeddings_phase["presentation_start_frame"],
                                     embeddings_phase["presentation_end_frame"])
            video = integrate_threejs(manim_video, segment, args.mode, beat_start,
                                      durations[1], total, args.output_dir, timeline)
            attempts[-1].update({"status": "success", "output": str(video)})
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            attempts[-1].update({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)})
            if args.with_threejs:
                (args.output_dir / "renderer_selection.json").write_text(json.dumps({
                    "requested": "threejs_required", "selected": None,
                    "reason": "required Three.js renderer failed", "trace_id": trace["trace_id"],
                    "renderer_attempts": attempts,
                }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                raise
            selection_reason = f"Three.js failed ({type(exc).__name__}: {exc}); full Manim timeline retained"
            print(f"Three.js fallback: {type(exc).__name__}: {exc}; keeping complete Manim render")
            use_three = False
    (args.output_dir / "renderer_selection.json").write_text(json.dumps({
        "requested": "threejs_required" if args.with_threejs else
                     "auto" if args.auto_threejs else "manim_only",
        "selected": "manim+threejs" if use_three else "manim",
        "reason": selection_reason,
        "trace_id": trace["trace_id"],
        "timeline_sha256": timeline["timeline_sha256"],
        "timeline_frame_count": timeline["total_frames"],
        "timeline": str(timeline_path),
        "threejs_interval_sec": {"start": durations[0], "end": durations[0]+durations[1]}
            if use_three else None,
        "threejs_interval_frames": {"start": embeddings_phase["presentation_start_frame"],
                                    "end": embeddings_phase["presentation_end_frame"]}
            if use_three else None,
        "renderer_attempts": attempts,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audio_args = (args.audio_source, args.audio_manifest, args.caption_timing)
    if not args.silent and any(audio_args) and not all(audio_args):
        raise SystemExit("audio requires --audio-source, --audio-manifest and --caption-timing together")
    if args.silent:
        target = args.output_dir / ("rag_video_preview.mp4" if args.mode == "preview" else "rag_video.mp4")
        shutil.copyfile(video, target)
        print(f"AUDIO ADAPTER: skipped by --silent; video-only output {target}")
    elif all(audio_args):
        target = compose_audio(video, *audio_args, total, args.output_dir, args.mode)
    else:
        target = args.output_dir / ("rag_video_preview.mp4" if args.mode == "preview" else "rag_video.mp4")
        shutil.copyfile(video, target)
        print("AUDIO ADAPTER: no measured narration inputs supplied; rendering video-only")
    validate_video(target, args.mode)
    print(f"PASS: {'Manim + Three.js' if use_three else 'Manim'} -> {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
