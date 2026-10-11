from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from core.education.education_planner import plan_lesson
from core.education.blender_compat import configure_eevee
from core.education.renderer_registry import RendererResolutionError, validate_battery_asset_load_report
from core.simulation_engines.battery.result_validator import load_validated_result
from core.simulation_engines.battery.trace import TRACE_SCHEMA, validate_trace
from core.simulation_engines.battery.schema import validate_config

ROOT = Path(__file__).resolve().parents[1]


class BatteryContractTests(unittest.TestCase):
    def test_result_metadata_matches_rows_and_event_endpoint(self):
        from core.simulation_engines.battery.result_validator import validate_timeseries

        rows = [
            {"time_s": 0, "terminal_voltage_v": 4.1, "current_a": 5,
             "discharge_capacity_ah": 0, "estimated_soc": 1.0},
            {"time_s": 60, "terminal_voltage_v": 3.9, "current_a": 5,
             "discharge_capacity_ah": 60 * 5 / 3600, "estimated_soc": 1 - 60 / 3600},
            {"time_s": 90, "terminal_voltage_v": 3.8, "current_a": 5,
             "discharge_capacity_ah": 90 * 5 / 3600, "estimated_soc": 1 - 90 / 3600},
        ]
        metadata = {"sample_count": 3, "sample_interval_s": 60, "actual_end_time_s": 90,
                    "requested_duration_s": 7200, "termination_reason": "event: Minimum voltage [V]",
                    "event_time_s": 90, "voltage_cutoff_lower_v": 2.5, "voltage_cutoff_upper_v": 4.5,
                    "initial_soc": 1.0, "nominal_capacity_ah": 5.0}
        self.assertEqual(validate_timeseries(rows, metadata), [])
        invalid = dict(metadata, sample_count=4)
        self.assertTrue(any("sample_count" in error for error in validate_timeseries(rows, invalid)))
        invalid = dict(metadata, event_time_s=100)
        self.assertTrue(any("event_time_s" in error for error in validate_timeseries(rows, invalid)))

    def test_blender_eevee_compat_selects_engine_exposed_by_runtime(self):
        from types import SimpleNamespace

        def scene_with(*identifiers):
            enum_items = [SimpleNamespace(identifier=value) for value in identifiers]
            render = SimpleNamespace(bl_rna=SimpleNamespace(properties={
                "engine": SimpleNamespace(enum_items=enum_items)}), engine="")
            return SimpleNamespace(render=render, eevee=SimpleNamespace(taa_render_samples=0))

        blender_52 = scene_with("BLENDER_EEVEE", "BLENDER_WORKBENCH")
        self.assertEqual(configure_eevee(blender_52, 4), "BLENDER_EEVEE")
        self.assertEqual(blender_52.eevee.taa_render_samples, 8)
        prior_build = scene_with("BLENDER_EEVEE_NEXT")
        self.assertEqual(configure_eevee(prior_build, 16), "BLENDER_EEVEE_NEXT")
        with self.assertRaisesRegex(RuntimeError, "Eevee renderer unavailable"):
            configure_eevee(scene_with("BLENDER_WORKBENCH"), 16)

    def test_blender_still_preflight_does_not_require_manim(self):
        from subprocess import CompletedProcess
        from scripts.produce_lesson import renderer_runtime_preflight

        contract = {"selected_modes": ["blender", "manim"]}
        with mock.patch("core.mechanism.renderer._blender_binary", return_value="/tmp/blender"), \
             mock.patch("scripts.produce_lesson.subprocess.run",
                        return_value=CompletedProcess(args=["/tmp/blender"], returncode=0,
                                                      stdout="Blender 5.2.1\n", stderr="")) as run:
            versions = renderer_runtime_preflight(None, contract, blender_only=True)
        self.assertEqual(versions, {"blender": "Blender 5.2.1"})
        run.assert_called_once_with(["/tmp/blender", "--version"], cwd=ROOT,
                                    capture_output=True, text=True, check=True)

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
            with mock.patch("core.simulation_engines.battery.trace.load_validated_result",
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
