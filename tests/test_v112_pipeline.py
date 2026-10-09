from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.mechanism.adapters.attention import SelfAttentionAdapter
from core.mechanism.adapters.nms import NMSAdapter
from core.mechanism.protocol import MechanismRequest
from core.mechanism.adapters.quantization import QuantizationAdapter
from core.mechanism.run_management import (canonical_hash, make_run_identity,
                                          prepare_run_dir, validate_replay_trace)
from core.mechanism.storyboard import build_storyboard


class RunManagementTests(unittest.TestCase):
    def setUp(self):
        self.adapter = QuantizationAdapter()
        self.trace = self.adapter.execute(self.adapter.prepare(MechanismRequest("quantization")))

    def _identity(self, *, config=None, trace=None, renderer="manim:preview"):
        return make_run_identity(topic="quantization", config=config or {},
            trace=trace or self.trace, mode="executable", renderer=renderer)

    def test_config_trace_renderer_and_topic_partition_run_identity(self):
        base = self._identity()
        self.assertNotEqual(base["run_id"], self._identity(config={"bits": 4})["run_id"])
        changed = json.loads(json.dumps(self.trace))
        changed["payload"]["bits"] = 4
        self.assertNotEqual(base["run_id"], self._identity(trace=changed)["run_id"])
        self.assertNotEqual(base["run_id"], self._identity(renderer="manim:final")["run_id"])
        other = make_run_identity(topic="nms", config={}, trace=self.trace,
                                  mode="executable", renderer="manim:preview")
        self.assertNotEqual(base["run_id"], other["run_id"])

    def test_same_run_reuses_only_valid_completed_media(self):
        with tempfile.TemporaryDirectory() as temp:
            identity = self._identity()
            run, hit = prepare_run_dir(Path(temp), identity["run_id"], expected_identity=identity)
            self.assertFalse(hit)
            media = run / "preview.mp4"
            media.write_bytes(b"complete-test-media")
            (run / "production_report.json").write_text(json.dumps({
                "identity": identity, "media": str(media), "technical_decode": "PASS"}), encoding="utf-8")
            with patch("core.mechanism.run_management._validate_cached_media", return_value=True):
                reused, hit = prepare_run_dir(Path(temp), identity["run_id"], expected_identity=identity)
            self.assertEqual(reused, run)
            self.assertTrue(hit)

    def test_corrupt_media_is_never_accepted_as_a_completed_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            identity = self._identity()
            run, _ = prepare_run_dir(Path(temp), identity["run_id"], expected_identity=identity)
            media = run / "preview.mp4"
            media.write_bytes(b"truncated")
            (run / "production_report.json").write_text(json.dumps({
                "identity": identity, "media": str(media), "technical_decode": "PASS"}), encoding="utf-8")
            with patch("core.mechanism.run_management._validate_cached_media", return_value=False):
                with self.assertRaises(FileExistsError):
                    prepare_run_dir(Path(temp), identity["run_id"], expected_identity=identity)
            self.assertEqual(media.read_bytes(), b"truncated")

    def test_incomplete_or_conflicting_run_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            identity = self._identity()
            run, _ = prepare_run_dir(Path(temp), identity["run_id"], expected_identity=identity)
            sentinel = run / "trace.json"
            sentinel.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                prepare_run_dir(Path(temp), identity["run_id"], expected_identity=identity)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_explicit_run_id_cannot_reuse_different_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            first, _ = prepare_run_dir(Path(temp), "custom", expected_identity=self._identity())
            media = first / "preview.mp4"
            media.write_bytes(b"media")
            (first / "production_report.json").write_text(json.dumps({
                "identity": self._identity(), "media": str(media), "technical_decode": "PASS"}), encoding="utf-8")
            with patch("core.mechanism.run_management._validate_cached_media", return_value=True):
                with self.assertRaises(FileExistsError):
                    prepare_run_dir(Path(temp), "custom", expected_identity=self._identity(config={"bits": 4}))

    def test_replay_rejects_schema_topic_and_payload_tampering(self):
        errors = validate_replay_trace("quantization", "mechanism-envelope/v1",
                                       self.trace, self.adapter)
        self.assertEqual(errors, [])
        wrong_schema = {**self.trace, "schema": "unknown/v9"}
        self.assertTrue(any("schema mismatch" in error for error in validate_replay_trace(
            "quantization", "mechanism-envelope/v1", wrong_schema, self.adapter)))
        wrong_topic = {**self.trace, "topic": "nms"}
        self.assertTrue(any("topic mismatch" in error for error in validate_replay_trace(
            "quantization", "mechanism-envelope/v1", wrong_topic, self.adapter)))
        tampered = json.loads(json.dumps(self.trace))
        tampered["payload"]["quantized_integer"][0] += 1
        self.assertTrue(validate_replay_trace("quantization", "mechanism-envelope/v1",
                                              tampered, self.adapter))

    def test_trace_hash_is_stable_between_executable_and_replay_inputs(self):
        encoded = json.dumps(self.trace, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"))
        replayed = json.loads(encoded)
        self.assertEqual(canonical_hash(self.trace), canonical_hash(replayed))


class StoryboardTests(unittest.TestCase):
    def test_trace_complexity_changes_storyboard_and_narration_time_is_measured_input(self):
        adapter = QuantizationAdapter()
        trace = adapter.execute(adapter.prepare(MechanismRequest("quantization")))
        plan = adapter.build_visual_plan(trace)
        basic = build_storyboard("quantization", trace, plan, "trace.json", render_mode="preview")
        config = {"scope": "weight_and_activation", "activations": [0.2, 0.6, 1.0]}
        expanded_trace = adapter.execute(adapter.prepare(MechanismRequest("quantization", config)))
        expanded_plan = adapter.build_visual_plan(expanded_trace)
        expanded = build_storyboard("quantization", expanded_trace, expanded_plan, "trace.json",
                                    render_mode="preview", measured_narration_seconds=18.0)
        self.assertEqual(len(basic["beats"]), 3)
        self.assertEqual(len(expanded["beats"]), 4)
        self.assertAlmostEqual(sum(beat["sec"] for beat in expanded["beats"]), 18.0, places=2)
        self.assertEqual(expanded["narration_timing_status"], "measured")

    def test_nms_beat_selection_tracks_trace_operations_and_candidates(self):
        adapter = NMSAdapter()
        trace = adapter.execute(adapter.prepare(MechanismRequest("nms", {
            "boxes": [[0, 0, 10, 10]], "scores": [0.9], "confidence_threshold": 0.5})))
        storyboard = build_storyboard("nms", trace, adapter.build_visual_plan(trace),
                                      "trace.json", render_mode="preview")
        self.assertEqual([beat["object"] for beat in storyboard["beats"]],
                         ["검출 후보", "필터링 상태", "greedy NMS 상태", "결과 상자"])

    def test_attention_plan_covers_matrix_operation_stages(self):
        adapter = SelfAttentionAdapter()
        trace = adapter.execute(adapter.prepare(MechanismRequest("self_attention", {"causal_mask": True})))
        storyboard = build_storyboard("self_attention", trace, adapter.build_visual_plan(trace),
                                      "trace.json", render_mode="preview")
        self.assertEqual(len(storyboard["beats"]), 5)
        self.assertIn("Causal mask", storyboard["beats"][2]["caption"])


if __name__ == "__main__":
    unittest.main()
