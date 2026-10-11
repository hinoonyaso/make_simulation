from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from core.education.education_planner import plan_lesson
from core.education.renderer_registry import RendererResolutionError, validate_battery_asset_load_report
from core.simulation_engines.battery.result_validator import load_validated_result
from core.simulation_engines.battery.trace import TRACE_SCHEMA, validate_trace
from core.simulation_engines.battery.schema import validate_config

ROOT = Path(__file__).resolve().parents[1]


class BatteryContractTests(unittest.TestCase):
    def test_config_and_plan_are_valid_without_executing_solver(self):
        config = json.loads((ROOT / "examples/education/battery_spm_config.json").read_text())
        self.assertEqual(validate_config(config), [])
        planned = plan_lesson(json.loads((ROOT / "examples/education/battery_spm_smoke.json").read_text()))
        self.assertEqual(planned["evidence"]["status"], "PLANNED")
        self.assertEqual(planned["renderer_contract"]["registry_id"], "li_ion_battery")
        self.assertEqual(planned["renderer_contract"]["selected_modes"], ["blender", "manim"])

    def test_invalid_config_values_are_rejected(self):
        config = json.loads((ROOT / "examples/education/battery_spm_config.json").read_text())
        config["initial_soc"] = 1.5
        self.assertTrue(any("initial_soc" in error for error in validate_config(config)))
        config["initial_soc"] = 1.0
        config["model"] = "DFN"
        self.assertTrue(any("only SPM" in error for error in validate_config(config)))

    def test_trace_sidecar_revalidates_solver_files_and_hash_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in (("result.json", "{}"), ("simulation_config.json", "{}"),
                                  ("battery_timeseries.csv", "time_s\n0\n")):
                (root / name).write_text(content)
            trace = {"schema": TRACE_SCHEMA, "solver_id": "pybamm", "run_id": "run",
                     "result_sha256": "x", "config_sha256": "x", "sample_count": 2,
                     "actual_end_time_s": 1, "result_file": "result.json",
                     "config_file": "simulation_config.json", "timeseries_file": "battery_timeseries.csv"}
            path = root / "battery_trace.json"
            path.write_text(json.dumps(trace))
            with unittest.mock.patch("core.simulation_engines.battery.trace.load_validated_result",
                                     side_effect=ValueError("hash mismatch")):
                errors = validate_trace(path)
            self.assertTrue(any("hash mismatch" in error for error in errors))

    def test_blender_report_must_match_same_solver_run_and_cell_asset(self):
        spec = json.loads((ROOT / "examples/education/battery_spm_smoke.json").read_text())
        contract = plan_lesson(spec)["renderer_contract"]
        contract["solver_result"] = {"solver_id": "pybamm", "run_id": "run-1", "result_sha256": "abc"}
        report = {"status": "PASS", "validation_contract": "battery_education_asset",
                  "asset_id": contract["asset_id"],
                  "asset_sha256": contract["asset_validation"]["sha256"],
                  "battery_objects": contract["calculated_results"]["cell_object_names"],
                  "loaded_objects_present": True, "geometry_validation": "PASS",
                  "solver_id": "pybamm", "solver_run_id": "run-1", "solver_result_sha256": "abc"}
        validate_battery_asset_load_report(report, contract)
        invalid = copy.deepcopy(report)
        invalid["solver_run_id"] = "different-run"
        with self.assertRaisesRegex(RendererResolutionError, "PyBaMM run"):
            validate_battery_asset_load_report(invalid, contract)


if __name__ == "__main__":
    unittest.main()
