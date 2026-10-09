"""Optional real YOLO image inference with trace-backed class-aware NMS evidence."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import numpy as np
from core.mechanism.protocol import MechanismRequest

SCHEMA = "object-detection-execution-trace/v1"
SUPPORTED_YOLO11N_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def intersection_over_union(a: list[float], b: list[float]) -> float:
    left = max(a[0], b[0]); top = max(a[1], b[1])
    right = min(a[2], b[2]); bottom = min(a[3], b[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union > 0 else 0.0


def class_aware_nms(candidates: list[dict[str, Any]], threshold: float,
                    box_key: str = "xyxy") -> tuple[list[str], list[dict[str, Any]]]:
    order = sorted(candidates, key=lambda item: (-item["score"], item["raw_index"]))
    kept: list[str] = []
    steps: list[dict[str, Any]] = []
    while order:
        winner = order[0]
        kept.append(winner["id"])
        survivors = []
        comparisons = []
        for candidate in order[1:]:
            iou = intersection_over_union(winner[box_key], candidate[box_key])
            same_class = winner["class_id"] == candidate["class_id"]
            suppressed = same_class and iou > threshold
            comparisons.append({"candidate_id": candidate["id"], "iou": iou,
                                "same_class": same_class, "suppressed": suppressed})
            if not suppressed:
                survivors.append(candidate)
        steps.append({"winner_id": winner["id"], "comparisons": comparisons})
        order = survivors
    return kept, steps


def _scale_letterboxed_xyxy(boxes: np.ndarray, image_width: int, image_height: int,
                            input_width: int, input_height: int) -> np.ndarray:
    gain = min(input_height / image_height, input_width / image_width)
    resized_w = int(round(image_width * gain))
    resized_h = int(round(image_height * gain))
    pad_x = int(round((input_width - resized_w) / 2 - 0.1))
    pad_y = int(round((input_height - resized_h) / 2 - 0.1))
    boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_x) / gain
    boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_y) / gain
    boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, image_width)
    boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, image_height)
    return boxes


def validate_object_detection_trace(trace: dict[str, Any]) -> list[str]:
    errors = []
    if trace.get("schema") != SCHEMA:
        return [f"schema must be {SCHEMA}"]
    candidates = trace.get("candidates", [])
    ids = [item.get("id") for item in candidates]
    by_id = {item.get("id"): item for item in candidates}
    if len(ids) != len(set(ids)):
        errors.append("candidate IDs must be unique")
    threshold = float(trace.get("thresholds", {}).get("confidence", -1))
    iou_threshold = float(trace.get("thresholds", {}).get("iou", -1))
    display_floor = float(trace.get("thresholds", {}).get("trace_display_floor", -1))
    if not (0 <= display_floor <= threshold <= 1 and 0 <= iou_threshold <= 1):
        errors.append("confidence, display-floor and IoU thresholds are inconsistent")
        return errors
    for item in candidates:
        box = item.get("xyxy")
        if (not isinstance(box, list) or len(box) != 4 or
                not np.isfinite(np.asarray(box, dtype=float)).all() or
                box[2] <= box[0] or box[3] <= box[1]):
            errors.append(f"{item.get('id')}: invalid xyxy box")
        model_box = item.get("model_xyxy")
        if (not isinstance(model_box, list) or len(model_box) != 4 or
                not np.isfinite(np.asarray(model_box, dtype=float)).all() or
                model_box[2] <= model_box[0] or model_box[3] <= model_box[1]):
            errors.append(f"{item.get('id')}: invalid model_xyxy box")
        score = item.get("score")
        if not isinstance(score, (int, float)) or not np.isfinite(score) or not 0 <= score <= 1:
            errors.append(f"{item.get('id')}: invalid confidence")
    confidence_pass = [item["id"] for item in candidates if item["score"] >= threshold]
    if confidence_pass != trace.get("confidence_pass_ids"):
        errors.append("confidence pass IDs do not match candidate scores")
    kept, steps = class_aware_nms([by_id[i] for i in confidence_pass], iou_threshold,
                                  box_key="model_xyxy")
    if kept != trace.get("kept_ids"):
        errors.append("class-aware NMS selection does not match candidate geometry")
    if steps != trace.get("nms_steps"):
        errors.append("class-aware NMS comparisons do not match candidate geometry")
    final_rows = trace.get("model_final_detections", [])
    final_ids = [item.get("id") for item in final_rows]
    if final_ids != kept:
        errors.append("model final detections do not match recomputed class-aware NMS")
    for row in final_rows:
        candidate = by_id.get(row.get("id"))
        if candidate is None:
            continue
        if row.get("class_id") != candidate.get("class_id"):
            errors.append(f"{row.get('id')}: final detection class does not match candidate")
        if (not isinstance(row.get("score"), (int, float)) or
                abs(float(row["score"]) - float(candidate["score"])) >= 1e-4):
            errors.append(f"{row.get('id')}: final detection score does not match candidate")
        box = row.get("xyxy")
        if (not isinstance(box, list) or len(box) != 4 or
                not np.isfinite(np.asarray(box, dtype=float)).all() or
                np.max(np.abs(np.asarray(box, dtype=float) - np.asarray(candidate["xyxy"], dtype=float))) >= .05):
            errors.append(f"{row.get('id')}: final detection box does not match candidate")
    visible = trace.get("visualization_candidate_ids", [])
    if any(item_id not in by_id for item_id in visible):
        errors.append("visualization candidate IDs must exist in candidates")
    return errors


def select_visualization_ids(steps: list[dict[str, Any]], candidates: list[dict[str, Any]],
                             confidence: float, display_limit: int) -> list[str]:
    """Choose a small readable subset while retaining an NMS pair and threshold examples."""
    if display_limit < 1:
        raise ValueError("display_limit must be >=1")
    visible_ids: list[str] = []
    nms_budget = max(1, display_limit - min(3, display_limit - 1))
    for step in steps:
        step_ids = [step["winner_id"]] + [c["candidate_id"] for c in step["comparisons"] if c["suppressed"]]
        for candidate_id in step_ids:
            if candidate_id not in visible_ids and len(visible_ids) < nms_budget:
                visible_ids.append(candidate_id)
        if len(visible_ids) >= nms_budget:
            break
    rejected = sorted((item for item in candidates if item["score"] < confidence),
                      key=lambda item: (-item["score"], item["raw_index"]))
    for item in rejected:
        if len(visible_ids) >= display_limit:
            break
        if item["id"] not in visible_ids:
            visible_ids.append(item["id"])
    for item in sorted((item for item in candidates if item["score"] >= confidence),
                       key=lambda value: (-value["score"], value["raw_index"])):
        if len(visible_ids) >= display_limit:
            break
        if item["id"] not in visible_ids:
            visible_ids.append(item["id"])
    return visible_ids


def run_yolo_inference(image_path: str | Path, model_path: str | Path, output_path: str | Path,
                       confidence_threshold: float = .25, iou_threshold: float = .45,
                       trace_display_floor: float = .05, imgsz: int = 640,
                       display_limit: int = 12) -> dict[str, Any]:
    """Run the official YOLO runtime on a local image and save validated inference evidence."""
    try:
        import torch
        import ultralytics
        from PIL import Image
        from ultralytics import YOLO
        from ultralytics.models.yolo.detect.predict import DetectionPredictor
        from ultralytics.utils import ops
    except ImportError as exc:
        raise RuntimeError("real YOLO inference requires the optional `ultralytics` runtime") from exc
    if ultralytics.__version__ != "8.3.0":
        raise RuntimeError(f"YOLO pre-NMS capture was verified with Ultralytics 8.3.0; found {ultralytics.__version__}")
    image_path = Path(image_path).resolve()
    model_path = Path(model_path).resolve()
    output_path = Path(output_path)
    if not image_path.is_file() or not model_path.is_file():
        raise FileNotFoundError("image and model checkpoint must both exist")
    if sha256(model_path) != SUPPORTED_YOLO11N_SHA256:
        raise ValueError("this adapter currently supports only the verified Ultralytics YOLO11n COCO checkpoint")
    if not (0 <= trace_display_floor <= confidence_threshold <= 1 and 0 <= iou_threshold <= 1):
        raise ValueError("thresholds must satisfy 0 <= trace display floor <= confidence <= 1 and IoU in [0,1]")
    if imgsz < 32 or display_limit < 1:
        raise ValueError("imgsz must be >=32 and display_limit >=1")
    with Image.open(image_path) as im:
        image_width, image_height = im.size

    model = YOLO(str(model_path), task="detect")
    captured: list[np.ndarray] = []
    captured_input_shape: list[tuple[int, int]] = []
    original_nms = ops.non_max_suppression
    original_postprocess = DetectionPredictor.postprocess

    def capture_pre_nms(preds, *args, **kwargs):
        raw = preds[0] if isinstance(preds, (tuple, list)) else preds
        # The runtime's NMS converts xywh to xyxy in-place after this hook.
        captured.append(raw.detach().cpu().numpy().copy())
        return original_nms(preds, *args, **kwargs)

    def capture_preprocess_shape(self, preds, img, orig_imgs):
        captured_input_shape.append((int(img.shape[-1]), int(img.shape[-2])))
        return original_postprocess(self, preds, img, orig_imgs)

    ops.non_max_suppression = capture_pre_nms
    DetectionPredictor.postprocess = capture_preprocess_shape
    try:
        result = model.predict(str(image_path), imgsz=imgsz, conf=confidence_threshold,
                               iou=iou_threshold, device="cpu", rect=False,
                               max_det=300, verbose=False)[0]
    finally:
        ops.non_max_suppression = original_nms
        DetectionPredictor.postprocess = original_postprocess
    if len(captured) != 1 or len(captured_input_shape) != 1:
        raise RuntimeError(f"expected one pre-NMS tensor, received {len(captured)}")

    raw = np.asarray(captured[0][0], dtype=np.float64)
    if raw.ndim != 2 or raw.shape[0] < 5:
        raise RuntimeError(f"unexpected YOLO detect tensor shape: {raw.shape}")
    rows = raw.T
    xywh = rows[:, :4]
    boxes = np.empty_like(xywh)
    boxes[:, 0] = xywh[:, 0] - xywh[:, 2] / 2
    boxes[:, 1] = xywh[:, 1] - xywh[:, 3] / 2
    boxes[:, 2] = xywh[:, 0] + xywh[:, 2] / 2
    boxes[:, 3] = xywh[:, 1] + xywh[:, 3] / 2
    class_scores = rows[:, 4:]
    class_ids = np.argmax(class_scores, axis=1)
    scores = class_scores[np.arange(len(class_scores)), class_ids]
    input_width, input_height = captured_input_shape[0]
    boxes_model = boxes.copy()
    boxes_original = _scale_letterboxed_xyxy(boxes.copy(), image_width, image_height,
                                             input_width, input_height)

    candidates = []
    for raw_index in np.flatnonzero(scores >= trace_display_floor):
        class_id = int(class_ids[raw_index])
        candidates.append({"id": f"det-{int(raw_index):05d}", "raw_index": int(raw_index),
                           "class_id": class_id, "class_name": str(model.names[class_id]),
                           "score": float(scores[raw_index]),
                           "xyxy": [float(v) for v in boxes_original[raw_index]],
                           "model_xyxy": [float(v) for v in boxes_model[raw_index]]})
    confidence_pass = [item for item in candidates if item["score"] >= confidence_threshold]
    kept_ids, steps = class_aware_nms(confidence_pass, iou_threshold, box_key="model_xyxy")
    by_id = {item["id"]: item for item in candidates}

    final_rows = []
    for box in result.boxes:
        final_rows.append({"xyxy": [float(v) for v in box.xyxy[0].cpu().tolist()],
                           "score": float(box.conf[0]), "class_id": int(box.cls[0])})
    if len(final_rows) != len(kept_ids):
        raise RuntimeError(f"custom class-aware NMS returned {len(kept_ids)} boxes; YOLO runtime returned {len(final_rows)}")
    model_final = []
    remaining = list(kept_ids)
    for row in final_rows:
        match = next((candidate_id for candidate_id in remaining
                      if by_id[candidate_id]["class_id"] == row["class_id"] and
                      abs(by_id[candidate_id]["score"] - row["score"]) < 1e-4 and
                      np.max(np.abs(np.asarray(by_id[candidate_id]["xyxy"]) - row["xyxy"])) < .05), None)
        if match is None:
            raise RuntimeError("custom candidate/NMS result does not match the Ultralytics predictor output")
        remaining.remove(match)
        model_final.append({"id": match, **row})
    if remaining:
        raise RuntimeError(f"some expected YOLO final boxes did not match predictor output: {remaining}")

    # Full inference is retained; only the teaching overlay is capped.
    visible_ids = select_visualization_ids(steps, candidates, confidence_threshold, display_limit)
    trace = {
        "schema": SCHEMA,
        "source": "Ultralytics YOLO11n image inference; class-aware NMS trace replay",
        "input_image": {"path": str(image_path), "sha256": sha256(image_path),
                        "width": image_width, "height": image_height},
        "model": {"name": "Ultralytics YOLO11n COCO", "checkpoint": str(model_path),
                  "sha256": sha256(model_path),
                  "source_url": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt",
                  "license": "AGPL-3.0", "runtime": "Ultralytics", "runtime_version": ultralytics.__version__,
                  "torch_version": torch.__version__, "device": "cpu",
                  "class_names": {str(key): str(value) for key, value in model.names.items()}},
        "preprocessing": {"imgsz": imgsz, "rect": False,
                          "input_tensor": [1, 3, input_height, input_width],
                          "resize": "letterbox, aspect-preserving, centered padding"},
        "thresholds": {"confidence": float(confidence_threshold), "iou": float(iou_threshold),
                       "trace_display_floor": float(trace_display_floor)},
        "raw_prediction_count": int(raw.shape[1]),
        "trace_candidate_count": len(candidates),
        "confidence_pass_count": len(confidence_pass),
        "confidence_reject_count_above_display_floor": len(candidates) - len(confidence_pass),
        "candidates": candidates,
        "confidence_pass_ids": [item["id"] for item in confidence_pass],
        "nms_steps": steps,
        "kept_ids": kept_ids,
        "model_final_detections": model_final,
        "visualization_candidate_ids": visible_ids,
        "visualization_note": f"Shows at most {display_limit} trace candidates; inference/NMS ran over the full raw tensor.",
    }
    errors = validate_object_detection_trace(trace)
    if errors:
        raise RuntimeError("generated object-detection trace invalid: " + "; ".join(errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return trace


class ObjectDetectionAdapter:
    """Common CLI adapter; inference runs in a child process to isolate runtime hooks."""

    def __init__(self, capability: dict[str, Any] | None = None):
        self.capability = capability or {}
        self.root = Path(__file__).resolve().parents[3]

    def describe_capability(self):
        return self.capability

    def prepare(self, request: MechanismRequest):
        options = dict(request.options)
        for key in ("image", "model"):
            if not options.get(key):
                raise ValueError(f"object_detection requires --{key}")
            options[key] = str(Path(options[key]).resolve())
            if not Path(options[key]).is_file():
                raise FileNotFoundError(f"object-detection {key} does not exist: {options[key]}")
        return options

    def execute(self, config: dict[str, Any]):
        with tempfile.TemporaryDirectory(prefix="v11_yolo_inference_") as temp:
            trace_path = Path(temp) / "trace.json"
            command = [sys.executable, str(self.root / "scripts/run_yolo_inference.py"),
                       "--image", config["image"], "--model", config["model"], "--out", str(trace_path),
                       "--confidence", str(config.get("confidence_threshold", .25)),
                       "--iou", str(config.get("iou_threshold", .45)),
                       "--display-limit", str(config.get("display_limit", 12))]
            subprocess.run(command, cwd=self.root, check=True)
            return json.loads(trace_path.read_text(encoding="utf-8"))

    def validate(self, trace: dict[str, Any]) -> list[str]:
        errors = validate_object_detection_trace(trace)
        image_info = trace.get("input_image", {})
        image_path = Path(image_info.get("path", ""))
        if not image_path.is_file():
            errors.append(f"replay image is unavailable: {image_path}")
        elif sha256(image_path) != image_info.get("sha256"):
            errors.append("replay image SHA-256 does not match the inference trace")
        if trace.get("source") != "Ultralytics YOLO11n image inference; class-aware NMS trace replay":
            errors.append("trace does not identify the supported real-inference execution path")
        if trace.get("model", {}).get("sha256") != SUPPORTED_YOLO11N_SHA256:
            errors.append("trace model SHA-256 is not the supported YOLO11n checkpoint")
        return errors

    def build_visual_plan(self, trace: dict[str, Any]):
        return {"kind": "object_detection", "title": "실제 YOLO 추론에서 최종 상자를 고르는 과정",
                "input_image": trace["input_image"], "model": trace["model"],
                "raw_prediction_count": trace["raw_prediction_count"],
                "trace_candidate_count": trace["trace_candidate_count"],
                "confidence_pass_count": trace["confidence_pass_count"],
                "kept_ids": trace["kept_ids"], "visualization_candidate_ids": trace["visualization_candidate_ids"],
                "trace_sha256": hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest()}

    def render(self, plan: dict[str, Any], manifest: dict[str, Any], output: Path) -> Path:
        from core.mechanism.renderer import render_yolo_trace
        trace_path = Path(manifest["_trace_path"])
        return render_yolo_trace(trace_path, output, Path(manifest["_path"]),
                                 manifest.get("render_mode", "preview"))
