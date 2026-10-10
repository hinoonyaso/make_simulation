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


def build_caption_timing(manifest: dict, timeline: dict) -> list[dict]:
    """Build the one silent-preview cue timeline from the saved presentation frames."""
    phases = {phase["phase_id"]: phase for phase in timeline["phases"]}
    cues = []
    for beat in manifest["beats"]:
        phase = phases[beat["phase_id"]]
        start = phase["presentation_start_frame"] / timeline["fps"]
        end = phase["presentation_end_frame"] / timeline["fps"]
        sentences = [part.strip() for part in re.split(
            r"(?<=[.!?。！？])\s*", beat.get("caption", "").strip()) if part.strip()]
        weights = [max(1, len(sentence)) for sentence in sentences]
        cursor = start
        for index, (sentence, weight) in enumerate(zip(sentences, weights)):
            cue_end = end if index == len(sentences) - 1 else cursor + (end - start) * weight / sum(weights)
            cues.append({"beat_id": beat["id"], "start": cursor, "end": cue_end,
                         "caption": sentence, "timing_source": "manifest_phase_proportional"})
            cursor = cue_end
    return cues


def write_caption_sidecars(cues: list[dict], output: Path) -> None:
    def stamp(seconds, separator="."):
        ms = round(seconds * 1000)
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d}{separator}{ms:03d}"

    vtt = "WEBVTT\n\n" + "\n\n".join(
        f"{stamp(c['start'])} --> {stamp(c['end'])}\n{c['caption']}" for c in cues) + "\n"
    srt = "\n\n".join(
        f"{i}\n{stamp(c['start'], ',')} --> {stamp(c['end'], ',')}\n{c['caption']}"
        for i, c in enumerate(cues, 1)) + "\n"
    (output / "caption_timing.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "subtitles.ko.vtt").write_text(vtt, encoding="utf-8")
    (output / "subtitles.ko.srt").write_text(srt, encoding="utf-8")


def write_captions(manifest: dict, output: Path, timeline: dict | None = None) -> list[dict]:
    if timeline is None:  # compatibility for direct callers; rendering always supplies the saved timeline.
        phases, frame = [], 0
        for beat in manifest["beats"]:
            start = round(frame)
            frame += round(float(beat["sec"]) * 30)
            phases.append({"phase_id": beat["phase_id"], "presentation_start_frame": start,
                           "presentation_end_frame": frame})
        timeline = {"fps": 30, "phases": phases}
    cues = build_caption_timing(manifest, timeline)
    write_caption_sidecars(cues, output)
    return cues


def burn_captions(video: Path, cues: list[dict], output: Path) -> None:
    """Burn the authoritative cue JSON used to write both subtitle sidecars."""
    probe = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", str(video)], text=True)
    stream = json.loads(probe)["streams"][0]
    width, height = int(stream["width"]), int(stream["height"])
    scale = height / 540
    def ass_stamp(seconds: float) -> str:
        centis = round(seconds * 100)
        hours, centis = divmod(centis, 360000)
        minutes, centis = divmod(centis, 6000)
        seconds, centis = divmod(centis, 100)
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centis:02d}"
    ass_path = output.parent / "subtitles.ko.ass"
    rows = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "WrapStyle: 2",
            "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,NanumGothic,{30 * scale:g},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,{3 * scale:g},{scale:g},2,{40 * scale:g},{40 * scale:g},{24 * scale:g},1",
            "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for cue in cues:
        text = "\\N".join(textwrap.wrap(cue["caption"], width=27, break_long_words=False))
        rows.append(f"Dialogue: 0,{ass_stamp(cue['start'])},{ass_stamp(cue['end'])},Default,,0,0,0,,{text}")
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
        cue_path = run_dir / "caption_timing.json"
        cues = json.loads(cue_path.read_text(encoding="utf-8"))
        burn_captions(final, cues, captioned)
        final.unlink()
        captioned.rename(final)
        (run_dir / "caption_burnin_report.json").write_text(json.dumps({
            "status": "PASS", "source": "caption_timing.json", "duration_sec": timeline["total_frames"]/timeline["fps"],
            "sentences": len(cues), "line_wrap_chars": 27,
            "font": "NanumGothic", "burned_in": True, "sidecar": "subtitles.ko.vtt",
            "timestamp_rounding": "ASS centiseconds; VTT/SRT milliseconds"}, ensure_ascii=False, indent=2)+"\n",
            encoding="utf-8")
    return final, {"blender_render_sec": blender_sec, "manim_render_sec": manim_sec}


def write_qa_reports(run_dir: Path, video: Path, cues: list[dict], *, narrated: bool) -> dict:
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams",
        "-show_format", "-of", "json", str(video)], text=True))
    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video_qa = {"status": "PASS", "path": video.name,
        "codec": video_stream.get("codec_name"), "width": video_stream.get("width"),
        "height": video_stream.get("height"), "fps": video_stream.get("r_frame_rate"),
        "frames": video_stream.get("nb_frames"), "duration_sec": float(probe["format"]["duration"]),
        "full_decode": "PASS (validate_delivery.py)",
        "black_freeze_review": "NOT_AUTOMATED", "full_motion_human_review": "PENDING"}
    audio_status = "PASS" if narrated and audio_streams else "BLOCKED — USER AUTHORIZATION REQUIRED"
    audio_qa = {"status": audio_status, "audio_streams": len(audio_streams),
        "codec": audio_streams[0].get("codec_name") if audio_streams else None,
        "narration_generation": "Edge TTS + Whisper" if narrated else "NOT_RUN",
        "authorization": "approved" if narrated else "not granted",
        "duration_sync": "validated against narration manifest" if narrated else "NOT_APPLICABLE_TO_SILENT_OUTPUT",
        "silence_clipping_last_word": "NOT_REVIEWED"}
    (run_dir / "video_qa.json").write_text(json.dumps(video_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "audio_qa.json").write_text(json.dumps(audio_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    qa = {"video": video_qa, "audio": audio_qa, "subtitles": {
        "status": "PASS" if cues else "FAIL", "cue_count": len(cues),
        "sidecars": ["subtitles.ko.vtt", "subtitles.ko.srt"],
        "burn_in_source": "caption_timing.json", "burn_in_sidecar_parity": "same cue JSON; ASS rounded to centiseconds"},
        "engineering": {"status": "PASS", "evidence_boundary": "conceptual illustration only; no contact/friction solver",
                        "human_accuracy_review": "PENDING"},
        "learner_comprehension": "NOT_TESTED"}
    md = ["# Bearing lesson QA", "", f"- Video: {video.name} — {video_qa['width']}×{video_qa['height']}, "
          f"{video_qa['fps']} fps, {video_qa['duration_sec']:.3f}s, {video_qa['codec']}",
          f"- Video decode: {video_qa['full_decode']}", f"- Audio: {audio_status}",
          f"- Subtitle cues: {len(cues)}; VTT/SRT and burn-in share caption_timing.json.",
          "- Engineering evidence: conceptual illustration; no contact, friction, or deformation solver.",
          "- Full normal-speed motion, narration listening, and learner comprehension: not reviewed.", ""]
    (run_dir / "qa_report.md").write_text("\n".join(md), encoding="utf-8")
    (run_dir / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"video_qa": video_qa, "audio_qa": audio_qa}


def mux_narration(video: Path, narration: Path, output: Path) -> None:
    """Mux full measured narration without a truncating shortest-stream rule."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(narration),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
        "-movflags", "+faststart", str(output)], cwd=ROOT, check=True)


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
        write_captions(planned["visual_manifest"], run_dir, planned["timeline"])
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
                      "--fps", "30", "--full-decode", "--caption-timing", str(run_dir / "caption_timing.json")]
        if args.with_tts:
            validation.extend(["--audio-manifest", str(run_dir / "assets/audio/manifest.json")])
        else:
            validation.extend(["--timeline", str(timeline_path)])
        subprocess.run(validation, cwd=ROOT, check=True)
        report.update(metrics)
        if args.with_tts:
            narration = run_dir / "output/narration.wav"
            if not narration.exists():
                raise FileNotFoundError(f"TTS stage did not produce {narration}")
            narrated = run_dir / "final.mp4"
            mux_narration(video, narration, narrated)
            video = narrated
            report["audio_status"] = "Edge TTS generated; captions aligned by Whisper"
            subprocess.run([sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(video),
                "--min-width", "1920", "--min-height", "1080", "--require-audio", "--fps", "30",
                "--audio-manifest", str(run_dir / "assets/audio/manifest.json"),
                "--caption-timing", str(run_dir / "caption_timing.json"), "--full-decode"],
                cwd=ROOT, check=True)
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
        cues = json.loads((run_dir / "caption_timing.json").read_text(encoding="utf-8"))
        report.update(write_qa_reports(run_dir, video, cues, narrated=args.with_tts))
        if not args.with_tts:
            report["audio_status"] = "BLOCKED — USER AUTHORIZATION REQUIRED"
    (run_dir / "production_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
