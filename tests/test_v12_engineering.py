import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.mechanism.engineering_trace import validate_discrete_events, validate_time_series
from core.mechanism.registry import MechanismRegistry
from core.simulation_engines.communication.can_protocol import arbitrate, bit_stuff, crc15_can
from core.mechanism.storyboard import build_storyboard


class V12EngineeringTests(unittest.TestCase):
    def test_registry_exposes_only_three_executable_engineering_topics(self):
        registry = MechanismRegistry()
        cases = (("감쇠 진동", "physics_oscillator"), ("CAN 중재", "can_arbitration"),
                 ("PMSM FOC", "motor_foc"))
        for alias, topic in cases:
            self.assertEqual(registry.require_executable(alias)["topic"], topic)
        self.assertIsNone(registry.resolve("BLDC"))

    def test_oscillator_sympy_scipy_control_energy_and_forced_cases(self):
        from core.mechanism.adapters.physics_oscillator import PhysicsOscillatorAdapter
        adapter = PhysicsOscillatorAdapter()
        for damping, force in ((0.0, 0.0), (0.6, 0.0), (6.0, 0.0), (0.6, 0.4)):
            trace = adapter.execute({"mass_kg": 1, "damping_n_s_m": damping,
                "stiffness_n_m": 4, "initial_displacement_m": .25,
                "duration_s": 1.0, "sample_period_s": .01,
                "force_amplitude_n": force, "force_frequency_hz": .7})
            self.assertEqual(adapter.validate(trace), [])
            payload = trace["payload"]
            self.assertIn("python-control", trace["operations"][2]["engine"])
            if force == 0:
                self.assertLess(payload["validation"]["max_abs_analytic_error_m"], 2e-7)
            if damping == 0 and force == 0:
                self.assertLess(payload["validation"]["relative_energy_drift"], 1e-7)
            sweep = payload["damping_sweep"]["damping_n_s_m"]
            self.assertAlmostEqual(sweep["critical"], 2*(4**.5))
            self.assertEqual(len(payload["signals"]["position_overdamped"]["values"]),
                             len(payload["timestamps"]))
        with self.assertRaisesRegex(ValueError, "mass_kg"):
            adapter.execute({"mass_kg": 0})
        with self.assertRaisesRegex(ValueError, "finite"):
            adapter.execute({"stiffness_n_m": float("nan")})

    def test_generic_time_series_supports_independent_sample_clocks(self):
        trace = {"kind": "time_series", "timestamps": [0.0, 1.0], "signals": {
            "slow": {"unit": "m", "values": [0.0, 1.0]},
            "fast": {"unit": "A", "timestamps": [0.0, .5, 1.0], "values": [0.0, 2.0, 0.0]}}}
        self.assertEqual(validate_time_series(trace), [])
        trace["signals"]["fast"]["timestamps"] = [0.0, 0.0, 1.0]
        self.assertTrue(validate_time_series(trace))
        events = {"kind": "discrete_events", "events": [
            {"timestamp": 0, "node": "A", "event": "TX"},
            {"timestamp": 1, "node": "B", "event": "LOST"}]}
        self.assertEqual(validate_discrete_events(events), [])

    def test_physics_execution_cache_hits_only_validated_identical_trace(self):
        from tempfile import TemporaryDirectory
        from core.mechanism.adapters.physics_oscillator import PhysicsOscillatorAdapter
        from core.mechanism.execution_cache import execute_cached
        adapter = PhysicsOscillatorAdapter()
        with TemporaryDirectory() as directory:
            trace, first = execute_cached("physics_oscillator", {"duration_s":.3,"sample_period_s":.01},
                                          adapter,Path(directory))
            replay, second = execute_cached("physics_oscillator", {"duration_s":.3,"sample_period_s":.01},
                                            adapter,Path(directory))
            self.assertEqual(first["cache_status"],"MISS")
            self.assertEqual(second["cache_status"],"HIT")
            self.assertEqual(trace["trace_id"],replay["trace_id"])
            stored = Path(second["directory"])/"trace.json"
            raw = stored.read_text(encoding="utf-8").replace('"trace_id":', '"edited_trace_id":', 1)
            stored.write_text(raw,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"execution cache REJECTED"):
                execute_cached("physics_oscillator", {"duration_s":.3,"sample_period_s":.01},
                               adapter,Path(directory))

    def test_group_export_is_lock_derived_and_excludes_project_ai_stack(self):
        from scripts.export_v12_requirements import export
        packages = {p["name"].lower(): p["version"] for p in export(
            ["sim-math", "sim-can", "sim-motor", "sim-render"])}
        self.assertEqual(packages["motulator"], "0.9.0")
        self.assertEqual(packages["manim"], "0.21.0")
        self.assertIn("scipy", packages)
        self.assertNotIn("torch", packages)
        self.assertNotIn("mujoco", packages)
        self.assertNotIn("edge-tts", packages)

    def test_can_crc_bit_stuff_arbitration_ack_and_equal_id_edges(self):
        self.assertEqual(bit_stuff([1, 1, 1, 1, 1])[0], (1, 1, 1, 1, 1, 0))
        # Independent polynomial long division for CRC-15/CAN.
        bits = [0, 1, 0, 1, 1, 0, 1, 0]
        poly = 0x4599
        dividend = 0
        for bit in bits:
            dividend = (dividend << 1) | bit
        dividend <<= 15
        for shift in range(len(bits) + 14, 14, -1):
            if dividend & (1 << shift):
                dividend ^= poly << (shift - 15)
        self.assertEqual(crc15_can(bits), dividend & 0x7FFF)
        two = arbitrate([{"node":"A","id":0x100,"data":"01"},
                         {"node":"B","id":0x200,"data":"02"}], receivers=["R"])
        self.assertEqual(two["winners"], ["A"])
        self.assertTrue(two["acknowledged"])
        three = arbitrate([{"node":"A","id":0x100,"data":"01"},
                           {"node":"B","id":0x200,"data":"02"},
                           {"node":"C","id":0x300,"data":"03"}], receivers=["R"])
        self.assertEqual(three["winners"], ["A"])
        same = arbitrate([{"node":"A","id":0x100,"data":"01"},
                          {"node":"B","id":0x100,"data":"01"}], receivers=["R"])
        self.assertEqual(same["winners"], ["A", "B"])
        conflict = arbitrate([{"node":"A","id":0x100,"data":"01"},
                              {"node":"B","id":0x100,"data":"02"}], receivers=["R"])
        self.assertEqual(conflict["status"], "bit_error_equal_arbitration")
        no_ack = arbitrate([{"node":"A","id":0x100,"data":"01"}])
        self.assertFalse(no_ack["acknowledged"])
        remote_priority = arbitrate([{"node":"R","id":0x100,"remote":True},
                                     {"node":"D","id":0x100,"data":"01"}], receivers=["RX"])
        self.assertEqual(remote_priority["winners"], ["D"])

    def test_can_adapter_virtualbus_dbc_and_domain_integrity(self):
        from core.mechanism.adapters.can_arbitration import CANArbitrationAdapter
        adapter = CANArbitrationAdapter()
        trace = adapter.execute({})
        self.assertEqual(adapter.validate(trace), [])
        p = trace["payload"]
        self.assertEqual(p["dbc_round_trip"]["status"], "PASS")
        self.assertEqual(p["python_can_virtual_bus"]["status"], "PASS")
        tampered = copy.deepcopy(trace)
        tampered["payload"]["physical_bits"][0] = 1
        self.assertTrue(adapter.validate(tampered))

    def test_motor_foc_trace_uses_motulator_pmsm_and_load_step(self):
        from core.mechanism.adapters.motor_foc import MotorFOCAdapter
        adapter = MotorFOCAdapter()
        config = {"duration_s": .15, "sample_period_s": .0001,
                  "load_step_time_s": .08, "speed_step_time_s": .005}
        trace = adapter.execute(config)
        self.assertEqual(adapter.validate(trace), [])
        p = trace["payload"]
        self.assertTrue(p["validation"]["load_step_detected"])
        self.assertIn("averaged", p["control"]["inverter_model"])
        self.assertGreater(len(p["signals"]["speed_reference"]["timestamps"]), 2)
        self.assertNotEqual(len(p["timestamps"]), len(p["signals"]["speed_reference"]["timestamps"]))
        tampered = copy.deepcopy(trace)
        tampered["payload"]["signals"]["speed_rpm"]["values"][10] += 100
        self.assertTrue(adapter.validate(tampered))

    def test_engineering_storyboard_and_timeline_are_trace_backed(self):
        from core.mechanism.adapters.physics_oscillator import PhysicsOscillatorAdapter
        from core.mechanism.adapters.can_arbitration import CANArbitrationAdapter
        from core.mechanism.adapters.motor_foc import MotorFOCAdapter
        from scripts.produce_video import _build_run_timeline
        for adapter, config in ((PhysicsOscillatorAdapter(), {"duration_s":.4}),
                                 (CANArbitrationAdapter(), {}),
                                 (MotorFOCAdapter(), {"duration_s":.12,"load_step_time_s":.07})):
            trace = adapter.execute(config)
            plan = adapter.build_visual_plan(trace)
            manifest = build_storyboard(trace["topic"],trace,plan,"trace.json",render_mode="preview")
            timeline = _build_run_timeline(trace["topic"],trace,manifest,"numerical_explanation")
            self.assertEqual([x["phase_id"] for x in timeline["phases"]],
                             [b["phase_id"] for b in manifest["beats"]])
            self.assertGreater(timeline["total_frames"], 0)


if __name__ == "__main__":
    unittest.main()
