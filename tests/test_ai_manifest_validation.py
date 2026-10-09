import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py"
spec = importlib.util.spec_from_file_location("manifest_validator_errors", path)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class TraceDispatchFailureTests(unittest.TestCase):
    def _trace_result(self, content):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        trace = Path(temp.name) / "trace.json"
        trace.write_text(content, encoding="utf-8")
        return validator._trace_validator(trace)()

    def test_missing_trace_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = validator._trace_validator(Path(tmp) / "missing.json")()
        self.assertEqual(len(errors), 1)
        self.assertIn("missing trace file", errors[0])

    def test_invalid_json_and_non_object_are_reported(self):
        self.assertIn("invalid JSON", self._trace_result("{" )[0])
        self.assertEqual(self._trace_result("[]"), ["trace root must be a JSON object"])

    def test_unknown_schema_is_never_sent_to_robotics_validator(self):
        errors = self._trace_result(json.dumps({"schema": "future/v9"}))
        self.assertEqual(errors, ["unsupported trace schema: 'future/v9'"])

    def test_permission_error_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "trace.json"
            target.write_text("{}", encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                errors = validator._trace_validator(target)()
        self.assertIn("unreadable trace file", errors[0])

    def test_empty_ai_trace_and_missing_fields_return_validation_errors(self):
        errors = self._trace_result(json.dumps({"schema": "ai-mechanism-trace/v1"}))
        self.assertTrue(any("inputs must be" in item for item in errors))
        self.assertTrue(any("operations must be" in item for item in errors))

    def test_malformed_manifest_returns_error_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text("{", encoding="utf-8")
            errors, warnings = validator.validate(str(path))
        self.assertIn("invalid manifest JSON", errors[0])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
