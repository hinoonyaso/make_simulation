from __future__ import annotations

import unittest
from unittest.mock import patch

from core.mechanism.timeline import build_timeline, source_time_for_frame, validate_timeline
from core.mechanism.renderer_routing import decide_renderer
from core.mechanism.run_management import make_run_identity


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.beats = [{"phase_id": "a", "sec": 0.51}, {"phase_id": "b", "sec": 1.01}]

    def test_rounding_produces_contiguous_integer_frame_ranges(self):
        value = build_timeline(self.beats, fps=30)
        self.assertEqual([(p["presentation_start_frame"], p["presentation_end_frame"])
                          for p in value["phases"]], [(0, 15), (15, 46)])
        self.assertEqual(value["total_frames"], 46)
        self.assertEqual(validate_timeline(value, expected_phase_ids=["a", "b"]), [])

    def test_rejects_invalid_durations_fps_phase_order_and_source_range(self):
        for duration in (0, -1, float("nan"), float("inf")):
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                build_timeline([{"phase_id": "a", "sec": duration}])
        with self.assertRaises(ValueError):
            build_timeline(self.beats, fps=0)
        with self.assertRaises(ValueError):
            build_timeline(self.beats, source_range=(3, 2))
        value = build_timeline(self.beats)
        value["phases"][1]["presentation_start_frame"] += 1
        self.assertTrue(any("gap, overlap" in error for error in validate_timeline(value)))
        intact = build_timeline(self.beats)
        intact["phases"][0]["visual_goal"] = "motion_3d"
        self.assertTrue(any("timeline_sha256" in error for error in validate_timeline(intact)))

    def test_maps_hold_and_slow_motion_frames_to_trace_time(self):
        value = build_timeline(self.beats, fps=10, source_range=(2, 4), phase_source={
            "a": {"source_start_sec": 2, "source_end_sec": 2, "playback_mode": "hold"},
            "b": {"source_start_sec": 2, "source_end_sec": 4, "playback_mode": "slow_motion"}})
        self.assertEqual(source_time_for_frame(value, 0), ("a", 2.0))
        self.assertEqual(source_time_for_frame(value, 5), ("b", 2.0))
        self.assertEqual(source_time_for_frame(value, 14), ("b", 4.0))


class RendererRoutingTests(unittest.TestCase):
    PASS = {"status": "PASS", "version": "test-runtime"}

    def test_visual_goals_select_evidence_appropriate_renderers(self):
        h1 = {"samples": [{"qpos": [0]}, {"qpos": [1]}]}
        motion = decide_renderer(topic="robot_kinematics", requested_renderer="auto",
            visual_goal="motion_3d", trace=h1, preflight_result=self.PASS)
        inferred_motion = decide_renderer(topic="robot_kinematics", requested_renderer="auto",
            visual_goal="auto", trace=h1, preflight_result=self.PASS)
        numeric = decide_renderer(topic="robot_kinematics", requested_renderer="auto",
            visual_goal="comparative_analysis", trace=h1, preflight_result=self.PASS)
        yolo = decide_renderer(topic="object_detection", requested_renderer="auto",
            visual_goal="auto", trace={}, preflight_result=self.PASS)
        self.assertEqual(motion["selected_renderer"], "blender_h1_trace_playback")
        self.assertEqual(inferred_motion["visual_goal"], "motion_3d")
        self.assertEqual(inferred_motion["selected_renderer"], "blender_h1_trace_playback")
        self.assertEqual(numeric["selected_renderer"], "manim")
        self.assertEqual(yolo["selected_renderer"], "manim_yolo_image_space")

    def test_unavailable_spatial_renderer_falls_back_with_feature_loss(self):
        rag = {"inputs": [{"kind": "query", "embedding": [1, 0]}],
               "intermediate_values": [{"kind": "embedding", "value": [1, 0]}]}
        with patch("core.mechanism.renderer_routing.preflight", return_value=self.PASS):
            decision = decide_renderer(topic="rag", requested_renderer="auto",
                visual_goal="spatial_relationship", trace=rag,
                preflight_result={"status": "BLOCKED", "reason": "browser unavailable"})
        self.assertEqual(decision["selected_renderer"], "manim")
        self.assertTrue(decision["feature_loss"])

    def test_explicit_blender_failure_never_falls_back(self):
        trace = {"samples": [{"qpos": [0]}, {"qpos": [1]}]}
        blocked = {"status": "BLOCKED", "reason": "Blender process failed"}
        decision = decide_renderer(topic="robot_kinematics", requested_renderer="blender",
            visual_goal="motion_3d", trace=trace, preflight_result=blocked)
        self.assertEqual(decision["status"], "BLOCKED")
        self.assertIsNone(decision["selected_renderer"])

    def test_renderer_or_timeline_changes_run_identity(self):
        trace = {"trace_id": "same"}
        a = build_timeline([{"phase_id": "a", "sec": 1}])
        b = build_timeline([{"phase_id": "a", "sec": 2}])
        identity = lambda renderer, timeline: make_run_identity(topic="rag", config={}, trace=trace,
            mode="replay", renderer=renderer, visual_goal="algorithm_flow", timeline=timeline)
        self.assertEqual(identity("manim:preview", a)["timeline_hash"], a["timeline_sha256"])
        self.assertNotEqual(identity("manim:preview", a)["run_id"], identity("blender:preview", a)["run_id"])
        self.assertNotEqual(identity("manim:preview", a)["run_id"], identity("manim:preview", b)["run_id"])


if __name__ == "__main__":
    unittest.main()
