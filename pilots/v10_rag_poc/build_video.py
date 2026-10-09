"""Render the checked-in RAG trace; narration and the Three.js segment are optional adapters."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"
THREE = ROOT / "pilots/v10_threejs_rag"
THREE_VIDEO = THREE / "output/threejs_rag_3d.mp4"
SEGMENT_MAP = OUT / "embedding_segment_manifest.json"


def load_trace_validator():
    spec = importlib.util.spec_from_file_location(
        "rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_trace


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def render_manim(mode: str) -> Path:
    size = "960,540" if mode == "preview" else "1920,1080"
    quality = "-ql" if mode == "preview" else "-qh"
    folder = OUT / f"{mode}_render"
    folder.mkdir(parents=True, exist_ok=True)
    log = OUT / f"{mode}_render.log"
    with log.open("w", encoding="utf-8") as stream:
        subprocess.run(["uv", "run", "manim", quality, "--fps", "30", "--resolution", size,
                        "--disable_caching", "--media_dir", str(folder),
                        str(HERE / "rag_mechanism_scene.py"), "RAGMechanismPoC"],
                       cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    resolution = "540p30" if mode == "preview" else "1080p30"
    return folder / f"videos/rag_mechanism_scene/{resolution}/RAGMechanismPoC.mp4"


def render_threejs() -> None:
    if not (THREE / "node_modules/three").exists() or not (THREE / "node_modules/playwright").exists():
        raise SystemExit("Three.js adapter not installed. Run `cd pilots/v10_threejs_rag && npm ci && npx playwright install chromium --only-shell`.")
    run(["npm", "run", "build:data"], cwd=THREE)
    projection = json.loads((THREE / "data/embedding_space_3d.json").read_text(encoding="utf-8"))
    manifest_path = THREE / "output/threejs_rag_3d_manifest.json"
    inputs = [THREE / "index.html", THREE / "src/main.js", THREE / "src/style.css"]
    digest = hashlib.sha256()
    for path in inputs:
        digest.update(path.relative_to(THREE).as_posix().encode())
        digest.update(path.read_bytes())
    current_scene_hash = digest.hexdigest()
    current_manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    if (THREE_VIDEO.is_file() and
            current_manifest.get("source_trace_sha256") == projection["source_trace_sha256"] and
            current_manifest.get("scene_sha256") == current_scene_hash):
        print("Reusing fresh trace-matched Three.js segment")
    else:
        run(["npm", "run", "render:video"], cwd=THREE)
    if not THREE_VIDEO.is_file():
        raise SystemExit(f"Three.js capture did not produce {THREE_VIDEO}")


def integrate_threejs(base_video: Path, mode: str) -> Path:
    target = OUT / f"{mode}_with_threejs.mp4"
    width, height = (960, 540) if mode == "preview" else (1920, 1080)
    # The Manim beat is [8.5, 17.0). Three.js contributes 8.0 s, then the last
    # actual frame holds for 0.5 s so the existing narration/caption clock stays fixed.
    filter_graph = (
        f"[0:v]trim=start=0:end=8.5,setpts=PTS-STARTPTS,fps=30,scale={width}:{height},setsar=1[v0];"
        f"[1:v]setpts=PTS-STARTPTS,fps=30,scale={width}:{height},"
        "tpad=stop_mode=clone:stop_duration=0.5,trim=duration=8.5,setsar=1[v1];"
        f"[0:v]trim=start=17:end=34,setpts=PTS-STARTPTS,fps=30,scale={width}:{height},setsar=1[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[outv]"
    )
    run(["ffmpeg", "-v", "error", "-y", "-i", str(base_video), "-i", str(THREE_VIDEO),
         "-filter_complex", filter_graph, "-map", "[outv]", "-t", "34", "-r", "30",
         "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)])
    projection = json.loads((THREE / "data/embedding_space_3d.json").read_text(encoding="utf-8"))
    SEGMENT_MAP.write_text(json.dumps({
        "schema": "v10-rag-embedding-segment/v1",
        "trace_id": projection["trace_id"],
        "query_id": projection["query_id"],
        "chunk_ids": [point["id"] for point in projection["points"] if point["kind"] == "chunk"],
        "retrieval": projection["retrieval"],
        "video_timeline": {"start_sec": 8.5, "end_sec": 17.0,
                            "source_start_sec": 0.0, "source_end_sec": 8.0,
                            "hold_last_frame_sec": 0.5, "fps": 30},
        "timestamp_semantics": "presentation timeline; AI trace contains no per-operation execution timestamps",
        "source_trace_sha256": projection["source_trace_sha256"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Three.js segment integrated at [8.5, 17.0)s; trace={projection['trace_id']}; "
          f"query={projection['query_id']}; top3={' -> '.join(projection['retrieval']['top_k_ids'])}")
    return target


def compose_audio(video: Path, mode: str, source: Path, manifest_path: Path,
                  captions_path: Path) -> Path:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cues = json.loads(captions_path.read_text(encoding="utf-8"))
    starts = {}
    elapsed = 0.0
    for beat in manifest["beats"]:
        starts[beat["id"]] = elapsed
        elapsed += beat["sec"]
    windows = [("B04", 9.5), ("B08", 9.5), ("B13", 9.0), ("B15", 7.5)]
    audio_dir = OUT / "audio_adapter"
    audio_dir.mkdir(parents=True, exist_ok=True)
    inputs, filters, selected = [], [], []
    for index, (beat_id, local_start) in enumerate(windows):
        if beat_id not in starts:
            raise SystemExit(f"Audio adapter manifest lacks beat {beat_id}")
        begin = starts[beat_id] + local_start
        part = audio_dir / f"voice_{index}.wav"
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(begin), "-i", str(source),
             "-t", "8.5", "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(part)])
        inputs += ["-i", str(part)]
        filters.append(f"[{index}:a]")
        for cue in cues:
            if cue["end"] > begin and cue["start"] < begin + 8.5:
                selected.append({"start": max(cue["start"], begin) - begin + index*8.5,
                                 "end": min(cue["end"], begin + 8.5) - begin + index*8.5,
                                 "caption": cue["caption"]})
    audio = audio_dir / "narration.wav"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
         "".join(filters) + f"concat=n={len(windows)}:v=0:a=1[a]", "-map", "[a]",
         "-c:a", "pcm_s16le", str(audio)])
    def stamp(seconds):
        ms = round(seconds*1000)
        hh, ms = divmod(ms, 3600000); mm, ms = divmod(ms, 60000); ss, ms = divmod(ms, 1000)
        return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
    srt = audio_dir / "subtitles.ko.srt"
    srt.write_text("\n\n".join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['caption']}"
                                for i, c in enumerate(selected)) + "\n", encoding="utf-8")
    target = OUT / ("rag_mechanism_poc_preview.mp4" if mode == "preview" else "rag_mechanism_poc.mp4")
    subtitle_size = 12 if mode == "preview" else 18
    style = (f"FontName=NanumGothic,FontSize={subtitle_size},PrimaryColour=&H00FFFFFF,"
             "OutlineColour=&H00202020,BorderStyle=1,Outline=1,Shadow=0,MarginV=18")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(audio),
         "-filter_complex", f"[0:v]subtitles='{srt}':force_style='{style}'[v]",
         "-map", "[v]", "-map", "1:a", "-t", "34", "-r", "30", "-c:v", "libx264",
         "-threads", "2", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(target)])
    (OUT / "caption_timing.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2)+"\n",
                                              encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preview", "final"), nargs="?", default="preview")
    parser.add_argument("--silent", action="store_true", help="skip the optional narration/caption adapter")
    parser.add_argument("--with-threejs", action="store_true",
                        help="render and insert the trace-matched 3D embedding beat at 8.5–17.0 sec")
    parser.add_argument("--audio-source", type=Path,
                        help="optional source video containing the previously approved narration")
    parser.add_argument("--audio-manifest", type=Path,
                        help="manifest whose recorded beat timings locate narration windows")
    parser.add_argument("--caption-timing", type=Path,
                        help="optional measured caption cues for the narration source")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    trace_path = HERE / "data/ai_trace.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    errors = load_trace_validator()(trace)
    if errors:
        raise SystemExit("Invalid checked-in AI execution trace: " + "; ".join(errors))
    print(f"Using {trace['schema']} {trace['trace_id']} ({len(trace['intermediate_values'])} values)")

    if args.with_threejs:
        render_threejs()
    manim_video = render_manim(args.mode)
    if not manim_video.is_file():
        raise SystemExit(f"Manim render missing: {manim_video}")
    video = integrate_threejs(manim_video, args.mode) if args.with_threejs else manim_video
    target = OUT / ("rag_mechanism_poc_preview.mp4" if args.mode == "preview" else "rag_mechanism_poc.mp4")

    if args.silent:
        shutil.copyfile(video, target)
        print(f"AUDIO ADAPTER: skipped by --silent; generated video-only {target}")
        return
    legacy = ROOT / "pilots/07_naive_rag"
    source = args.audio_source or legacy / "output/naive_rag_ko.mp4"
    audio_manifest = args.audio_manifest or legacy / "visual_manifest.json"
    caption_timing = args.caption_timing or legacy / "output/caption_timing.json"
    missing = [path for path in (source, audio_manifest, caption_timing) if not path.is_file()]
    if missing:
        print("AUDIO ADAPTER: source narration/caption asset(s) unavailable; rendering video-only. "
              "Use --audio-source, --audio-manifest and --caption-timing to provide them: "
              + ", ".join(str(path) for path in missing))
        shutil.copyfile(video, target)
    else:
        target = compose_audio(video, args.mode, source, audio_manifest, caption_timing)
    print(f"Rendered {target} ({target.stat().st_size} bytes; mode={'video+audio' if not args.silent and not missing else 'video-only'})")


if __name__ == "__main__":
    main()
