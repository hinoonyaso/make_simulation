"""Actual greedy IoU NMS over supplied/synthetic boxes; no detector inference."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from core.mechanism.protocol import MechanismRequest
from core.mechanism.trace_contract import make_envelope, validate_envelope


DEFAULT_BOXES = [[12, 14, 70, 80], [18, 20, 68, 76], [90, 18, 150, 82], [95, 24, 148, 78], [170, 30, 220, 90]]
DEFAULT_SCORES = [.94, .81, .87, .66, .58]


def intersection_over_union(a: np.ndarray, b: np.ndarray) -> float:
    left, top = np.maximum(a[:2], b[:2])
    right, bottom = np.minimum(a[2:], b[2:])
    intersection = max(0.0, right-left) * max(0.0, bottom-top)
    area_a = max(0.0, a[2]-a[0]) * max(0.0, a[3]-a[1])
    area_b = max(0.0, b[2]-b[0]) * max(0.0, b[3]-b[1])
    union = area_a + area_b - intersection
    return float(intersection / union) if union > 0 else 0.0


class NMSAdapter:
    def __init__(self, capability: dict[str, Any] | None = None): self.capability = capability or {}
    def describe_capability(self): return self.capability
    def prepare(self, request: MechanismRequest): return {"topic": request.topic, **request.options}

    def execute(self, config: dict[str, Any]) -> dict[str, Any]:
        boxes = np.asarray(config.get("boxes", DEFAULT_BOXES), dtype=np.float64)
        scores = np.asarray(config.get("scores", DEFAULT_SCORES), dtype=np.float64)
        ids = list(config.get("ids", [f"box-{i+1:02d}" for i in range(len(scores))]))
        confidence = float(config.get("confidence_threshold", .25))
        iou_threshold = float(config.get("iou_threshold", .5))
        if boxes.ndim != 2 or boxes.shape[1] != 4 or len(boxes) != len(scores) or len(ids) != len(scores):
            raise ValueError("boxes, scores and ids must have matching length; boxes use x1,y1,x2,y2")
        if not np.isfinite(boxes).all() or not np.isfinite(scores).all() or np.any(boxes[:, 2:] <= boxes[:, :2]):
            raise ValueError("boxes/scores must be finite and boxes must have positive area")
        if not 0 <= confidence <= 1 or not 0 <= iou_threshold <= 1 or np.any((scores < 0) | (scores > 1)):
            raise ValueError("scores and thresholds must be in [0,1]")
        passed = [i for i, score in enumerate(scores) if score >= confidence]
        order = sorted(passed, key=lambda i: (-scores[i], i))
        kept, steps = [], []
        while order:
            current, order = order[0], order[1:]
            kept.append(current)
            comparisons, survivors = [], []
            for candidate in order:
                overlap = intersection_over_union(boxes[current], boxes[candidate])
                suppressed = overlap > iou_threshold
                comparisons.append({"winner_id": ids[current], "candidate_id": ids[candidate],
                                    "iou": overlap, "suppressed": suppressed})
                if not suppressed: survivors.append(candidate)
            steps.append({"selected_id": ids[current], "comparisons": comparisons})
            order = survivors
        payload = {"boxes_xyxy": boxes.tolist(), "scores": scores.tolist(), "ids": ids,
                   "confidence_threshold": confidence, "iou_threshold": iou_threshold,
                   "confidence_pass_ids": [ids[i] for i in passed],
                   "kept_ids": [ids[i] for i in kept], "steps": steps,
                   "model_inference_executed": False}
        trace = make_envelope(domain="computer_vision", topic="nms", execution_type="toy_simulation",
            inputs=[{"id": "detection_candidates", "format": "xyxy", "count": len(ids)}],
            operations=[{"id": "confidence_filter", "threshold": confidence},
                        {"id": "greedy_iou_nms", "threshold": iou_threshold}],
            outputs=[{"id": "kept_candidates", "candidate_ids": payload["kept_ids"]}], payload=payload,
            provenance={"backend": "NumPy implementation of greedy IoU NMS", "input_kind": "controlled synthetic candidates"},
            limitations=["No YOLO model, preprocessing, image inference, or dataset evaluation was run."])
        return trace

    def validate(self, trace):
        errors = validate_envelope(trace)
        if trace.get("topic") != "nms" or trace.get("domain") != "computer_vision":
            errors.append("NMS trace domain/topic mismatch")
        try:
            p = trace["payload"]
            boxes, scores, ids = p["boxes_xyxy"], p["scores"], p["ids"]
            if len(boxes) != len(scores) or len(boxes) != len(ids) or len(set(ids)) != len(ids):
                errors.append("NMS candidate identity/array mismatch")
                return errors
            expected = self.execute({"boxes": boxes, "scores": scores, "ids": ids,
                                     "confidence_threshold": p["confidence_threshold"],
                                     "iou_threshold": p["iou_threshold"]})["payload"]
            for key in ("confidence_pass_ids", "kept_ids"):
                if p.get(key) != expected[key]:
                    errors.append(f"NMS {key} do not match the input candidates and thresholds")
            actual_steps = p.get("steps", [])
            expected_steps = expected["steps"]
            if len(actual_steps) != len(expected_steps):
                errors.append("NMS greedy selection step count mismatch")
            else:
                for actual, wanted in zip(actual_steps, expected_steps):
                    if actual.get("selected_id") != wanted["selected_id"] or len(actual.get("comparisons", [])) != len(wanted["comparisons"]):
                        errors.append("NMS selection/comparison order mismatch")
                        break
                    for got, ref in zip(actual["comparisons"], wanted["comparisons"]):
                        if (got.get("winner_id") != ref["winner_id"] or
                                got.get("candidate_id") != ref["candidate_id"] or
                                got.get("suppressed") != ref["suppressed"] or
                                not np.isclose(float(got.get("iou", np.nan)), ref["iou"], atol=1e-12)):
                            errors.append("NMS recorded IoU comparison does not match the boxes")
                            break
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"invalid NMS payload: {exc}")
        return errors

    def build_visual_plan(self, trace):
        p = trace["payload"]
        return {"kind": "nms", "boxes_xyxy": p["boxes_xyxy"], "scores": p["scores"],
                "ids": p["ids"], "confidence_threshold": p["confidence_threshold"],
                "iou_threshold": p["iou_threshold"], "kept_ids": p["kept_ids"], "steps": p["steps"]}

    def render(self, plan, manifest, output: Path):
        from core.mechanism.renderer import render_plan
        return render_plan(plan, Path(manifest["_path"]), output, manifest.get("render_mode", "preview"))
