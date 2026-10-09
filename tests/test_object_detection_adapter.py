from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
import hashlib

from core.mechanism.adapters.object_detection import (
    SCHEMA,
    class_aware_nms,
    select_visualization_ids,
    validate_object_detection_trace,
)


class ObjectDetectionTraceTests(unittest.TestCase):
    def test_nms_suppresses_same_class_but_keeps_overlapping_other_class(self):
        candidates = [
            {"id": "bus", "raw_index": 0, "class_id": 5, "score": .9,
             "xyxy": [0, 0, 10, 10]},
            {"id": "bus-duplicate", "raw_index": 1, "class_id": 5, "score": .8,
             "xyxy": [1, 1, 11, 11]},
            {"id": "person", "raw_index": 2, "class_id": 0, "score": .7,
             "xyxy": [1, 1, 11, 11]},
        ]
        kept, steps = class_aware_nms(candidates, .45)
        self.assertEqual(kept, ["bus", "person"])
        self.assertTrue(steps[0]["comparisons"][0]["suppressed"])
        self.assertFalse(steps[0]["comparisons"][1]["suppressed"])

    def test_visualization_candidate_selection_obeys_hard_limit(self):
        candidates = [{"id": f"c{i}", "raw_index": i, "score": .9 - i * .02}
                      for i in range(20)]
        steps = [{"winner_id": "c0", "comparisons": [
            {"candidate_id": "c1", "suppressed": True},
            {"candidate_id": "c2", "suppressed": True},
        ]}]
        selected = select_visualization_ids(steps, candidates, .7, 5)
        self.assertLessEqual(len(selected), 5)
        self.assertEqual(selected[:2], ["c0", "c1"])
        self.assertIn("c11", selected)  # one rejected candidate remains visible

    def test_class_aware_nms_keeps_overlapping_different_classes_and_equal_score_order_is_stable(self):
        candidates = [
            {"id": "a", "raw_index": 2, "class_id": 0, "score": .8, "xyxy": [0, 0, 10, 10]},
            {"id": "b", "raw_index": 1, "class_id": 1, "score": .8, "xyxy": [0, 0, 10, 10]},
            {"id": "c", "raw_index": 3, "class_id": 2, "score": .7, "xyxy": [0, 0, 10, 10]},
        ]
        kept, steps = class_aware_nms(candidates, .45)
        self.assertEqual(kept, ["b", "a", "c"])
        self.assertTrue(all(not comparison["suppressed"]
                            for step in steps for comparison in step["comparisons"]))

    def test_identical_boxes_same_class_suppress_and_many_nonoverlapping_boxes_survive(self):
        identical = [
            {"id": "high", "raw_index": 0, "class_id": 4, "score": .9, "xyxy": [1, 1, 8, 8]},
            {"id": "low", "raw_index": 1, "class_id": 4, "score": .8, "xyxy": [1, 1, 8, 8]},
        ]
        kept, steps = class_aware_nms(identical, .5)
        self.assertEqual(kept, ["high"])
        self.assertTrue(steps[0]["comparisons"][0]["suppressed"])
        many = [{"id": f"b{i}", "raw_index": i, "class_id": i, "score": .99-i*.001,
                 "xyxy": [i*20, 0, i*20+10, 10]} for i in range(100)]
        kept, steps = class_aware_nms(many, .45)
        self.assertEqual(len(kept), 100)
        self.assertEqual(sum(len(step["comparisons"]) for step in steps), 4950)

    def test_object_detection_replay_checks_source_image_hash(self):
        from core.mechanism.adapters.object_detection import ObjectDetectionAdapter, SUPPORTED_YOLO11N_SHA256
        with TemporaryDirectory() as temp:
            image = Path(temp) / "image.jpg"
            image.write_bytes(b"test image")
            candidate = {"id": "det-0", "raw_index": 0, "class_id": 0, "class_name": "person",
                         "score": .9, "xyxy": [0, 0, 10, 10], "model_xyxy": [0, 0, 10, 10]}
            trace = {"schema": SCHEMA, "source": "Ultralytics YOLO11n image inference; class-aware NMS trace replay",
                "input_image": {"path": str(image), "sha256": hashlib.sha256(image.read_bytes()).hexdigest()},
                "model": {"sha256": SUPPORTED_YOLO11N_SHA256},
                "thresholds": {"confidence": .25, "iou": .45, "trace_display_floor": .05},
                "candidates": [candidate], "confidence_pass_ids": ["det-0"],
                "nms_steps": [{"winner_id": "det-0", "comparisons": []}], "kept_ids": ["det-0"],
                "model_final_detections": [{"id": "det-0", "class_id": 0, "score": .9,
                                              "xyxy": [0, 0, 10, 10]}],
                "visualization_candidate_ids": ["det-0"]}
            adapter = ObjectDetectionAdapter()
            self.assertEqual(adapter.validate(trace), [])
            image.write_bytes(b"changed image")
            self.assertTrue(any("SHA-256" in error for error in adapter.validate(trace)))

    def test_validator_rejects_malformed_model_space_box(self):
        candidate = {"id": "det-0", "raw_index": 0, "class_id": 0, "class_name": "person",
                     "score": .9, "xyxy": [0, 0, 10, 10], "model_xyxy": [0, 0, 10, 10]}
        trace = {"schema": SCHEMA, "thresholds": {"confidence": .25, "iou": .45,
                  "trace_display_floor": .05}, "candidates": [candidate],
                 "confidence_pass_ids": ["det-0"], "nms_steps": [{"winner_id": "det-0",
                  "comparisons": []}], "kept_ids": ["det-0"],
                 "model_final_detections": [{"id": "det-0", "class_id": 0, "score": .9,
                                              "xyxy": [0, 0, 10, 10]}],
                 "visualization_candidate_ids": ["det-0"]}
        self.assertEqual(validate_object_detection_trace(trace), [])
        trace["model_final_detections"][0]["score"] = .7
        self.assertTrue(any("final detection score" in error
                            for error in validate_object_detection_trace(trace)))
        trace["model_final_detections"][0]["score"] = .9
        trace["candidates"][0]["model_xyxy"] = [0, 0, 0, 1]
        self.assertTrue(any("invalid model_xyxy" in error
                            for error in validate_object_detection_trace(trace)))


if __name__ == "__main__":
    unittest.main()
