from __future__ import annotations

import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory

from core.education.blueprint_registry import available_blueprints, get_blueprint, validate_asset_blueprint
from core.education.education_planner import plan_lesson
from core.education.evidence_router import route_evidence
from core.education.lesson_spec import LessonSpec, validate_lesson_spec
from core.education.lesson_validator import validate_manifest
from core.mechanism.timeline import validate_timeline

ROOT = Path(__file__).resolve().parents[1]


class EducationFirstTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "examples/education" / name).read_text(encoding="utf-8"))

    def test_bearing_concept_spec_and_manifest(self):
        spec = self.load("bearing.json")
        json_schema = json.loads((ROOT / "core/education/lesson_spec.schema.json").read_text(encoding="utf-8"))
        self.assertIn("beats", json_schema["required"])
        self.assertEqual(json_schema["properties"]["schema"]["const"], "education-lesson-spec/v1")
        self.assertEqual(validate_lesson_spec(spec), [])
        self.assertEqual(LessonSpec.from_dict(spec).topic, "ball_bearing")
        planned = plan_lesson(spec)
        self.assertEqual(validate_manifest(planned["visual_manifest"]), [])
        self.assertEqual(planned["evidence"]["status"], "CONCEPT_ONLY")
        self.assertEqual(planned["visual_manifest"]["asset_id"], "edu.bearing_6204.v1")
        self.assertFalse(planned["evidence"]["execution_required"])
        self.assertEqual(validate_timeline(planned["timeline"],
                         expected_phase_ids=[b["phase_id"] for b in spec["beats"]]), [])
        self.assertEqual(sum(b["sec"] for b in spec["beats"]), spec["duration_target_sec"])

    def test_invalid_spec_and_manifest_are_rejected(self):
        self.assertTrue(validate_lesson_spec({"topic": "x"}))
        spec = self.load("education_smoke.json")
        spec["beats"][0]["tool"] = "X"
        with self.assertRaisesRegex(ValueError, "visual manifest"):
            plan_lesson(spec)

    def test_blueprint_registry_is_deterministic(self):
        self.assertEqual(set(available_blueprints()), {"exploded_assembly", "layered_structure", "signal_timing",
                         "coordinate_transform", "process_flow", "before_after", "mechanism_motion"})
        self.assertIn("blender", get_blueprint("exploded_assembly")["renderers"])
        with self.assertRaises(ValueError):
            get_blueprint("unknown")

    def test_same_blueprint_routes_across_assets_and_rejects_unsupported_combinations(self):
        self.assertEqual(validate_asset_blueprint("edu.bldc_motor_concept.v1", "layered_structure")["renderer"], "blender")
        self.assertEqual(validate_asset_blueprint("edu.pcb_layered.v1", "layered_structure")["blueprint"], "layered_structure")
        with self.assertRaisesRegex(ValueError, "unsupported asset/blueprint combination"):
            validate_asset_blueprint("edu.pcb_layered.v1", "mechanism_motion")
        with self.assertRaisesRegex(ValueError, "does not support animation operations"):
            validate_asset_blueprint("edu.bearing_6204.v1", "exploded_assembly", {"rotate": True})

    def test_registry_backed_asset_loader_resolves_hash_and_license(self):
        from core.education.blender_asset_loader import resolve_education_asset
        resolved = resolve_education_asset("edu.bearing_6204.v1")
        self.assertTrue(resolved["path"].is_file())
        self.assertEqual(resolved["collection"], "6204 envelope and estimated internal teaching geometry")
        self.assertEqual(resolved["license"], "CC0-1.0")
        self.assertEqual(len(resolved["sha256"]), 64)

    def test_blender_asset_lessons_plan_from_manifest_asset_ids(self):
        for name, asset_id, duration in (("bldc_motor.json","edu.bldc_motor_concept.v1",20),
                                         ("pcb_via.json","edu.pcb_layered.v1",20)):
            spec=self.load(name)
            self.assertEqual(validate_lesson_spec(spec), [])
            planned=plan_lesson(spec)
            self.assertEqual(planned["visual_manifest"]["asset_id"],asset_id)
            self.assertEqual(planned["timeline"]["total_frames"],duration*30)
        spec=self.load("pcb_via.json")
        spec["beats"][0]["blueprint"]="mechanism_motion"
        with self.assertRaisesRegex(ValueError,"unsupported asset/blueprint combination"):
            plan_lesson(spec)

    def test_computed_mode_requires_solver(self):
        spec = self.load("bearing.json")
        spec["modes"] = ["computed_engineering_demonstration"]
        with self.assertRaisesRegex(ValueError, "requires a named solver"):
            route_evidence(spec, spec["beats"])

    def test_named_solver_is_not_reported_as_executed_without_adapter(self):
        spec = self.load("bearing.json")
        spec["modes"] = ["computed_engineering_demonstration"]
        spec["solver"] = "CalculiX"
        spec["trace"] = "future_trace.json"
        result = route_evidence(spec, spec["beats"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["execution_required"])

    def test_concept_smoke_plan_is_solver_free(self):
        planned = plan_lesson(self.load("education_smoke.json"))
        self.assertEqual(planned["evidence"]["status"], "CONCEPT_ONLY")
        self.assertEqual(len(planned["timeline"]["phases"]), 2)

    def test_caption_writer_splits_korean_sentences(self):
        from scripts.produce_lesson import write_captions
        spec = self.load("education_smoke.json")
        spec["beats"][0]["caption"] = "첫 문장입니다. 둘째 문장입니다."
        spec["beats"][1]["caption"] = ""
        with TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = plan_lesson(spec)["visual_manifest"]
            write_captions(manifest, output)
            vtt = (output / "subtitles.ko.vtt").read_text(encoding="utf-8")
        self.assertIn("첫 문장입니다.", vtt)
        self.assertIn("둘째 문장입니다.", vtt)
        self.assertEqual(vtt.count(" --> "), 2)


if __name__ == "__main__":
    unittest.main()
