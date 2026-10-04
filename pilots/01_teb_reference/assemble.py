"""Encode shots, crossfade S1 -> S2, cut to S3, mix narration + captions, then run the bundle gates.

Timeline contract (all from visual_manifest.json after core/narration/prepare_audio.py tts):
  S1 length = B01.sec;  S2 = XFADE hold + B02..B06;  S3 length = B07.sec
  final = B01 + B02..B06 + B07 = narration length.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parents[1]
OUT = HERE / "output"
SHOTS = OUT / "shots"
FPS = 30
XFADE = 0.6  # must equal manim_shot.XFADE; S1 ends on the exact Manim first frame


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(path)]))


def encode(src_args, dst):
    run("ffmpeg", "-v", "error", "-y", *src_args, "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-r", FPS, dst)
    return dst


def write_media_ranges(manifest_path):
    """Renderer-side duty: record which part of each shot file belongs to each beat."""
    d = json.loads(manifest_path.read_text(encoding="utf-8"))
    t_s2 = XFADE
    for b in d["beats"]:
        sec = float(b["sec"])
        if b["media"].endswith("S2.mp4"):
            b["media_in"], b["media_out"] = round(t_s2, 3), round(t_s2 + sec, 3)
            t_s2 += sec
        else:
            b["media_in"], b["media_out"] = 0.0, round(sec, 3)
    manifest_path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return d


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    s1 = encode(["-framerate", FPS, "-i", OUT / "blender/S1_final/frame_%04d.png"], SHOTS / "S1.mp4")
    s3 = encode(["-framerate", FPS, "-i", OUT / "blender/S3_final/frame_%04d.png"], SHOTS / "S3.mp4")
    s2 = encode(["-i", OUT / "manim/videos/manim_shot/1080p30/BandDissection.mp4"], SHOTS / "S2.mp4")
    picture = SHOTS / "picture.mp4"
    off = duration(s1) - XFADE
    run("ffmpeg", "-v", "error", "-y", "-i", s1, "-i", s2, "-i", s3, "-filter_complex",
        f"[0:v]settb=1/{FPS},fps={FPS}[a];[1:v]settb=1/{FPS},fps={FPS}[b];[2:v]settb=1/{FPS},fps={FPS}[c];"
        f"[a][b]xfade=transition=fade:duration={XFADE}:offset={off:.4f}[ab];[ab][c]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", picture)
    narration = OUT / "narration.wav"
    srt = OUT / "subtitles.ko.srt"
    final = OUT / "pilot_teb_reference.mp4"
    total = json.loads((HERE / "assets/audio/manifest.json").read_text(encoding="utf-8"))[-1]["end"]
    # Hold the last picture frame if frame rounding left the video a few ms short of the narration.
    run("ffmpeg", "-v", "error", "-y", "-i", picture, "-i", narration, "-i", srt,
        "-filter_complex", f"[0:v]tpad=stop_mode=clone:stop_duration=1[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "[v]", "-map", "[a]", "-map", "2:s", "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", "language=kor",
        "-movflags", "+faststart", final)
    manifest = HERE / "visual_manifest.json"
    beats = write_media_ranges(manifest)["beats"]
    py = sys.executable
    run(py, BUNDLE / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py", manifest, "--require-media")
    run(py, BUNDLE / "core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py", manifest, OUT / "sequence.json")
    run(py, BUNDLE / "scripts/validate_delivery.py", final, "--require-audio", "--fps", FPS,
        "--audio-manifest", HERE / "assets/audio/manifest.json", "--caption-timing", OUT / "caption_timing.json",
        "--full-decode")
    starts, t = [], 0.0
    for b in beats:
        starts.append(round(t + 0.5, 2)); t += float(b["sec"])
    run(py, BUNDLE / "core/render-reviewer-skill/scripts/extract_review_frames.py", final,
        "--out", OUT / "review_frames", "--times", *starts)
    print(f"FINAL {final} {duration(final):.2f}s picture {duration(picture):.2f}s narration {total:.2f}s "
          f"(S1+S2+S3 = {duration(s1):.2f}+{duration(s2):.2f}+{duration(s3):.2f}, xfade {XFADE}s)")


if __name__ == "__main__":
    main()
