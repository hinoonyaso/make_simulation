from __future__ import annotations

import json
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory

from core.education.blueprint_registry import available_blueprints, get_blueprint
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
                         "coordinate_transform", "process_flow", "before_after"})
        self.assertIn("blender", get_blueprint("exploded_assembly")["renderers"])
        with self.assertRaises(ValueError):
            get_blueprint("unknown")

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
