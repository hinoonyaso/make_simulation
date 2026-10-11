#!/usr/bin/env python3
"""Create a V9-manifest-driven education lesson using optional solver evidence."""
from __future__ import annotations

import argparse
import hashlib
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
from core.education.renderer_registry import EducationRenderer, RendererResolutionError, resolve_renderer


AUDIO_QA_STATUSES = {"NOT_REQUESTED", "BLOCKED", "PASS", "FAIL"}


def delivery_resolution_args(preview: bool) -> list[str]:
    """Return the minimum delivery dimensions for the selected render mode."""
    width, height = (960, 540) if preview else (1920, 1080)
    return ["--min-width", str(width), "--min-height", str(height)]


def validate_media_frame_range(video: Path, timeline: dict) -> dict:
    """Compare the encoded video frame count with the planned half-open range."""
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
        "-show_entries", "stream=nb_read_frames,r_frame_rate", "-of", "json", str(video),
    ], text=True)
    streams = json.loads(result).get("streams", [])
    if len(streams) != 1:
        raise RuntimeError(f"Expected one video stream in {video}, found {len(streams)}")
    stream = streams[0]
    try:
        observed = int(stream["nb_read_frames"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(f"ffprobe did not report a valid frame count for {video}") from exc
    expected = int(timeline["total_frames"])
    if observed != expected:
        raise RuntimeError(f"Encoded frame count {observed} does not match timeline {expected}")
    return {"status": "PASS", "start_inclusive": 0, "end_exclusive": expected,
            "expected_frames": expected, "observed_frames": observed,
            "frame_rate": stream.get("r_frame_rate")}


def engineering_qa(*, manifest_validated: bool, timeline_validated: bool,
                   evidence_types: list[str]) -> dict:
    evidence = {item.upper() for item in evidence_types}
    if evidence == {"CONCEPTUAL_ILLUSTRATION"}:
        evidence_type = "CONCEPTUAL_ILLUSTRATION"
        computation = "NOT_COMPUTED"
        boundary = "Illustrative geometry and motion only; no contact force, friction, stress, or deformation calculation."
    else:
        evidence_type = sorted(evidence)
        computation = "NOT_ASSERTED"
        boundary = "See per-beat evidence declarations; automated delivery checks do not review engineering claims."
    return {
        "status": "REVIEW_REQUIRED",
        "manifest_contract": {"status": "PASS" if manifest_validated else "NOT_RUN"},
        "video_timeline": {"status": "PASS" if timeline_validated else "NOT_RUN"},
        "evidence": {"type": evidence_type, "calculation_status": computation,
                     "boundary": boundary},
        "human_accuracy_review": {"status": "PENDING"},
    }


def write_audio_failure_reports(run_dir: Path, report: dict, error: Exception,
                                lesson_title: str = "Education lesson") -> None:
    """Persist a requested audio path failure without claiming a media review."""
    report.update({"status": "FAILED", "audio_status": "FAIL",
                   "audio_error": f"{type(error).__name__}: {error}"})
    audio_qa = {"status": "FAIL", "audio_streams": None, "codec": None,
                "narration_generation": "FAILED", "authorization": "NOT_EXPOSED_BY_CLI",
                "duration_sync": "FAILED_OR_NOT_REACHED", "silence_clipping_last_word": "NOT_REVIEWED"}
    qa = {"video": {"status": "NOT_RUN"}, "audio": audio_qa,
          "subtitles": {"status": "NOT_RUN"},
          "engineering": engineering_qa(manifest_validated=False, timeline_validated=False,
                                         evidence_types=[]),
          "learner_comprehension": "NOT_TESTED"}
    (run_dir / "audio_qa.json").write_text(json.dumps(audio_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "qa_report.md").write_text(
        f"# {lesson_title} QA\n\n- Audio: FAIL\n- Audio pipeline error: "
        f"{type(error).__name__}: {error}\n- Video and engineering review: not completed.\n",
        encoding="utf-8")
    (run_dir / "production_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def renderer_runtime_preflight(renderer: EducationRenderer, contract: dict, *, manim_only: bool = False) -> dict:
    """Probe only the backends required by the beats; never downgrade B beats to Manim."""
    from core.mechanism.renderer import _blender_binary
    selected = set(contract["selected_modes"])
    if manim_only and "blender" in selected:
        raise RendererResolutionError(
            "BLOCKED: --manim-only cannot render Blender-required beats as a valid lesson; "
            "no renderer fallback was applied")
    command = shlex.split(os.environ.get("V11_MANIM_BIN", "uv run manim"))
    if not command:
        raise RendererResolutionError("BLOCKED: V11_MANIM_BIN does not name a Manim executable")
    manim_check = subprocess.run([*command, "--version"], cwd=ROOT, capture_output=True,
                                 text=True, check=True)
    def version_line(completed, prefix: str) -> str:
        output = "\n".join(filter(None, (getattr(completed, "stdout", None),
                                             getattr(completed, "stderr", None))))
        candidates = [line.strip() for line in output.splitlines() if line.strip()]
        return next((line for line in candidates if line.startswith(prefix)),
                    candidates[-1] if candidates else "version unavailable")

    result = {"manim": version_line(manim_check, "Manim Community v")}
    if "blender" in selected and not manim_only:
        blender = _blender_binary()
        blender_check = subprocess.run([blender, "--version"], cwd=ROOT, capture_output=True,
                                       text=True, check=True)
        result["blender"] = version_line(blender_check, "Blender ")
    return result


def validate_blender_asset_load_report(report: dict, renderer_contract: dict) -> None:
    """Reject Blender output unless its report proves the registered asset was loaded."""
    expected_asset = renderer_contract["asset_validation"]
    expected_objects = set(expected_asset.get("metadata", {}).get("objects", []))
    observed_objects = set(report.get("blender_loaded_objects", []))
    if (report.get("status") != "PASS"
            or report.get("asset_id") != renderer_contract.get("asset_id")
            or report.get("asset_sha256") != expected_asset.get("sha256")
            or observed_objects != expected_objects
            or report.get("pivot_validation") != "PASS"
            or not report.get("loaded_objects_present")
            or report.get("centers_fixed_during_animation") is not True
            or report.get("fixed_center_validation", {}).get("status") != "PASS"):
        raise RuntimeError("Blender asset load report does not prove the registered asset was loaded and validated")


def render(manifest_path: Path, timeline_path: Path, run_dir: Path, mode: str, manim_only: bool = False,
           *, renderer: EducationRenderer | None = None, renderer_contract: dict | None = None,
           runtime_versions: dict | None = None):
    if renderer is None or renderer_contract is None:
        raise ValueError("generic education render requires an allow-listed renderer and resolved contract")
    from core.mechanism.renderer import _blender_binary
    width, height, manim_quality = (960, 540, "-ql") if mode == "preview" else (1920, 1080, "-qh")
    blender_sec = 0.0
    blender_output = None
    blender = None
    asset_load_report = None
    selected = set(renderer_contract["selected_modes"])
    uses_blender = "blender" in selected and not manim_only
    if uses_blender:
        if not renderer.blender_script:
            raise RendererResolutionError(f"BLOCKED: {renderer.topic} has no registered Blender scene")
        blender = _blender_binary()
        blender_script = ROOT / renderer.blender_script
        blender_output = run_dir / f"{renderer.topic}_blender.mp4"
        blender_args = [blender, "--background", "--factory-startup", "--python-exit-code", "1", "--python",
            blender_path_arg(blender_script, blender), "--", "--manifest", blender_path_arg(manifest_path, blender),
            "--timeline", blender_path_arg(timeline_path, blender)]
        if renderer.blender_context_required:
            blender_args.extend(["--context", blender_path_arg(run_dir / "renderer_context.json", blender)])
        blender_args.extend([
            "--output", blender_path_arg(blender_output, blender),
            "--width", str(width), "--height", str(height), "--fps", "30"])
        blender_args.extend(["--samples", "16" if mode == "preview" else "32"])
        started = time.perf_counter()
        subprocess.run(blender_args, cwd=ROOT, check=True)
        blender_sec = time.perf_counter() - started
        if not blender_output.is_file() or blender_output.stat().st_size == 0:
            raise RuntimeError(f"Blender exited without producing its expected video: {blender_output}")
        asset_report_path = run_dir / "asset_load_report.json"
        if renderer.asset_load_report_required:
            if not asset_report_path.is_file():
                raise RuntimeError(
                    f"Blender renderer {renderer.topic!r} requires asset_load_report.json, but none was produced")
            asset_load_report = json.loads(asset_report_path.read_text(encoding="utf-8"))
            validate_blender_asset_load_report(asset_load_report, renderer_contract)

    scene = ROOT / renderer.manim_script
    manim_dir = run_dir / f"{renderer.topic}_manim"
    env = os.environ.copy()
    env["EDUCATION_MANIFEST_PATH"] = str(manifest_path.resolve())
    env["EDUCATION_TIMELINE_PATH"] = str(timeline_path.resolve())
    env["EDUCATION_RENDER_CONTEXT_PATH"] = str((run_dir / "renderer_context.json").resolve())
    # Keep the V13 environment names for the unchanged bearing scene.
    env["V13_MANIFEST_PATH"] = str(manifest_path.resolve())
    env["V13_TIMELINE_PATH"] = str(timeline_path.resolve())
    command = shlex.split(os.environ.get("V11_MANIM_BIN", "uv run manim"))
    started = time.perf_counter()
    subprocess.run([*command, manim_quality, "--fps", "30", "--resolution", f"{width},{height}",
                    "--disable_caching", "--media_dir", str(manim_dir), str(scene), renderer.manim_scene_class],
                   cwd=ROOT, env=env, check=True)
    manim_sec = time.perf_counter() - started
    manim_files = list(manim_dir.rglob(f"{renderer.manim_scene_class}.mp4"))
    if len(manim_files) != 1:
        raise FileNotFoundError(f"expected exactly one Manim render, found {len(manim_files)}")
    manim_video = manim_files[0]
    final = run_dir / ("preview.mp4" if mode == "preview" else "silent_final.mp4")
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    filters, inputs = [], []
    concat_labels = []
    for index, (beat, phase) in enumerate(zip(manifest["beats"], timeline["phases"])):
        source = (1 if uses_blender else 0) if beat.get("tool") == "M" else 0
        label = f"v{index}"
        filters.append(f"[{source}:v]trim=start_frame={phase['presentation_start_frame']}:"
                       f"end_frame={phase['presentation_end_frame']},setpts=PTS-STARTPTS[{label}]")
        concat_labels.append(f"[{label}]")
    filters.append("".join(concat_labels) + f"concat=n={len(concat_labels)}:v=1:a=0[outv]")
    ffmpeg_inputs = ["ffmpeg", "-v", "error", "-y"]
    if uses_blender:
        ffmpeg_inputs.extend(["-i", str(blender_output)])
    ffmpeg_inputs.extend(["-i", str(manim_video), "-filter_complex", ";".join(filters),
                          "-map", "[outv]", "-an", "-r", "30", "-c:v", "libx264",
                          "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final)])
    subprocess.run(ffmpeg_inputs, cwd=ROOT, check=True)
    provenance = {
        "topic": renderer.topic,
        "renderer_registry_id": renderer.topic,
        "asset_id": renderer_contract["asset_id"],
        "asset_validation": renderer_contract["asset_validation"],
        "calculated_results": renderer_contract.get("calculated_results"),
        "asset_loaded_by_renderer": asset_load_report is not None,
        "asset_load_report": "asset_load_report.json" if asset_load_report is not None else None,
        "fps": 30,
        "resolution": [width, height],
        "renderers": (["manim"] + (["blender"] if uses_blender else [])),
        "renderer_versions": runtime_versions or {},
        "blender_render_sec": blender_sec,
        "manim_render_sec": manim_sec,
        "composition": "per-beat renderer selected by V9 manifest tool and shared V12 integer-frame timeline",
        "solver_used": False,
        "manim_only": manim_only,
        "selected_modes": sorted(selected),
        "media_validation": "PENDING",
        "output": final.name,
        "evidence_types": sorted({beat.get("evidence_type", "conceptual_illustration")
                                   for beat in manifest["beats"]}),
        "evidence_boundary": "Renderer expresses lesson evidence; it does not create solver results.",
    }
    (run_dir / "renderer_provenance.json").write_text(json.dumps(provenance,
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


def write_qa_reports(run_dir: Path, video: Path, cues: list[dict], *, audio_status: str,
                     production_report: dict, manifest_validated: bool = True,
                     timeline_validated: bool = True,
                     evidence_types: list[str] | None = None,
                     lesson_title: str = "Education lesson") -> dict:
    if audio_status not in AUDIO_QA_STATUSES:
        raise ValueError(f"invalid audio QA status: {audio_status}")
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams",
        "-show_format", "-of", "json", str(video)], text=True))
    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if audio_status == "PASS" and not audio_streams:
        raise ValueError("audio QA cannot PASS without an audio stream")
    if audio_status in {"NOT_REQUESTED", "BLOCKED"} and audio_streams:
        raise ValueError(f"audio QA {audio_status} requires a silent output")
    video_qa = {"status": "PASS", "path": video.name,
        "codec": video_stream.get("codec_name"), "width": video_stream.get("width"),
        "height": video_stream.get("height"), "fps": video_stream.get("r_frame_rate"),
        "frames": video_stream.get("nb_frames"), "duration_sec": float(probe["format"]["duration"]),
        "full_decode": "PASS (validate_delivery.py)",
        "black_freeze_review": "NOT_AUTOMATED", "full_motion_human_review": "PENDING"}
    audio_qa = {"status": audio_status, "audio_streams": len(audio_streams),
        "codec": audio_streams[0].get("codec_name") if audio_streams else None,
        "narration_generation": ("Edge TTS + Whisper" if audio_status == "PASS" else
                                 "BLOCKED" if audio_status == "BLOCKED" else "NOT_RUN"),
        "authorization": "NOT_EXPOSED_BY_CLI",
        "duration_sync": ("validated against narration manifest" if audio_status == "PASS" else
                          "BLOCKED" if audio_status == "BLOCKED" else "NOT_APPLICABLE_TO_SILENT_OUTPUT"),
        "silence_clipping_last_word": "NOT_REVIEWED"}
    (run_dir / "video_qa.json").write_text(json.dumps(video_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "audio_qa.json").write_text(json.dumps(audio_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    qa = {"video": video_qa, "audio": audio_qa, "subtitles": {
        "status": "PASS" if cues else "FAIL", "cue_count": len(cues),
        "sidecars": ["subtitles.ko.vtt", "subtitles.ko.srt"],
        "burn_in_source": "caption_timing.json", "burn_in_sidecar_parity": "same cue JSON; ASS rounded to centiseconds"},
        "engineering": engineering_qa(manifest_validated=manifest_validated,
            timeline_validated=timeline_validated,
            evidence_types=evidence_types or ["conceptual_illustration"]),
        "learner_comprehension": "NOT_TESTED"}
    md = [f"# {lesson_title} QA", "", f"- Video: {video.name} — {video_qa['width']}×{video_qa['height']}, "
          f"{video_qa['fps']} fps, {video_qa['duration_sec']:.3f}s, {video_qa['codec']}",
          f"- Video decode: {video_qa['full_decode']}", f"- Audio: {audio_status}",
          f"- Subtitle cues: {len(cues)}; VTT/SRT and burn-in share caption_timing.json.",
          f"- Engineering QA: {qa['engineering']['status']}; manifest contract "
          f"{qa['engineering']['manifest_contract']['status']}; video/timeline "
          f"{qa['engineering']['video_timeline']['status']}.",
          f"- Engineering evidence: {qa['engineering']['evidence']['type']} — "
          f"{qa['engineering']['evidence']['calculation_status']}; "
          f"{qa['engineering']['evidence']['boundary']}",
          f"- Human accuracy review: {qa['engineering']['human_accuracy_review']['status']}.",
          "- Full normal-speed motion, narration listening, and learner comprehension: not reviewed.", ""]
    (run_dir / "qa_report.md").write_text("\n".join(md), encoding="utf-8")
    (run_dir / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    production_report["audio_status"] = audio_status
    (run_dir / "production_report.json").write_text(
        json.dumps(production_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"video_qa": video_qa, "audio_qa": audio_qa, "engineering_qa": qa["engineering"]}


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
    if args.plan_only and args.with_tts:
        parser.error("--plan-only cannot be combined with --with-tts; planning never generates audio")
    raw = json.loads(args.spec.read_text(encoding="utf-8"))
    errors = validate_lesson_spec(raw)
    if errors:
        parser.error("invalid lesson spec: " + "; ".join(errors))
    LessonSpec.from_dict(raw)
    try:
        planned = plan_lesson(raw)
        renderer = resolve_renderer(raw["topic"])
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    if not args.plan_only and planned["evidence"]["status"] in {"PLANNED", "BLOCKED"}:
        parser.error("lesson evidence route is not renderable: " + str(planned["evidence"].get("reason")))
    runtime_versions = {}
    if not args.plan_only:
        try:
            runtime_versions = renderer_runtime_preflight(
                renderer, planned["renderer_contract"], manim_only=args.manim_only)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            parser.error(str(exc))
    run_id = args.run_id or f"{raw['topic']}-{time.strftime('%Y%m%d-%H%M%S')}"
    run_dir = args.output_root.resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "lesson_spec.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    manifest_path = run_dir / "visual_manifest.json"
    timeline_path = run_dir / "timeline.json"
    manifest_path.write_text(json.dumps(planned["visual_manifest"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    timeline_path.write_text(json.dumps(planned["timeline"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (run_dir / "visual_plan.json").write_text(json.dumps(planned["visual_plan"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (run_dir / "renderer_context.json").write_text(
        json.dumps(planned["renderer_contract"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (run_dir / "renderer_resolution.json").write_text(
        json.dumps({"status": "PASS", **planned["renderer_contract"]}, ensure_ascii=False, indent=2)+"\n",
        encoding="utf-8")
    (run_dir / "evidence_report.json").write_text(json.dumps(planned["evidence"], ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    report = {"status": "PLANNED" if args.plan_only else "RUNNING", "solver_used": False,
              "renderer_registry_id": planned["renderer_contract"]["registry_id"],
              "asset_id": planned["renderer_contract"]["asset_id"],
              "asset_validation": planned["renderer_contract"]["asset_validation"]["status"],
              "evidence_status": planned["evidence"], "manifest": str(manifest_path),
              "timeline": str(timeline_path), "audio_status": "NOT_REQUESTED",
              "output_dir": str(run_dir)}
    if args.with_tts:
        try:
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
        except Exception as exc:
            write_audio_failure_reports(run_dir, report, exc, raw.get("title", raw["question"]))
            raise
    else:
        write_captions(planned["visual_manifest"], run_dir, planned["timeline"])
    if args.plan_only:
        report["status"] = "PLAN_VALIDATED"
    else:
        video, metrics = render(manifest_path, timeline_path, run_dir,
                                "preview" if args.preview else "final", manim_only=args.manim_only,
                                renderer=renderer, renderer_contract=planned["renderer_contract"],
                                runtime_versions=runtime_versions)
        validation = [sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(video),
                      *delivery_resolution_args(args.preview),
                      "--fps", "30", "--full-decode", "--caption-timing", str(run_dir / "caption_timing.json")]
        if args.with_tts:
            validation.extend(["--audio-manifest", str(run_dir / "assets/audio/manifest.json")])
        else:
            validation.extend(["--timeline", str(timeline_path)])
        try:
            subprocess.run(validation, cwd=ROOT, check=True)
        except Exception as exc:
            if args.with_tts:
                write_audio_failure_reports(run_dir, report, exc, raw.get("title", raw["question"]))
            raise
        report.update(metrics)
        if args.with_tts:
            try:
                narration = run_dir / "output/narration.wav"
                if not narration.exists():
                    raise FileNotFoundError(f"TTS stage did not produce {narration}")
                narrated = run_dir / "final.mp4"
                mux_narration(video, narration, narrated)
                video = narrated
                final_validation = [sys.executable, str(ROOT / "scripts/validate_delivery.py"), str(video),
                    *delivery_resolution_args(args.preview), "--require-audio", "--fps", "30",
                    "--audio-manifest", str(run_dir / "assets/audio/manifest.json"),
                    "--caption-timing", str(run_dir / "caption_timing.json"), "--full-decode"]
                subprocess.run(final_validation, cwd=ROOT, check=True)
            except Exception as exc:
                write_audio_failure_reports(run_dir, report, exc, raw.get("title", raw["question"]))
                raise
        rendered_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rendered_timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
        frame_range = validate_media_frame_range(video, rendered_timeline)
        for beat, phase in zip(rendered_manifest["beats"], rendered_timeline["phases"]):
            beat["media"] = video.name
            beat["media_in"] = phase["presentation_start_sec"]
            beat["media_out"] = phase["presentation_end_sec"]
        manifest_path.write_text(json.dumps(rendered_manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        manifest_check = [sys.executable,
            str(ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py"),
            str(manifest_path), "--require-media"]
        subprocess.run(manifest_check, cwd=ROOT, check=True)
        provenance_path = run_dir / "renderer_provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        video_sha256 = hashlib.sha256(video.read_bytes()).hexdigest()
        provenance.update({"output": video.name, "media_validation": "PASS", "video_sha256":
                           video_sha256,
                           "timeline_sha256": rendered_timeline.get("timeline_sha256"),
                           "frame_range": frame_range})
        provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        report.update({"status": "NARRATED_COMPLETE" if args.with_tts else ("SILENT_PREVIEW" if args.preview else "SILENT_RENDER"),
                       "video": str(video), "video_sha256": video_sha256,
                       "renderers": provenance["renderers"], "renderer_versions": runtime_versions,
                       "frame_range_validation": frame_range["status"],
                       "observed_video_frames": frame_range["observed_frames"],
                       "renderer_provenance": str(provenance_path)})
        cues = json.loads((run_dir / "caption_timing.json").read_text(encoding="utf-8"))
        evidence_types = planned["evidence"].get("beat_evidence", ["conceptual_illustration"])
        report.update(write_qa_reports(run_dir, video, cues,
            audio_status="PASS" if args.with_tts else "NOT_REQUESTED",
            production_report=report, manifest_validated=True, timeline_validated=True,
            evidence_types=evidence_types, lesson_title=raw.get("title", raw["question"])))
    (run_dir / "production_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
