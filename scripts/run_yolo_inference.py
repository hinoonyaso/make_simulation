#!/usr/bin/env python3
"""Optional real YOLO inference CLI; install Ultralytics in the active environment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.mechanism.adapters.object_detection import run_yolo_inference


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--confidence", type=float, default=.25)
    parser.add_argument("--iou", type=float, default=.45)
    parser.add_argument("--display-limit", type=int, default=12)
    args = parser.parse_args()
    trace = run_yolo_inference(args.image, args.model, args.out,
                               confidence_threshold=args.confidence,
                               iou_threshold=args.iou,
                               display_limit=args.display_limit)
    print(json.dumps({"trace": str(args.out),
                      "raw_prediction_count": trace["raw_prediction_count"],
                      "trace_candidates": trace["trace_candidate_count"],
                      "confidence_pass": trace["confidence_pass_count"],
                      "final_detections": len(trace["model_final_detections"]),
                      "visualization_candidates": trace["visualization_candidate_ids"]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
