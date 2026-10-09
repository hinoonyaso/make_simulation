import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "mujoco_adapter", ROOT / "core/robotics-simulation/mujoco_adapter.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class MujocoArmSimulationTests(unittest.TestCase):
    def test_actual_model_run_fk_and_repeatability(self):
        model = ROOT / "assets/unitree_h1/mjcf/h1_with_hand.xml"
        with tempfile.TemporaryDirectory() as temp:
            first_dir = Path(temp) / "first"
            second_dir = Path(temp) / "second"
            first = adapter.run_arm_experiment(model, first_dir)
            second = adapter.run_arm_experiment(model, second_dir)
            self.assertEqual(first["schema"], "robotics-visual-trace/v1")
            self.assertEqual(len(first["samples"]), 101)
            self.assertLessEqual(first["validation"]["fk_max_position_error_m"], 1e-9)
            self.assertGreater(first["validation"]["end_effector_travel_m"], .01)
            self.assertTrue(np.allclose(
                [sample["qpos"] for sample in first["samples"]],
                [sample["qpos"] for sample in second["samples"]], atol=1e-12, rtol=0))
            self.assertTrue(np.allclose(
                [sample["ee_pos"] for sample in first["samples"]],
                [sample["ee_pos"] for sample in second["samples"]], atol=1e-12, rtol=0))
            self.assertEqual(json.loads((first_dir / "trace.json").read_text())["model"]["engine_version"],
                             first["model"]["engine_version"])

    def test_rejects_incommensurate_sampling(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "divisible"):
                adapter.run_arm_experiment(ROOT / "assets/unitree_h1/mjcf/h1_with_hand.xml",
                                           temp, duration=1.0, timestep=.003,
                                           sample_period=.02)


if __name__ == "__main__":
    unittest.main()
