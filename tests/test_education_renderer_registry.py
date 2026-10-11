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
        self.assertFalse(from_spec.blender_context_required)
        self.assertFalse(from_spec.asset_load_report_required)

    def test_spur_gear_renderer_and_asset_resolve(self):
        renderer = resolve_renderer("spur_gears")
        asset = resolve_asset(renderer.asset_id)
        self.assertEqual(renderer.manim_scene_class, "SpurGearsLessonScene")
        self.assertEqual(asset["id"], "edu.spur_gears_20_40.v1")
        self.assertEqual(asset["status"], "PASS")
        self.assertEqual(asset["metadata"]["pinion_teeth"], 20)
        self.assertEqual(asset["metadata"]["gear_teeth"], 40)
        self.assertTrue(renderer.blender_context_required)
        self.assertTrue(renderer.asset_load_report_required)

    def _render_with_fake_runtimes(self, spec_name: str, asset_report: dict | None):
        from scripts.produce_lesson import render
        planned = plan_lesson(self.load(spec_name))
        renderer = resolve_renderer(planned["renderer_contract"]["registry_id"])
        calls = []
        context_asset_ids = []
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            manifest_path, timeline_path = run_dir / "visual_manifest.json", run_dir / "timeline.json"
            (run_dir / "renderer_context.json").write_text(
                json.dumps(planned["renderer_contract"]), encoding="utf-8")
            manifest_path.write_text(json.dumps(planned["visual_manifest"]), encoding="utf-8")
            timeline_path.write_text(json.dumps(planned["timeline"]), encoding="utf-8")

            def fake_run(args, **kwargs):
                calls.append(args)
                if args[0] == "ffmpeg":
                    Path(args[-1]).touch()
                elif "--output" in args:
                    if "--context" in args:
                        context_path = Path(args[args.index("--context") + 1])
                        context_asset_ids.append(json.loads(context_path.read_text(encoding="utf-8")).get("asset_id"))
                    output = Path(args[args.index("--output") + 1])
                    output.write_bytes(b"video")
                    if asset_report is not None:
                        (run_dir / "asset_load_report.json").write_text(
                            json.dumps(asset_report), encoding="utf-8")
                elif "--media_dir" in args:
                    media_dir = Path(args[args.index("--media_dir") + 1])
                    scene_class = args[-1]
                    manim_video = media_dir / "videos" / "scene" / "540p30" / f"{scene_class}.mp4"
                    manim_video.parent.mkdir(parents=True)
                    manim_video.touch()
                return __import__("subprocess").CompletedProcess(args, 0)

            with patch("core.mechanism.renderer._blender_binary", return_value="blender-test"), \
                 patch("scripts.produce_lesson.subprocess.run", side_effect=fake_run):
                result = render(manifest_path, timeline_path, run_dir, "preview",
                                renderer=renderer, renderer_contract=planned["renderer_contract"],
                                runtime_versions={"manim": "test", "blender": "test"})
            provenance = json.loads((run_dir / "renderer_provenance.json").read_text(encoding="utf-8"))
            saved_report = run_dir / "asset_load_report.json"
            return result, calls, provenance, saved_report.exists(), planned["renderer_contract"], context_asset_ids

    def test_bearing_blender_keeps_legacy_cli_and_report_is_optional(self):
        _, calls, provenance, has_report, _, _ = self._render_with_fake_runtimes("bearing.json", None)
        blender_args = calls[0]
        self.assertIn("--manifest", blender_args)
        self.assertIn("--timeline", blender_args)
        self.assertNotIn("--context", blender_args)
        self.assertFalse(has_report)
        self.assertFalse(provenance["asset_loaded_by_renderer"])
        self.assertIsNone(provenance["asset_load_report"])

    def test_gear_blender_receives_context_and_validates_registered_asset_report(self):
        contract = plan_lesson(self.load("spur_gears_full.json"))["renderer_contract"]
        metadata = contract["asset_validation"]["metadata"]
        report = {"status": "PASS", "asset_id": contract["asset_id"],
                  "asset_sha256": contract["asset_validation"]["sha256"],
                  "blender_loaded_objects": metadata["objects"],
                  "loaded_objects_present": True, "pivot_validation": "PASS",
                  "centers_fixed_during_animation": True,
                  "fixed_center_validation": {"status": "PASS"}}
        _, calls, provenance, has_report, _, context_asset_ids = self._render_with_fake_runtimes(
            "spur_gears_full.json", report)
        blender_args = calls[0]
        self.assertIn("--context", blender_args)
        self.assertEqual(context_asset_ids, ["edu.spur_gears_20_40.v1"])
        self.assertTrue(has_report)
        self.assertTrue(provenance["asset_loaded_by_renderer"])

    def test_gear_blender_missing_asset_report_fails_before_success_provenance(self):
        from scripts.produce_lesson import render
        planned = plan_lesson(self.load("spur_gears_full.json"))
        renderer = resolve_renderer("spur_gears")
        with TemporaryDirectory() as directory:
            run_dir = Path(directory)
            manifest_path, timeline_path = run_dir / "manifest.json", run_dir / "timeline.json"
            (run_dir / "renderer_context.json").write_text("{}", encoding="utf-8")
            manifest_path.write_text(json.dumps(planned["visual_manifest"]), encoding="utf-8")
            timeline_path.write_text(json.dumps(planned["timeline"]), encoding="utf-8")
            def fake_blender(args, **kwargs):
                Path(args[args.index("--output") + 1]).write_bytes(b"video")
                return __import__("subprocess").CompletedProcess(args, 0)
            with patch("core.mechanism.renderer._blender_binary", return_value="blender-test"), \
                 patch("scripts.produce_lesson.subprocess.run", side_effect=fake_blender):
                with self.assertRaisesRegex(RuntimeError, "requires asset_load_report.json"):
                    render(manifest_path, timeline_path, run_dir, "preview", renderer=renderer,
                           renderer_contract=planned["renderer_contract"])
            self.assertFalse((run_dir / "renderer_provenance.json").exists())

    def test_gear_asset_report_rejects_hash_object_and_pivot_failures(self):
        from scripts.produce_lesson import validate_blender_asset_load_report
        contract = plan_lesson(self.load("spur_gears_full.json"))["renderer_contract"]
        metadata = contract["asset_validation"]["metadata"]
        base = {"status": "PASS", "asset_id": contract["asset_id"],
                "asset_sha256": contract["asset_validation"]["sha256"],
                "blender_loaded_objects": metadata["objects"],
                "loaded_objects_present": True, "pivot_validation": "PASS",
                "centers_fixed_during_animation": True,
                "fixed_center_validation": {"status": "PASS"}}
        invalid_reports = []
        for key, value in (("asset_sha256", "0" * 64),
                           ("blender_loaded_objects", metadata["objects"][:-1]),
                           ("pivot_validation", "FAIL"),
                           ("fixed_center_validation", {"status": "FAIL"})):
            invalid = copy.deepcopy(base)
            invalid[key] = value
            invalid_reports.append(invalid)
        for report in invalid_reports:
            with self.subTest(report=report):
                with self.assertRaisesRegex(RuntimeError, "does not prove"):
                    validate_blender_asset_load_report(report, contract)

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

    def test_spur_gear_topic_selects_registered_blender_renderer(self):
        spec = self.load("spur_gears.json")
        spec["beats"][0]["tool"] = "B"
        plan = plan_lesson(spec)
        self.assertIn("blender", plan["renderer_contract"]["selected_modes"])
        self.assertEqual(plan["renderer_contract"]["scene"]["blender_script"],
                         "pilots/v14_education/blender/spur_gears_scene.py")

    def test_full_gear_lesson_is_80_seconds_and_mixed_renderer(self):
        spec = self.load("spur_gears_full.json")
        plan = plan_lesson(spec)
        self.assertEqual(plan["timeline"]["fps"], 30)
        self.assertEqual(plan["timeline"]["total_frames"], 2400)
        self.assertEqual(plan["timeline"]["total_duration_sec"], 80)
        self.assertEqual(plan["renderer_contract"]["selected_modes"], ["blender", "manim"])
        self.assertEqual(plan["renderer_contract"]["calculated_results"]["omega_2_over_omega_1"], -.5)
        self.assertEqual(plan["renderer_contract"]["calculated_results"]["pinion_center_m"], (-.03, 0, 0))
        self.assertEqual(plan["renderer_contract"]["calculated_results"]["gear_center_m"], (.03, 0, 0))
        self.assertEqual(plan["evidence"]["status"], "CONCEPT_ONLY")

    def test_ratio_calculation_smoke_is_a_five_second_manim_only_lesson(self):
        spec = self.load("gear_ratio_smoke.json")
        planned = plan_lesson(spec)
        self.assertEqual(planned["timeline"]["total_frames"], 150)
        self.assertEqual(planned["renderer_contract"]["selected_modes"], ["manim"])
        self.assertEqual(planned["renderer_contract"]["asset_id"], "edu.spur_gears_20_40.v1")
        self.assertEqual(planned["renderer_contract"]["calculated_results"]["omega_2_over_omega_1"], -.5)
        scene = (ROOT / "pilots/v14_education/manim/spur_gears_scene.py").read_text(encoding="utf-8")
        self.assertNotIn("MathTex(", scene)

    def test_blender_gear_keys_share_ideal_ratio_and_continuous_phase_boundaries(self):
        from core.education.gear_animation import plan_gear_rotation_keys
        planned = plan_lesson(self.load("spur_gears_full.json"))
        keys = plan_gear_rotation_keys(planned["visual_manifest"], planned["timeline"], -.5)
        pinion = keys["Pinion_20T"]
        gear = keys["Gear_40T"]
        first_input = next(row for row in pinion if row["frame"] == 661)
        first_output = next(row for row in gear if row["frame"] == 661)
        last_input = next(row for row in pinion if row["frame"] == 1021)
        last_output = next(row for row in gear if row["frame"] == 1021)
        self.assertEqual(first_input["angle_rad"], 0)
        self.assertEqual(first_output["angle_rad"], 0)
        self.assertAlmostEqual(last_input["angle_rad"], 2 * __import__("math").pi)
        self.assertAlmostEqual(last_output["angle_rad"], -__import__("math").pi)
        for name in ("Pinion_Hub", "Gear_Hub"):
            self.assertEqual(keys[name], keys["Pinion_20T"] if name == "Pinion_Hub" else keys["Gear_40T"])

    def test_gear_key_planner_rejects_nonfinite_turns_and_mismatched_phases(self):
        from core.education.gear_animation import plan_gear_rotation_keys
        planned = plan_lesson(self.load("spur_gears_full.json"))
        manifest, timeline = planned["visual_manifest"], planned["timeline"]
        manifest["beats"][2]["input_turns"] = float("nan")
        with self.assertRaisesRegex(ValueError, "input_turns must be finite"):
            plan_gear_rotation_keys(manifest, timeline, -.5)
        manifest, timeline = planned["visual_manifest"], planned["timeline"]
        timeline["phases"].pop()
        with self.assertRaisesRegex(ValueError, "must match"):
            plan_gear_rotation_keys(manifest, timeline, -.5)

    def test_gear_rotation_key_planner_scales_two_turns_and_reverse_input(self):
        import math
        from core.education.gear_animation import plan_gear_rotation_keys
        planned = plan_lesson(self.load("spur_gears_full.json"))
        manifest = copy.deepcopy(planned["visual_manifest"])
        manifest["beats"][2]["input_turns"] = 2.0
        forward = plan_gear_rotation_keys(manifest, planned["timeline"], -.5)
        self.assertAlmostEqual(next(row["angle_rad"] for row in forward["Pinion_20T"]
                                   if row["frame"] == 1021), 4 * math.pi)
        self.assertAlmostEqual(next(row["angle_rad"] for row in forward["Gear_40T"]
                                   if row["frame"] == 1021), -2 * math.pi)
        manifest["beats"][2]["input_turns"] = -1.0
        reverse = plan_gear_rotation_keys(manifest, planned["timeline"], -.5)
        self.assertAlmostEqual(next(row["angle_rad"] for row in reverse["Pinion_20T"]
                                   if row["frame"] == 1021), -2 * math.pi)
        self.assertAlmostEqual(next(row["angle_rad"] for row in reverse["Gear_40T"]
                                   if row["frame"] == 1021), math.pi)

    def test_blender_load_report_must_match_registered_asset_and_objects(self):
        from scripts.produce_lesson import validate_blender_asset_load_report
        planned = plan_lesson(self.load("spur_gears_full.json"))
        contract = planned["renderer_contract"]
        metadata = contract["asset_validation"]["metadata"]
        report = {"status": "PASS", "asset_id": contract["asset_id"],
                  "asset_sha256": contract["asset_validation"]["sha256"],
                  "blender_loaded_objects": metadata["objects"],
                  "loaded_objects_present": True, "pivot_validation": "PASS",
                  "centers_fixed_during_animation": True,
                  "fixed_center_validation": {"status": "PASS"}}
        validate_blender_asset_load_report(report, contract)
        report["asset_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "does not prove"):
            validate_blender_asset_load_report(report, contract)
        report["asset_sha256"] = contract["asset_validation"]["sha256"]
        report["blender_loaded_objects"] = metadata["objects"][:-1]
        with self.assertRaisesRegex(RuntimeError, "does not prove"):
            validate_blender_asset_load_report(report, contract)

    def test_full_gear_lesson_cannot_silently_fall_back_to_manim(self):
        from scripts.produce_lesson import renderer_runtime_preflight
        spec = self.load("spur_gears_full.json")
        plan = plan_lesson(spec)
        with patch("scripts.produce_lesson.subprocess.run") as run:
            with self.assertRaisesRegex(RendererResolutionError, "no renderer fallback"):
                renderer_runtime_preflight(resolve_renderer(spec["topic"]),
                                           plan["renderer_contract"], manim_only=True)
        self.assertFalse(run.called)

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

    def test_external_gear_pitch_point_and_no_slip_velocity_match(self):
        from core.education.gear_kinematics import external_spur_gear_kinematics, vertical_velocity_direction
        result = external_spur_gear_kinematics(20, 40, .002, 1.0)
        self.assertEqual(result["pinion_pitch_radius_m"], .02)
        self.assertEqual(result["gear_pitch_radius_m"], .04)
        self.assertEqual(result["center_distance_m"], .06)
        self.assertEqual(result["pinion_center_m"], (0.0, 0.0))
        self.assertEqual(result["gear_center_m"], (.06, 0.0))
        self.assertEqual(result["pitch_point_m"], (.02, 0.0))
        self.assertAlmostEqual(abs(result["pitch_point_m"][0] - result["pinion_center_m"][0]),
                               result["pinion_pitch_radius_m"])
        self.assertAlmostEqual(abs(result["gear_center_m"][0] - result["pitch_point_m"][0]),
                               result["gear_pitch_radius_m"])
        self.assertLess(result["pinion_angular_velocity_rad_s"] * result["gear_angular_velocity_rad_s"], 0)
        self.assertAlmostEqual(result["gear_angular_velocity_rad_s"], -.5)
        self.assertEqual(result["pinion_pitch_velocity_m_s"], (0.0, .02))
        self.assertEqual(result["gear_pitch_velocity_m_s"], (0.0, .02))
        self.assertEqual(vertical_velocity_direction(result["pinion_pitch_velocity_m_s"]), 1)

    def test_external_gear_reverse_input_reverses_both_common_tangent_velocities(self):
        from core.education.gear_kinematics import external_spur_gear_kinematics, vertical_velocity_direction
        result = external_spur_gear_kinematics(20, 40, .002, -1.0)
        self.assertAlmostEqual(result["gear_angular_velocity_rad_s"], .5)
        self.assertLess(result["pinion_angular_velocity_rad_s"] * result["gear_angular_velocity_rad_s"], 0)
        self.assertEqual(result["pinion_pitch_velocity_m_s"], (0.0, -.02))
        self.assertEqual(result["gear_pitch_velocity_m_s"], (0.0, -.02))
        self.assertEqual(vertical_velocity_direction(result["pinion_pitch_velocity_m_s"]), -1)

    def test_external_gear_zero_speed_has_no_tangent_velocity_direction(self):
        from core.education.gear_kinematics import external_spur_gear_kinematics, vertical_velocity_direction
        result = external_spur_gear_kinematics(20, 40, .002, 0.0)
        self.assertEqual(result["gear_angular_velocity_rad_s"], 0.0)
        self.assertEqual(result["pinion_pitch_velocity_m_s"], (0.0, 0.0))
        self.assertEqual(result["gear_pitch_velocity_m_s"], (0.0, 0.0))
        self.assertEqual(vertical_velocity_direction(result["pinion_pitch_velocity_m_s"]), 0)

    def test_planning_does_not_mutate_the_source_lesson_spec(self):
        spec = self.load("spur_gears.json")
        before = copy.deepcopy(spec)
        plan_lesson(spec)
        self.assertEqual(spec, before)


if __name__ == "__main__":
    unittest.main()
