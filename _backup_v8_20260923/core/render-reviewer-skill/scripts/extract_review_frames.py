#!/usr/bin/env python3
"""Extract compact representative frames with ffmpeg for visual review."""
from __future__ import annotations
import argparse, json, shutil, subprocess
from pathlib import Path


def duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    data = json.loads(subprocess.check_output(cmd, text=True))
    return float(data["format"]["duration"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--out", default="review_frames")
    p.add_argument("--times", nargs="*", type=float, help="seconds; default = 7 evenly spaced samples")
    args = p.parse_args()
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("ffmpeg and ffprobe are required")
    video = Path(args.video).resolve()
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    d = duration(video)
    times = args.times or [d * f for f in (0.03, 0.16, 0.32, 0.50, 0.68, 0.84, 0.97)]
    for i, t in enumerate(times, 1):
        t = max(0.0, min(float(t), max(d - 0.001, 0.0)))
        target = out / f"{i:02d}_{t:07.2f}s.jpg"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-q:v", "2", "-y", str(target)], check=True)
    print(out)

if __name__ == "__main__":
    main()
