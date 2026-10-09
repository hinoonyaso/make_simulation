import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.mechanism.registry import MechanismRegistry
from core.mechanism.adapters.quantization import QuantizationAdapter
from core.mechanism.adapters.nms import NMSAdapter, intersection_over_union
from core.mechanism.adapters.mcu_pid import MCUPIDAdapter
from core.mechanism.trace_contract import make_envelope, validate_envelope


class MechanismAdapterTests(unittest.TestCase):
    def test_registry_routes_ready_adapters_and_marks_unimplemented_topics(self):
        registry = MechanismRegistry()
        for topic in ("quantization", "nms", "mcu_pid", "rag", "robot_kinematics"):
            self.assertEqual(registry.require_executable(topic)["implementation_status"], "ready")
        self.assertEqual(registry.resolve("VLA")["implementation_status"], "planned")
        self.assertIn("self_attention", {row["topic"] for row in registry.list_capabilities()})

    def test_envelope_rejects_unordered_timestamps(self):
        trace = make_envelope(domain="test", topic="unit", execution_type="numerical_simulation",
            inputs=[], operations=[], outputs=[], payload={}, timestamps=[0, 1])
        self.assertEqual(validate_envelope(trace), [])
        trace["timestamps"] = [1, 0]
        self.assertTrue(any("monotonic" in error for error in validate_envelope(trace)))

    def test_quantization_reconstructs_values_for_symmetric_and_per_channel(self):
        adapter = QuantizationAdapter()
        trace = adapter.execute({"weights": [[-1, 0, 1], [-.5, .2, .7]], "bits": 8,
                                 "scheme": "symmetric", "granularity": "per_channel"})
        self.assertEqual(adapter.validate(trace), [])
        p = trace["payload"]
        self.assertEqual(np.asarray(p["scale"]).shape, (2, 1))
        self.assertTrue(np.all(np.asarray(p["absolute_error"]) >= 0))
        self.assertFalse(p["hardware_kernel_executed"])

    def test_quantization_distinguishes_weight_only_from_weight_and_activation(self):
        adapter = QuantizationAdapter()
        with self.assertRaisesRegex(ValueError, "requires an activations tensor"):
            adapter.execute({"scope": "weight_and_activation"})
        trace = adapter.execute({"scope": "weight_and_activation", "weights": [-.8, .3],
                                 "activations": [[0.0, .25], [.5, .75]], "bits": 4})
        self.assertEqual(adapter.validate(trace), [])
        self.assertEqual(trace["payload"]["scope"], "weight_and_activation")
        self.assertEqual([item["id"] for item in trace["inputs"]], ["weights", "activations"])
        self.assertEqual(len(trace["outputs"]), 2)
        plan = adapter.build_visual_plan(trace)
        self.assertIsNotNone(plan["activation_max_absolute_error"])

    def test_nms_computes_iou_and_top_candidates(self):
        adapter = NMSAdapter()
        trace = adapter.execute({})
        self.assertEqual(adapter.validate(trace), [])
        self.assertAlmostEqual(intersection_over_union(np.array([0, 0, 2, 2]), np.array([1, 1, 3, 3])), 1/7)
        self.assertEqual(trace["payload"]["kept_ids"], ["box-01", "box-03", "box-05"])

    def test_pid_samples_are_monotonic_and_pwm_bounded(self):
        trace = MCUPIDAdapter().execute({"duration": .2, "dt": .02})
        self.assertEqual(validate_envelope(trace), [])
        rows = trace["payload"]["samples"]
        self.assertEqual(len(rows), 11)
        self.assertEqual([r["time_s"] for r in rows], sorted(r["time_s"] for r in rows))
        self.assertTrue(all(-1 <= r["pwm_duty"] <= 1 for r in rows))
        self.assertFalse(trace["payload"]["hardware_firmware_executed"])


if __name__ == "__main__":
    unittest.main()
