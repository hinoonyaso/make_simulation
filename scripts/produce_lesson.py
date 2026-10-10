#!/usr/bin/env python3
"""Create a V9-manifest-driven education lesson using optional solver evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import textwrap
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.education.education_planner import plan_lesson
from core.education.lesson_spec import LessonSpec, validate_lesson_spec


def blender_path_arg(path: Path, executable: str) -> str:
    if executable.casefold().endswith(".exe"):
        return subprocess.run(["wslpath", "-w", str(path.resolve())], capture_output=True,
                              text=True, check=True).stdout.strip()
    return str(path.resolve())


def write_captions(manifest: dict, output: Path) -> None:
    def stamp(seconds):
        ms = round(seconds * 1000)
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    elapsed, cues = 0.0, []
    for beat in manifest["beats"]:
        start, end = elapsed, elapsed + float(beat["sec"])
        sentences = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s*", beat["caption"].strip()) if part.strip()]
        weights = [max(1,len(sentence)) for sentence in sentences]
        total_weight = sum(weights) or 1
        cursor = start
        for index, (sentence, weight) in enumerate(zip(sentences, weights)):
            sentence_end = end if index == len(sentences)-1 else cursor + (end-start)*weight/total_weight
            cues.append(f"{stamp(cursor)} --> {stamp(sentence_end)}\n{sentence}")
            cursor = sentence_end
        elapsed = end
    (output / "subtitles.ko.vtt").write_text("WEBVTT\n\n" + "\n\n".join(cues) + "\n", encoding="utf-8")


def burn_captions(video: Path, manifest: dict, timeline: dict, output: Path) -> None:
    # Burn sentence cues from the same V9 manifest beat text. Sidecar VTT uses
    # the same proportional sentence timing for external players and later audio.
    def ass_stamp(seconds: float) -> str:
        centis = round(seconds * 100)
        hours, centis = divmod(centis, 360000)
        minutes, centis = divmod(centis, 6000)
        seconds, centis = divmod(centis, 100)
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"
    ass_path = output.parent / "subtitles.ko.ass"
    rows = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 960", "PlayResY: 540", "WrapStyle: 2",
            "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,NanumGothic,30,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,40,40,24,1",
            "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for beat, phase in zip(manifest["beats"], timeline["phases"]):
        sentences = [part.strip() for part in re.split(r"(?<=[.!?。！？])\s*", beat["caption"].strip()) if part.strip()]
        start, end = phase["presentation_start_sec"], phase["presentation_end_sec"]
        weights = [max(1, len(sentence)) for sentence in sentences]
        cursor = start
        for index, (sentence, weight) in enumerate(zip(sentences, weights)):
            cue_end = end if index == len(sentences)-1 else cursor + (end-start)*weight/sum(weights)
            text = "\\N".join(textwrap.wrap(sentence, width=27, break_long_words=False))
            cue_start = cursor if index == 0 else cursor + 1/30
            cue_stop = cue_end if index == len(sentences)-1 else cue_end - 1/30
            if cue_stop > cue_start:
                rows.append(f"Dialogue: 0,{ass_stamp(cue_start)},{ass_stamp(cue_stop)},Default,,0,0,0,,{text}")
            cursor = cue_end
    ass_path.write_text("\n".join(rows)+"\n", encoding="utf-8-sig")
    escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                    "-vf", f"ass='{escaped}'",
                    "-an", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(output)], check=True)


def render(manifest_path: Path, timeline_path: Path, run_dir: Path, mode: str, manim_only: bool = False):
    from core.mechanism.renderer import _blender_binary
    width, height, manim_quality = (960, 540, "-ql") if mode == "preview" else (1920, 1080, "-qh")
    blender_sec = 0.0
    blender_output = None
    blender = None
    if not manim_only:
        blender = _blender_binary()
        blender_script = ROOT / "pilots/v13_education/blender/bearing_scene.py"
        blender_output = run_dir / "bearing_blender.mp4"
        blender_args = [blender, "--background", "--factory-startup", "--python-exit-code", "1", "--python",
            blender_path_arg(blender_script, blender), "--", "--manifest", blender_path_arg(manifest_path, blender),
            "--timeline", blender_path_arg(timeline_path, blender), "--output", blender_path_arg(blender_output, blender),
            "--width", str(width), "--height", str(height), "--fps", "30"]
        blender_args.extend(["--samples", "16" if mode == "preview" else "32"])
        started = time.perf_counter()
        subprocess.run(blender_args, cwd=ROOT, check=True)
        blender_sec = time.perf_counter() - started
        if not blender_output.is_file() or blender_output.stat().st_size == 0:
            raise RuntimeError(f"Blender exited without producing its expected video: {blender_output}")

    scene = ROOT / "pilots/v13_education/manim/bearing_scene.py"
    manim_dir = run_dir / "bearing_manim"
    env = os.environ.copy()
    env["V13_MANIFEST_PATH"] = str(manifest_path.resolve())
    env["V13_TIMELINE_PATH"] = str(timeline_path.resolve())
    command = shlex.split(os.environ.get("V11_MANIM_BIN", "uv run manim"))
    started = time.perf_counter()
    subprocess.run([*command, manim_quality, "--fps", "30", "--resolution", f"{width},{height}",
                    "--disable_caching", "--media_dir", str(manim_dir), str(scene), "BearingLessonScene"],
                   cwd=ROOT, env=env, check=True)
    manim_sec = time.perf_counter() - started
    manim_files = list(manim_dir.rglob("BearingLessonScene.mp4"))
    if len(manim_files) != 1:
        raise FileNotFoundError(f"expected exactly one Manim render, found {len(manim_files)}")
    manim_video = manim_files[0]
    final = run_dir / ("preview.mp4" if mode == "preview" else "silent_final.mp4")
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    filters, inputs = [], []
    concat_labels = []
    for index, (beat, phase) in enumerate(zip(manifest["beats"], timeline["phases"])):
        source = 0 if manim_only else (1 if beat.get("tool") == "M" else 0)
        label = f"v{index}"
        filters.append(f"[{source}:v]trim=start_frame={phase['presentation_start_frame']}:"
                       f"end_frame={phase['presentation_end_frame']},setpts=PTS-STARTPTS[{label}]")
        concat_labels.append(f"[{label}]")
    filters.append("".join(concat_labels) + f"concat=n={len(concat_labels)}:v=1:a=0[outv]")
    ffmpeg_inputs = ["ffmpeg", "-v", "error", "-y"]
    if not manim_only:
        ffmpeg_inputs.extend(["-i", str(blender_output)])
    ffmpeg_inputs.extend(["-i", str(manim_video), "-filter_complex", ";".join(filters),
                          "-map", "[outv]", "-an", "-r", "30", "-c:v", "libx264",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)])
    subprocess.run(ffmpeg_inputs, cwd=ROOT, check=True)
    (run_dir / "renderer_provenance.json").write_text(json.dumps({
        "blender": blender, "blender_render_sec": blender_sec,
        "manim_render_sec": manim_sec, "composition": "per-beat renderer selected by V9 manifest tool",
        "fps": 30, "resolution": [width, height], "solver_used": False,
        "manim_only": manim_only,
        "evidence_boundary": "conceptual illustration; no contact force/friction solver"},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if (run_dir / "subtitles.ko.vtt").is_file():
        captioned = run_dir / "preview_captioned.mp4"
        burn_captions(final, manifest, timeline, captioned)
        final.unlink()
        captioned.rename(final)
        (run_dir / "caption_burnin_report.json").write_text(json.dumps({
            "status": "PASS", "source": "V9 manifest captions", "duration_sec": timeline["total_frames"]/timeline["fps"],
            "sentences": sum(len([part for part in re.split(r"(?<=[.!?。！？])\s*", b["caption"].strip()) if part.strip()])
                             for b in manifest["beats"]),
            "line_wrap_chars": 27, "font": "NanumGothic" if not manim_only else None,
            "burned_in": True, "sidecar": "subtitles.ko.vtt"}, ensure_ascii=False, indent=2)+"\n",
            encoding="utf-8")
    return final, {"blender_render_sec": blender_sec, "manim_render_sec": manim_sec}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--preview", action="store_true", help="render 960x540 at 30 fps")
    parser.add_argument("--plan-only", action="store_true", help="validate and write plan artifacts without rendering")
    parser.add_argument("--with-tts", action="store_true", help="send manifest narration to configured Edge TTS voice")
    parser.add_argument("--manim-only", action="store_true", help="render with Manim only (for lightweight CI smoke preview)")
    parser.add_argument("--output-root", type=Path, default=ROOT / "pilots/v13_education/output/lessons")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    raw = json.loads(args.spec.read_text(encoding="utf-8"))
    errors = validate_lesson_spec(raw)
    if errors:
        parser.error("invalid lesson spec: " + "; ".join(errors))
    LessonSpec.from_dict(raw)
    planned = plan_lesson(raw)
    if not args.plan_only and planned["evidence"]["status"] in {"PLANNED", "BLOCKED"}:
        parser.error("lesson evidence route is not renderable: " + str(planned["evidence"].get("reason")))
    run_id = args.run_id or f"{raw['topic']}-{time.strftime('%Y%m%d-%H%M%S')}"
    run_dir = args.output_root.resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "lesson_spec.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    manifest_path = run_dir / "visual_manifest.json"
    timeline_path = run_dir / "timeline.json"
    manifest_path.write_text(json.dumps(planned["visual_manifest"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    timeline_path.write_text(json.dumps(planned["timeline"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (run_dir / "visual_plan.json").write_text(json.dumps(planned["visual_plan"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (run_dir / "evidence_report.json").write_text(json.dumps(planned["evidence"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    if args.with_tts:
        subprocess.run([sys.executable, str(ROOT / "core/narration/prepare_audio.py"), "tts", str(manifest_path)],
                       cwd=ROOT, check=True)
        synced_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        planned = plan_lesson({**raw, "beats": synced_manifest["beats"]})
        planned["visual_manifest"].update({key: value for key, value in synced_manifest.items()
                                           if key not in {"beats", "format", "language"}})
        timeline_path.write_text(json.dumps(planned["timeline"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "core/narration/prepare_audio.py"), "captions", str(manifest_path)],
                       cwd=ROOT, check=True)
        audio_output = run_dir / "output"
        for name in ("subtitles.ko.vtt", "subtitles.ko.srt", "caption_timing.json"):
            source = audio_output / name
            if source.exists():
                (run_dir / name).write_bytes(source.read_bytes())
    else:
        write_captions(planned["visual_manifest"], run_dir)
    report = {"status": "PLANNED" if args.plan_only else "RUNNING", "solver_used": False,
              "evidence_status": planned["evidence"], "manifest": str(manifest_path),
              "timeline": str(timeline_path), "audio_status": "not generated",
              "output_dir": str(run_dir)}
    if args.plan_only:
        report["status"] = "PLAN_VALIDATED"
    else:
        video, metrics = render(manifest_path, timeline_path, run_dir,
                                "preview" if args.preview else "final", manim_only=args.manim_only)
        validation = [sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(video),
                      "--min-width", "540" if args.preview else "1080", "--min-height", "540" if args.preview else "1080",
                      "--fps", "30", "--full-decode"]
        subprocess.run(validation, cwd=ROOT, check=True)
        report.update(metrics)
        if args.with_tts:
            narration = run_dir / "output/narration.wav"
            if not narration.exists():
                raise FileNotFoundError(f"TTS stage did not produce {narration}")
            narrated = run_dir / "final.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(narration),
                            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                            "-shortest", str(narrated)], cwd=ROOT, check=True)
            video = narrated
            report["audio_status"] = "Edge TTS generated; captions aligned by Whisper"
        rendered_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rendered_timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        for beat, phase in zip(rendered_manifest["beats"], rendered_timeline["phases"]):
            beat["media"] = video.name
            beat["media_in"] = phase["presentation_start_sec"]
            beat["media_out"] = phase["presentation_end_sec"]
        manifest_path.write_text(json.dumps(rendered_manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        manifest_check = [sys.executable,
            str(ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py"),
            str(manifest_path), "--require-media"]
        subprocess.run(manifest_check, cwd=ROOT, check=True)
        report.update({"status": "NARRATED_COMPLETE" if args.with_tts else ("SILENT_PREVIEW" if args.preview else "SILENT_RENDER"),
                       "video": str(video), "video_sha256": __import__("hashlib").sha256(video.read_bytes()).hexdigest()})
    (run_dir / "production_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
