from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from core.education.education_planner import plan_lesson
from core.education.sparse_render_plan import build_sparse_render_plan, validate_sparse_render_plan

ROOT = Path(__file__).resolve().parents[1]


class SparseRenderPlanTests(unittest.TestCase):
    def setUp(self):
        spec = json.loads((ROOT / "examples/education/battery_spm_smoke.json").read_text())
        spec["beats"][0]["render_mode"] = "still"
        planned = plan_lesson(spec)
        self.manifest, self.timeline = planned["visual_manifest"], planned["timeline"]

    def test_battery_sparse_plan_uses_exact_0_based_to_blender_frame_mapping(self):
        plan = build_sparse_render_plan(self.manifest, self.timeline,
                                        supported_renderers=("blender", "manim"), supports_stills=True)
        self.assertEqual(validate_sparse_render_plan(plan, self.timeline), [])
        self.assertEqual(plan["total_frames"], 720)
        self.assertEqual(plan["blender_still_count"], 1)
        self.assertEqual(plan["blender_animation_frames"], 180)
        self.assertEqual(
            [(s["beat_id"], s["renderer"], s["timeline_start"], s["timeline_end"], s["output_frames"])
             for s in plan["segments"]],
            [("BAT01", "blender", 0, 180, 180),
             ("BAT02", "manim", 180, 360, 180),
             ("BAT03", "blender", 360, 540, 180),
             ("BAT04", "manim", 540, 720, 180)],
        )
        self.assertEqual(plan["segments"][0]["source_frame"], 1)
        self.assertEqual(plan["segments"][2]["source_frame_start"], 361)
        self.assertEqual(plan["segments"][2]["source_frame_end"], 540)
        self.assertEqual(plan["segments"][2]["output_frames"], 180)

    def test_sparse_is_battery_registry_default_without_changing_other_renderer_defaults(self):
        from core.education.renderer_registry import resolve_renderer

        battery = resolve_renderer("li_ion_battery")
        bearing = resolve_renderer("ball_bearing")
        self.assertEqual(battery.default_render_strategy, "sparse")
        self.assertIn("legacy_full", battery.render_strategies)
        self.assertEqual(bearing.default_render_strategy, "legacy_full")
        self.assertNotIn("sparse", bearing.render_strategies)

    def test_blender_report_must_match_plan_and_total_rendered_images(self):
        from scripts.produce_lesson import validate_sparse_blender_report

        plan = build_sparse_render_plan(self.manifest, self.timeline,
                                        supported_renderers=("blender", "manim"), supports_stills=True)
        report = {"sparse_render": {
            "timeline_sha256": plan["timeline_sha256"], "blender_rendered_images": 181,
            "segments": [
                {"beat_id": "BAT01", "mode": "still", "source_frame": 1,
                 "output_frames": 180, "blender_rendered_images": 1},
                {"beat_id": "BAT03", "mode": "animation", "source_frame_start": 361,
                 "source_frame_end": 540, "output_frames": 180, "blender_rendered_images": 180},
            ],
        }}
        validate_sparse_blender_report(report, plan)
        report["sparse_render"]["blender_rendered_images"] = 720
        with self.assertRaisesRegex(RuntimeError, "expects 181"):
            validate_sparse_blender_report(report, plan)

    def test_gap_overlap_still_capability_and_unsupported_renderer_are_rejected(self):
        plan = build_sparse_render_plan(self.manifest, self.timeline,
                                        supported_renderers=("blender", "manim"), supports_stills=True)
        broken = copy.deepcopy(self.timeline)
        broken["phases"][1]["presentation_start_frame"] += 1
        with self.assertRaisesRegex(ValueError, "gap, overlap"):
            build_sparse_render_plan(self.manifest, broken,
                                     supported_renderers=("blender", "manim"), supports_stills=True)
        with self.assertRaisesRegex(ValueError, "unsupported by its renderer capability"):
            build_sparse_render_plan(self.manifest, self.timeline,
                                     supported_renderers=("blender", "manim"), supports_stills=False)
        bad_manifest = copy.deepcopy(self.manifest)
        bad_manifest["beats"][0]["tool"] = "X"
        with self.assertRaisesRegex(ValueError, "unsupported sparse renderer"):
            build_sparse_render_plan(bad_manifest, self.timeline,
                                     supported_renderers=("blender", "manim"), supports_stills=True)
        corrupted = copy.deepcopy(plan)
        corrupted["segments"][2]["source_frame_end"] -= 1
        self.assertTrue(any("source frame mapping" in error
                            for error in validate_sparse_render_plan(corrupted, self.timeline)))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg fixture tools unavailable")
    def test_sparse_ffmpeg_composition_preserves_each_segment_frame_count(self):
        from scripts.produce_lesson import compose_sparse_video

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            segments = root / "segments"
            segments.mkdir()
            still = segments / "battery_BAT01.png"
            dynamic = segments / "battery_BAT03.mp4"
            manim = root / "manim.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                            "color=c=red:s=64x64:r=30", "-frames:v", "1", str(still)], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                            "color=c=blue:s=64x64:r=30", "-frames:v", "2", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(dynamic)], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                            "color=c=green:s=64x64:r=30", "-frames:v", "6", "-c:v", "libx264",
                            "-pix_fmt", "yuv420p", str(manim)], check=True)
            plan = {"segments": [
                {"beat_id": "BAT01", "renderer": "blender", "mode": "still",
                 "timeline_start": 0, "timeline_end": 2, "output_frames": 2},
                {"beat_id": "BAT02", "renderer": "manim", "mode": "video",
                 "timeline_start": 2, "timeline_end": 4, "output_frames": 2},
                {"beat_id": "BAT03", "renderer": "blender", "mode": "animation",
                 "timeline_start": 4, "timeline_end": 6, "output_frames": 2},
            ]}
            timeline = {"fps": 30, "total_frames": 6}
            result = compose_sparse_video(plan, timeline, segments, manim, root / "final.mp4")
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["frames"], 6)


if __name__ == "__main__":
    unittest.main()
