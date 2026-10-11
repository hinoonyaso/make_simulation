from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.education.education_planner import plan_lesson
from core.education.renderer_registry import (
    RendererResolutionError,
    resolve_asset,
    resolve_lesson_contract,
    resolve_renderer,
    validate_renderer_registration,
)
from core.mechanism.timeline import validate_timeline

ROOT = Path(__file__).resolve().parents[1]


class EducationRendererRegistryTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((ROOT / "examples/education" / name).read_text(encoding="utf-8"))

    def test_bearing_renderer_resolves_through_registered_alias(self):
        from_spec = resolve_renderer("ball_bearing")
        smoke_alias = resolve_renderer("ball_bearing_concept_smoke")
        self.assertEqual(from_spec, smoke_alias)
        self.assertEqual(from_spec.manim_scene_class, "BearingLessonScene")
        self.assertIn("blender", from_spec.supported_modes)

    def test_spur_gear_renderer_and_asset_resolve(self):
        renderer = resolve_renderer("spur_gears")
        asset = resolve_asset(renderer.asset_id)
        self.assertEqual(renderer.manim_scene_class, "SpurGearsLessonScene")
        self.assertEqual(asset["id"], "edu.spur_gears_20_40.v1")
        self.assertEqual(asset["status"], "PASS")
        self.assertEqual(asset["metadata"]["pinion_teeth"], 20)
        self.assertEqual(asset["metadata"]["gear_teeth"], 40)

    def test_unregistered_topic_is_rejected(self):
        with self.assertRaisesRegex(RendererResolutionError, "no education renderer registered"):
            resolve_renderer("unregistered_motor")

    def test_missing_scene_file_is_rejected_before_execution(self):
        renderer = replace(resolve_renderer("spur_gears"), manim_script="pilots/v14_education/missing.py")
        with self.assertRaisesRegex(RendererResolutionError, "Manim scene is missing"):
            validate_renderer_registration(renderer)

    def test_unregistered_manim_scene_class_is_rejected(self):
        renderer = replace(resolve_renderer("spur_gears"), manim_script="scene.py",
                           manim_scene_class="MissingScene")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scene.py").write_text("class OtherScene: pass\n", encoding="utf-8")
            with self.assertRaisesRegex(RendererResolutionError, "MissingScene.*not defined"):
                validate_renderer_registration(renderer, root=root)

    def test_topic_asset_id_mapping_is_enforced(self):
        spec = self.load("spur_gears.json")
        spec["asset_id"] = "edu.bearing_6204.v1"
        with self.assertRaisesRegex(RendererResolutionError, "topic 'spur_gears' maps to"):
            resolve_lesson_contract(spec)

    def test_unknown_blueprint_is_rejected(self):
        spec = self.load("spur_gears.json")
        spec["beats"][0]["blueprint"] = "unknown_blueprint"
        with self.assertRaisesRegex(RendererResolutionError, "unknown educational blueprint"):
            plan_lesson(spec)

    def test_registered_but_unsupported_blueprint_is_blocked(self):
        spec = self.load("spur_gears.json")
        spec["beats"][0]["blueprint"] = "exploded_assembly"
        with self.assertRaisesRegex(RendererResolutionError, "no manim implementation"):
            plan_lesson(spec)

    def test_topic_without_blender_cannot_select_blender(self):
        spec = self.load("spur_gears.json")
        spec["beats"][0]["tool"] = "B"
        with self.assertRaisesRegex(RendererResolutionError, "does not implement blender"):
            plan_lesson(spec)

    def test_plan_only_writes_plan_without_external_renderer_or_tts_calls(self):
        from scripts.produce_lesson import main
        with TemporaryDirectory() as directory:
            with patch.object(sys, "argv", ["produce_lesson.py", "--spec",
                    str(ROOT / "examples/education/spur_gears.json"), "--plan-only",
                    "--output-root", directory, "--run-id", "gear-plan"]), \
                 patch("scripts.produce_lesson.subprocess.run") as run, redirect_stdout(StringIO()):
                self.assertEqual(main(), 0)
            self.assertFalse(run.called)
            report = json.loads((Path(directory) / "gear-plan/production_report.json").read_text())
            resolution = json.loads((Path(directory) / "gear-plan/renderer_resolution.json").read_text())
        self.assertEqual(report["status"], "PLAN_VALIDATED")
        self.assertEqual(resolution["status"], "PASS")
        self.assertEqual(resolution["registry_id"], "spur_gears")
        self.assertEqual(resolution["calculated_results"]["omega_2_over_omega_1"], -.5)

    def test_manim_only_refuses_a_blender_required_lesson_without_fallback(self):
        from scripts.produce_lesson import renderer_runtime_preflight
        spec = self.load("bearing.json")
        contract = plan_lesson(spec)["renderer_contract"]
        with patch("scripts.produce_lesson.subprocess.run") as run:
            with self.assertRaisesRegex(RendererResolutionError, "no renderer fallback"):
                renderer_runtime_preflight(resolve_renderer(spec["topic"]), contract, manim_only=True)
        self.assertFalse(run.called)

    def test_renderer_failure_is_propagated(self):
        from scripts.produce_lesson import render
        spec = self.load("spur_gears.json")
        renderer = resolve_renderer(spec["topic"])
        contract = plan_lesson(spec)["renderer_contract"]
        with TemporaryDirectory() as directory, patch("scripts.produce_lesson.subprocess.run",
                side_effect=__import__("subprocess").CalledProcessError(1, ["manim"])):
            with self.assertRaises(__import__("subprocess").CalledProcessError):
                render(Path(directory) / "manifest.json", Path(directory) / "timeline.json",
                       Path(directory), "preview", renderer=renderer,
                       renderer_contract=contract, runtime_versions={"manim": "test"})

    def test_caption_timing_still_uses_saved_v12_integer_frame_boundaries(self):
        from scripts.produce_lesson import write_captions
        planned = plan_lesson(self.load("spur_gears.json"))
        with TemporaryDirectory() as directory:
            cues = write_captions(planned["visual_manifest"], Path(directory), planned["timeline"])
            saved = json.loads((Path(directory) / "caption_timing.json").read_text(encoding="utf-8"))
        self.assertEqual(cues, saved)
        self.assertEqual(cues[0]["start"], 0)
        self.assertEqual(cues[-1]["end"], planned["timeline"]["total_duration_sec"])

    def test_preview_and_final_resolution_policy_is_unchanged(self):
        from scripts.produce_lesson import delivery_resolution_args
        self.assertEqual(delivery_resolution_args(True), ["--min-width", "960", "--min-height", "540"])
        self.assertEqual(delivery_resolution_args(False), ["--min-width", "1920", "--min-height", "1080"])

    def test_encoded_frame_count_must_match_timeline(self):
        from unittest.mock import patch
        from scripts.produce_lesson import validate_media_frame_range
        video = Path("preview.mp4")
        timeline = {"total_frames": 360}
        probe = json.dumps({"streams": [{"nb_read_frames": "360", "r_frame_rate": "30/1"}]})
        with patch("scripts.produce_lesson.subprocess.check_output", return_value=probe):
            result = validate_media_frame_range(video, timeline)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["observed_frames"], 360)
        self.assertEqual(result["end_exclusive"], 360)

    def test_encoded_frame_count_mismatch_fails(self):
        from unittest.mock import patch
        from scripts.produce_lesson import validate_media_frame_range
        probe = json.dumps({"streams": [{"nb_read_frames": "359", "r_frame_rate": "30/1"}]})
        with patch("scripts.produce_lesson.subprocess.check_output", return_value=probe):
            with self.assertRaisesRegex(RuntimeError, "does not match timeline"):
                validate_media_frame_range(Path("preview.mp4"), {"total_frames": 360})

    def test_gear_timeline_frame_ranges_are_contiguous_and_match_total(self):
        planned = plan_lesson(self.load("spur_gears.json"))
        timeline = planned["timeline"]
        self.assertEqual(validate_timeline(timeline, expected_phase_ids=[
            beat["phase_id"] for beat in planned["visual_manifest"]["beats"]]), [])
        self.assertEqual(timeline["total_frames"], 360)
        self.assertEqual(timeline["phases"][0]["presentation_start_frame"], 0)
        self.assertEqual(timeline["phases"][-1]["presentation_end_frame"], 360)

    def test_plan_output_is_deterministic_for_the_same_spec(self):
        spec = self.load("spur_gears.json")
        first = json.dumps(plan_lesson(spec), ensure_ascii=False, sort_keys=True)
        second = json.dumps(plan_lesson(spec), ensure_ascii=False, sort_keys=True)
        self.assertEqual(first, second)

    def test_planning_does_not_mutate_the_source_lesson_spec(self):
        spec = self.load("spur_gears.json")
        before = copy.deepcopy(spec)
        plan_lesson(spec)
        self.assertEqual(spec, before)


if __name__ == "__main__":
    unittest.main()
