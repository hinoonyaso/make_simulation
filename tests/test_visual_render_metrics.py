from __future__ import annotations

import unittest

from scripts.analyze_visual_render import frame_metrics


class VisualRenderMetricTests(unittest.TestCase):
    def test_dark_repeated_and_brightness_candidates_are_reported(self):
        dark = bytes([0] * 16)
        light = bytes([220] * 16)
        result = frame_metrics([dark, dark, light], fps=2)
        self.assertEqual(result["dark_candidates"][0]["time_seconds"], 0)
        self.assertEqual(result["repeated_frame_candidates"], [
            {"from_seconds": 0.0, "to_seconds": 1.0, "duration_seconds": 1.0}
        ])
        self.assertEqual(result["brightness_jump_candidates"][0]["mean_luma_delta"], 220)
        self.assertIn("may be intentional", result["candidate_note"])

    def test_long_identical_run_is_one_freeze_candidate(self):
        frame = bytes([100] * 16)
        result = frame_metrics([frame, frame, frame, frame, bytes([110] * 16)], fps=2)
        self.assertEqual(result["repeated_frame_candidates"], [
            {"from_seconds": 0.0, "to_seconds": 2.0, "duration_seconds": 2.0}
        ])

    def test_no_candidates_for_distinct_normal_luma_samples(self):
        frames = [bytes([value, value + 1, value + 2, value + 3]) for value in (80, 84, 88)]
        result = frame_metrics(frames, fps=4)
        self.assertEqual(result["dark_candidates"], [])
        self.assertEqual(result["repeated_frame_candidates"], [])
        self.assertEqual(result["brightness_jump_candidates"], [])


if __name__ == "__main__":
    unittest.main()
