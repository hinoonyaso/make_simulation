#!/usr/bin/env python3
"""Sample a rendered video for technical metadata and visual anomaly candidates.

Heuristics are deliberately candidates only. They do not prove defect, readability,
motion quality, semantic overlap, comprehension, or full-frame visual continuity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess


def probe_video(path: Path) -> dict:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=width,height,avg_frame_rate,nb_frames,codec_name:format=duration,format_name",
        "-of", "json", str(path)], check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    if not data.get("streams"):
        raise ValueError(f"no video stream found: {path}")
    stream = data["streams"][0]
    return {"width": int(stream["width"]), "height": int(stream["height"]),
            "fps": stream.get("avg_frame_rate"), "frames": stream.get("nb_frames"),
            "codec": stream.get("codec_name"),
            "duration_seconds": float(data.get("format", {}).get("duration", 0)),
            "format": data.get("format", {}).get("format_name")}


def frame_metrics(frames: list[bytes], fps: float, min_repeat_seconds: float = 1.0) -> dict:
    means = [statistics.fmean(frame) for frame in frames]
    dark = []
    repeated = []
    jumps = []
    hashes = [hashlib.sha256(frame).hexdigest() for frame in frames]
    for index, (frame, mean) in enumerate(zip(frames, means)):
        timestamp = index / fps
        dark_fraction = sum(value <= 6 for value in frame) / max(1, len(frame))
        if mean < 5 and dark_fraction >= .99:
            dark.append({"time_seconds": round(timestamp, 3), "mean_luma_0_255": round(mean, 2),
                         "dark_pixel_fraction": round(dark_fraction, 4)})
        if index and abs(mean - means[index - 1]) >= 35:
            jumps.append({"from_seconds": round((index - 1) / fps, 3), "to_seconds": round(timestamp, 3),
                          "mean_luma_delta": round(mean - means[index - 1], 2)})
    run_start = 0
    while run_start < len(hashes):
        run_end = run_start
        while run_end + 1 < len(hashes) and hashes[run_end + 1] == hashes[run_start]:
            run_end += 1
        duration = (run_end - run_start + 1) / fps
        if run_end > run_start and duration >= min_repeat_seconds:
            repeated.append({"from_seconds": round(run_start / fps, 3),
                             "to_seconds": round((run_end + 1) / fps, 3),
                             "duration_seconds": round(duration, 3)})
        run_start = run_end + 1
    return {"sample_count": len(frames), "sample_rate_fps": fps,
            "mean_luma_range": [round(min(means), 2), round(max(means), 2)] if means else [],
            "dark_candidates": dark, "repeated_frame_candidates": repeated,
            "brightness_jump_candidates": jumps,
            "candidate_note": "Review exact video frames; dark canvases, deliberate holds, cuts and flashes may be intentional."}


def sample_video(path: Path, sample_rate: float = 4.0, width: int = 64, height: int = 36,
                 min_repeat_seconds: float = 1.0) -> dict:
    completed = subprocess.run([
        "ffmpeg", "-v", "error", "-i", str(path), "-vf",
        f"fps={sample_rate},scale={width}:{height}:flags=area,format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"], check=True, capture_output=True)
    frame_size = width * height
    frames = [completed.stdout[offset:offset + frame_size]
              for offset in range(0, len(completed.stdout), frame_size)
              if len(completed.stdout[offset:offset + frame_size]) == frame_size]
    return frame_metrics(frames, sample_rate, min_repeat_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--sample-rate", type=float, default=4.0)
    parser.add_argument("--freeze-candidate-min-seconds", type=float, default=1.0)
    args = parser.parse_args()
    if args.sample_rate <= 0 or args.freeze_candidate_min_seconds <= 0:
        parser.error("sample rate and freeze candidate duration must be positive")
    metadata = probe_video(args.video)
    samples = sample_video(args.video, args.sample_rate,
                           min_repeat_seconds=args.freeze_candidate_min_seconds)
    report = {"status": "PASS", "video": str(args.video.resolve()), "metadata": metadata,
              "decode_sample_status": "PASS", "visual_review_status": "INCOMPLETE",
              "sampling": samples,
              "limitations": ["Sampled grayscale metrics can miss short events and spatial detail.",
                              "Human visual review is required to classify each candidate and judge design quality."]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
