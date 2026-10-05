"""Assemble the studio context shot and narration-synced continuous Manim scene."""
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
    durations = [float(b["sec"]) for b in doc["beats"]]
    edges = [0.0]
    for d in durations:
        edges.append(edges[-1] + d)
    manim = "output/manim/videos/manim_shot/1080p30/CostmapInflation.mp4"
    intro = "../02_dwb_reference/output/shots/S1.mp4"
    for beat in doc["beats"]:
        beat["media"] = intro if beat["id"] == "B01" else manim
        beat["media_in"] = 0.0 if beat["id"] == "B01" else round(edges[int(beat["id"][1:]) - 1] - durations[0], 3)
        beat["media_out"] = round(durations[0], 3) if beat["id"] == "B01" else round(edges[int(beat["id"][1:])] - durations[0], 3)
    doc_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    picture = OUT / "picture.mp4"
    manim_start = durations[0]
    manim_end = edges[-1]
    graph = (
        f"[0:v]trim=start=0:duration={durations[0]:.6f},setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v0];"
        f"[1:v]trim=start=0:duration={manim_end-manim_start:.6f},setpts=PTS-STARTPTS,fps=30,scale=1920:1080,setsar=1[v1];"
        "[v0][v1]concat=n=2:v=1:a=0,format=yuv420p[v]"
    )
    run("ffmpeg", "-v", "error", "-y", "-i", ROOT / "pilots/02_dwb_reference/output/shots/S1.mp4",
        "-i", HERE / manim, "-filter_complex", graph, "-map", "[v]", "-an", "-c:v", "libx264",
        "-preset", "slow", "-crf", "16", "-r", FPS, "-pix_fmt", "yuv420p", "-movflags", "+faststart", picture)
    records = json.loads((HERE / "assets/audio/manifest.json").read_text(encoding="utf-8"))
    total = records[-1]["end"]
    final = OUT / "costmap_inflation_ko.mp4"
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
        "--audio-manifest", HERE / "assets/audio/manifest.json",
        "--caption-timing", OUT / "caption_timing.json", "--full-decode")
    print(f"FINAL {final} {total:.2f}s")


if __name__ == "__main__":
    main()
