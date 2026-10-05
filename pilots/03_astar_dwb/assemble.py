"""Assemble narration-synced 1080p30 shots and run V9 delivery gates."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"
FPS = 30

def run(*args):
    subprocess.run([str(a) for a in args], check=True)

def main():
    doc_path = HERE / "visual_manifest.json"
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    manim = "output/manim/videos/manim_shot/1080p30/AStarDWB.mp4"
    durations = [float(beat["sec"]) for beat in doc["beats"]]
    offsets = [0.0]
    for duration in durations:
        offsets.append(offsets[-1] + duration)
    studio_intro = "../02_dwb_reference/output/shots/S1.mp4"
    studio_drive = "../02_dwb_reference/output/shots/S3.mp4"
    ranges = [(studio_intro, 0.0, durations[0])]
    ranges.extend((manim, offsets[i], offsets[i + 1]) for i in range(1, 5))
    ranges.append((studio_drive, 0.0, durations[5]))
    ranges.append((manim, offsets[6], offsets[7]))
    for beat, (media, start, end) in zip(doc["beats"], ranges):
        beat["media"] = media
        beat["media_in"] = round(start, 3)
        beat["media_out"] = round(end, 3)
    doc_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    picture = OUT / "picture.mp4"
    # Physical studio shots bookend the continuous Manim explanation; the grid and DWB
    # traces remain separate examples, as stated on screen and in the narration.
    fmt = lambda v: f"{v:.6f}"
    graph = (
        f"[0:v]trim=start=0:duration={fmt(durations[0])},setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v0];"
        f"[1:v]trim=start={fmt(offsets[1])}:end={fmt(offsets[5])},setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v1];"
        f"[2:v]trim=start=0:duration={fmt(durations[5])},setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v2];"
        f"[1:v]trim=start={fmt(offsets[6])}:end={fmt(offsets[7])},setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v3];"
        "[v0][v1][v2][v3]concat=n=4:v=1:a=0,format=yuv420p[v]"
    )
    run("ffmpeg", "-v", "error", "-y", "-i", ROOT / "pilots/02_dwb_reference/output/shots/S1.mp4",
        "-i", HERE / manim, "-i", ROOT / "pilots/02_dwb_reference/output/shots/S3.mp4",
        "-filter_complex", graph, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "slow",
        "-crf", "16", "-r", FPS, "-pix_fmt", "yuv420p", "-movflags", "+faststart", picture)
    records = json.loads((HERE / "assets/audio/manifest.json").read_text(encoding="utf-8"))
    total = records[-1]["end"]
    final = OUT / "astar_dwb_ko.mp4"
    run("ffmpeg", "-v", "error", "-y", "-i", picture, "-i", OUT / "narration.wav",
        "-i", OUT / "subtitles.ko.srt", "-filter_complex",
        "[0:v]tpad=stop_mode=clone:stop_duration=1[v];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map", "[v]", "-map", "[a]", "-map", "2:s", "-t", f"{total:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", "language=kor",
        "-movflags", "+faststart", final)
    py = sys.executable
    run(py, ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py",
        doc_path, "--require-media")
    run(py, ROOT / "core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py",
        doc_path, OUT / "sequence.json")
    run(py, ROOT / "scripts/validate_delivery.py", final, "--require-audio", "--fps", FPS,
        "--audio-manifest", HERE / "assets/audio/manifest.json", "--caption-timing", OUT / "caption_timing.json",
        "--full-decode")
    print(f"FINAL {final} {total:.2f}s")

if __name__ == "__main__":
    main()
