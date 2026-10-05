"""Assemble the two Blender and one Manim shots, then finish once audio is available."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[1]
OUT = HERE / "output"
FPS = 30
XFADE = 0.6


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)], text=True))


def encode_frames(pattern, target):
    run("ffmpeg", "-v", "error", "-y", "-framerate", FPS, "-i", pattern,
        "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", FPS, target)


def write_media_ranges():
    path = HERE / "visual_manifest.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    t = XFADE
    for beat in doc["beats"]:
        sec = float(beat["sec"])
        if beat["id"] == "B01":
            beat["media"], beat["media_in"], beat["media_out"] = "output/shots/S1.mp4", 0.0, sec
        elif beat["id"] == "B07":
            beat["media"], beat["media_in"], beat["media_out"] = "output/shots/S3.mp4", 0.0, sec
        else:
            beat["media"], beat["media_in"], beat["media_out"] = "output/shots/S2.mp4", round(t, 3), round(t + sec, 3)
            t += sec
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def make_picture(preview=False):
    OUT.joinpath("shots").mkdir(parents=True, exist_ok=True)
    if preview:
        base1 = OUT / "blender/S1_preview/frame_%04d.png"
        base3 = OUT / "blender/S3_preview/frame_%04d.png"
        manim = OUT / "manim/videos/manim_shot/480p15/DWBDissection.mp4"
        manim_filter = "scale=960:540,fps=30"
        crf, preset = "20", "fast"
    else:
        base1 = OUT / "blender/S1_final/frame_%04d.png"
        base3 = OUT / "blender/S3_final/frame_%04d.png"
        manim = OUT / "manim/videos/manim_shot/1080p30/DWBDissection.mp4"
        manim_filter = "fps=30"
        crf, preset = "16", "slow"
    s1 = OUT / "shots/S1.mp4"
    s3 = OUT / "shots/S3.mp4"
    s2 = OUT / "shots/S2.mp4"
    run("ffmpeg", "-v", "error", "-y", "-framerate", FPS, "-i", base1,
        "-c:v", "libx264", "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p", "-r", FPS, s1)
    run("ffmpeg", "-v", "error", "-y", "-framerate", FPS, "-i", base3,
        "-c:v", "libx264", "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p", "-r", FPS, s3)
    run("ffmpeg", "-v", "error", "-y", "-i", manim, "-vf", manim_filter,
        "-an", "-c:v", "libx264", "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p", "-r", FPS, s2)
    xfade_at = duration(s1) - XFADE
    picture = OUT / ("preview_picture.mp4" if preview else "picture.mp4")
    run("ffmpeg", "-v", "error", "-y", "-i", s1, "-i", s2, "-i", s3,
        "-filter_complex",
        f"[0:v]settb=1/{FPS},fps={FPS}[a];[1:v]settb=1/{FPS},fps={FPS}[b];"
        f"[2:v]settb=1/{FPS},fps={FPS}[c];[a][b]xfade=transition=fade:duration={XFADE}:offset={xfade_at:.4f}[ab];"
        "[ab][c]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-c:v", "libx264", "-preset", preset, "-crf", crf,
        "-pix_fmt", "yuv420p", "-r", FPS, picture)
    write_media_ranges()
    return picture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="assemble low-resolution silent review picture")
    parser.add_argument("--picture-only", action="store_true", help="assemble final-resolution picture without muxing audio")
    args = parser.parse_args()
    picture = make_picture(args.preview)
    if args.preview or args.picture_only:
        label = "PREVIEW" if args.preview else "PICTURE ONLY"
        print(f"{label} {picture} {duration(picture):.2f}s")
        return
    audio = OUT / "narration.wav"
    srt = OUT / "subtitles.ko.srt"
    final = OUT / "dwb_reference_ko.mp4"
    if not audio.exists() or not srt.exists():
        raise SystemExit("missing audio or sentence captions; run the narration TTS and captions stages first")
    records = json.loads((HERE / "assets/audio/manifest.json").read_text(encoding="utf-8"))
    total = records[-1]["end"]
    run("ffmpeg", "-v", "error", "-y", "-i", picture, "-i", audio, "-i", srt,
        "-filter_complex", "[0:v]tpad=stop_mode=clone:stop_duration=1[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "[v]", "-map", "[a]", "-map", "2:s", "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", "language=kor",
        "-movflags", "+faststart", final)
    py = sys.executable
    manifest = HERE / "visual_manifest.json"
    run(py, BUNDLE / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py",
        manifest, "--require-media")
    run(py, BUNDLE / "core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py",
        manifest, OUT / "sequence.json")
    run(py, BUNDLE / "scripts/validate_delivery.py", final, "--require-audio", "--fps", FPS,
        "--audio-manifest", HERE / "assets/audio/manifest.json", "--caption-timing", OUT / "caption_timing.json",
        "--full-decode")
    print(f"FINAL {final} {duration(final):.2f}s")


if __name__ == "__main__":
    main()
