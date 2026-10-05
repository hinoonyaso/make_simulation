"""Mux the continuous Blender render with measured narration and sentence captions."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"
FPS = 30


def run(*args): subprocess.run([str(a) for a in args], check=True)


def main():
    manifest = HERE / "visual_manifest.json"
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    audio = json.loads((HERE / "assets/audio/manifest.json").read_text(encoding="utf-8"))
    edge = 0.0
    for beat in doc["beats"]:
        beat["media"] = "output/moving_obstacle_ko.mp4"
        beat["media_in"] = round(edge, 3)
        edge += float(beat["sec"])
        beat["media_out"] = round(edge, 3)
    manifest.write_text(json.dumps(doc, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    total = float(audio[-1]["end"])
    final = OUT / "moving_obstacle_ko.mp4"
    picture = OUT / "picture.mp4"
    run("ffmpeg", "-v", "error", "-y", "-framerate", FPS, "-start_number", "1",
        "-i", OUT / "frames/frame_%04d.png", "-frames:v", round(total*FPS),
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-r", FPS, "-movflags", "+faststart", picture)
    run("ffmpeg", "-v", "error", "-y", "-i", picture,
        "-i", OUT / "narration.wav", "-i", OUT / "subtitles.ko.srt",
        "-filter_complex", "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "0:v:0", "-map", "[a]", "-map", "2:s:0", "-t", f"{total:.3f}",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text",
        "-metadata:s:s:0", "language=kor", "-movflags", "+faststart", final)
    run(sys.executable, ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py",
        manifest, "--require-media")
    run(sys.executable, ROOT / "core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py",
        manifest, OUT / "sequence.json")
    run(sys.executable, ROOT / "scripts/validate_delivery.py", final, "--require-audio", "--fps", FPS,
        "--audio-manifest", HERE / "assets/audio/manifest.json",
        "--caption-timing", OUT / "caption_timing.json", "--full-decode")
    print(f"FINAL {final} {total:.2f}s 1920x1080@30")


if __name__ == "__main__": main()
