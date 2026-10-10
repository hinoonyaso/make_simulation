import copy
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.mechanism.engineering_trace import validate_discrete_events, validate_time_series
from core.mechanism.registry import MechanismRegistry
from core.simulation_engines.communication.can_protocol import arbitrate, bit_stuff, crc15_can
from core.mechanism.storyboard import build_storyboard
from core.mechanism.timeline import build_timeline


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

    def test_oscillator_non_divisible_duration_keeps_terminal_sample_everywhere(self):
        from core.mechanism.adapters.physics_oscillator import PhysicsOscillatorAdapter
        from scripts.produce_video import _build_run_timeline
        adapter = PhysicsOscillatorAdapter()
        trace = adapter.execute({"mass_kg": 1.0, "damping_n_s_m": 0.6,
            "stiffness_n_m": 4.0, "initial_displacement_m": 0.25,
            "initial_velocity_m_s": 0.0, "duration_s": 1.05,
            "sample_period_s": 0.1})
        payload = trace["payload"]
        times = payload["timestamps"]
        self.assertEqual(len(times), 12)
        for actual, expected in zip(times[:-1], [i / 10 for i in range(11)]):
            self.assertAlmostEqual(actual, expected, places=14)
        self.assertEqual(times[-1], 1.05)
        self.assertEqual(trace["timestamps"], times)
        for signal in payload["signals"].values():
            self.assertEqual(len(signal["values"]), len(times))
        self.assertEqual(payload["validation"]["sample_count"], len(times))
        self.assertLess(payload["validation"]["max_abs_analytic_error_m"], 2e-7)
        self.assertTrue(math.isfinite(payload["validation"]["energy_balance_residual_j"]))
        self.assertEqual(adapter.validate(trace), [])
        plan = adapter.build_visual_plan(trace)
        manifest = build_storyboard(trace["topic"], trace, plan, "trace.json", render_mode="preview")
        timeline = _build_run_timeline(trace["topic"], trace, manifest, "numerical_explanation")
        self.assertEqual(timeline["source_range_sec"], [0.0, 1.05])
        from core.mechanism.engineering_playback import engineering_state_for_frame
        self.assertEqual(engineering_state_for_frame(plan, timeline, 0)["source_time_sec"], 0.0)
        self.assertEqual(engineering_state_for_frame(
            plan, timeline, timeline["total_frames"]-1)["source_time_sec"], 1.05)

    def test_oscillator_timestamp_builder_boundaries_and_sample_limit(self):
        from core.mechanism.adapters.physics_oscillator import _build_timestamps
        cases = ((1.0, .1, 11), (1.05, .1, 12), (.25, .1, 4),
                 (.3, .1, 4), (.001, .0001, 11), (.05, .1, 2))
        for duration, sample, expected_count in cases:
            with self.subTest(duration=duration, sample=sample):
                times = _build_timestamps(duration, sample)
                self.assertEqual(len(times), expected_count)
                self.assertEqual(times[0], 0.0)
                self.assertEqual(times[-1], duration)
                self.assertTrue(all(math.isfinite(t) for t in times))
                self.assertTrue(all(a < b for a, b in zip(times, times[1:])))
        with self.assertRaisesRegex(ValueError, "2..1,000,000"):
            _build_timestamps(99_999.95, .1)
        for duration, sample in ((0, .1), (-1, .1), (float("nan"), .1),
                                 (float("inf"), .1), (1, 0), (1, -1),
                                 (1, float("nan")), (1, float("inf"))):
            with self.subTest(invalid_duration=duration, invalid_sample=sample):
                with self.assertRaises(ValueError):
                    _build_timestamps(duration, sample)

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
        self.assertEqual(crc15_can(bits), 0x64FE)  # independently derived CRC-15/CAN vector
        check_bits = [(byte >> shift) & 1 for byte in b"123456789" for shift in range(7, -1, -1)]
        self.assertEqual(crc15_can(check_bits), 0x059E)  # CRC-15/CAN catalogue check value
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

    def test_can_event_wire_index_and_ack_slot_are_exact(self):
        result = arbitrate([{"node":"loser","id":0x07C,"data":"01"},
                            {"node":"winner","id":0x078,"data":"01"}], receivers=["rx"])
        lost = next(event for event in result["events"] if event["event"] == "ARBITRATION_LOST")
        # Independent raw-to-wire position map: record the physical slot before
        # adding any stuff bit caused by the current raw bit.
        raw = [0, *[(0x07C >> i) & 1 for i in range(10, -1, -1)], 0]
        positions, wire = [], []
        last, run = None, 0
        for bit in raw:
            positions.append(len(wire))
            wire.append(bit)
            run = run + 1 if bit == last else 1
            last = bit
            if run == 5:
                wire.append(1 - last)
                last, run = 1 - last, 1
        self.assertEqual(lost["bit_index"], 8)
        self.assertEqual(lost["timestamp"], positions[1 + lost["bit_index"]])
        self.assertEqual(result["physical_bits"][lost["timestamp"]], 0)
        ack = next(event for event in result["events"] if event["event"] == "ACK")
        ack_missing = arbitrate([{"node":"only","id":0x100,"data":"01"}])
        missing = next(event for event in ack_missing["events"] if event["event"] == "ACK_MISSING")
        encoded = result["physical_bits"]
        self.assertEqual(ack["timestamp"], len(encoded) - 12)
        self.assertEqual(encoded[ack["timestamp"]], 0)
        self.assertEqual(missing["timestamp"], len(ack_missing["physical_bits"]) - 12)
        self.assertEqual(ack_missing["physical_bits"][missing["timestamp"]], 1)

    def test_can_validator_rejects_mutated_protocol_evidence_even_with_rehashed_trace(self):
        from core.mechanism.adapters.can_arbitration import CANArbitrationAdapter
        adapter = CANArbitrationAdapter()
        original = adapter.execute({})
        cases = (
            ("events", lambda p: p["events"].append({"timestamp": 0, "node": "X", "event": "TX_REQUEST"})),
            ("event_timestamp", lambda p: p["events"][0].__setitem__("timestamp", p["events"][0]["timestamp"] + 1)),
            ("bit_count", lambda p: p.__setitem__("bit_count", p["bit_count"] + 1)),
            ("stuffed_bit_positions_before_ack", lambda p: p["stuffed_bit_positions_before_ack"].append(1)),
            ("stuffed_crc", lambda p: p["stuffed_crc"].append(0)),
            ("requests", lambda p: p["requests"][0].__setitem__("id", p["requests"][0]["id"] + 1)),
            ("receivers", lambda p: p["receivers"].append("tampered")),
            ("bitrate_hz", lambda p: p.__setitem__("bitrate_hz", 500_000)),
            ("bit_time_seconds", lambda p: p.__setitem__("bit_time_seconds", 1.0)),
            ("bit_time_ns", lambda p: p["bit_time_ns"].__setitem__(0, 1)),
            ("crc_polynomial", lambda p: p.__setitem__("crc_polynomial", "0x8005")),
            ("crc15", lambda p: p.__setitem__("crc15", p["crc15"] ^ 1)),
            ("physical_bits", lambda p: p["physical_bits"].__setitem__(0, 1)),
        )
        for label, mutate in cases:
            with self.subTest(field=label):
                trace = json.loads(json.dumps(original))
                mutate(trace["payload"])
                base = {key: trace[key] for key in ("domain", "topic", "execution_type", "inputs", "operations", "outputs", "payload")}
                digest = hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
                trace["trace_id"] = f"can_arbitration:{digest}"
                self.assertTrue(adapter.validate(trace), label)

    def test_can_cache_domain_validator_rejects_rehashed_event_tamper(self):
        from tempfile import TemporaryDirectory
        from core.mechanism.adapters.can_arbitration import CANArbitrationAdapter
        from core.mechanism.execution_cache import execute_cached
        from core.mechanism.run_management import file_hash
        adapter = CANArbitrationAdapter()
        with TemporaryDirectory() as directory:
            _, report = execute_cached("can_arbitration", {}, adapter, Path(directory))
            trace_path = Path(report["directory"]) / "trace.json"
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            trace["payload"]["events"][-1]["timestamp"] += 1
            base = {key: trace[key] for key in ("domain", "topic", "execution_type", "inputs", "operations", "outputs", "payload")}
            digest = hashlib.sha256(json.dumps(base, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
            trace["trace_id"] = f"can_arbitration:{digest}"
            trace_path.write_text(json.dumps(trace, sort_keys=True, ensure_ascii=False), encoding="utf-8")
            execution_report_path = Path(report["directory"]) / "execution_report.json"
            execution_report = json.loads(execution_report_path.read_text(encoding="utf-8"))
            execution_report["trace_sha256"] = file_hash(trace_path)
            execution_report_path.write_text(json.dumps(execution_report, sort_keys=True), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "execution cache REJECTED"):
                execute_cached("can_arbitration", {}, adapter, Path(directory))

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

    def test_engineering_playback_uses_common_time_and_signal_specific_interpolation(self):
        from core.mechanism.engineering_playback import (
            engineering_state_for_frame, signal_value_at, source_time_to_x,
        )
        trace = {"payload": {"kind":"time_series","timestamps": [0.0, .15, .3], "signals": {
            "speed_rad_s": {"unit": "rad/s", "timestamps": [0.0, .15, .3], "values": [0, 15, 30]},
            "speed_reference": {"unit": "rad/s", "timestamps": [0.0, .1, .2, .2999], "values": [0, 10, 20, 30]},
            "load_torque": {"unit": "N·m", "timestamps": [0.0, .3], "values": [0, .5]}}}}
        timeline = build_timeline([{"phase_id":"speed_response","sec":.3,"caption":"x"},
                                   {"phase_id":"held","sec":.2,"caption":"y"}],
            fps=10, source_range=(0.0,.3), phase_source={
                "speed_response":{"source_start_sec":0.0,"source_end_sec":.3,"playback_mode":"replay"},
                "held":{"source_start_sec":.3,"source_end_sec":.3,"playback_mode":"hold"}})
        first = engineering_state_for_frame(trace, timeline, 0)
        middle = engineering_state_for_frame(trace, timeline, 1)
        last = engineering_state_for_frame(trace, timeline, 2)
        held = engineering_state_for_frame(trace, timeline, 3)
        self.assertEqual(first["source_time_sec"], 0.0)
        self.assertAlmostEqual(middle["source_time_sec"], .15)
        self.assertEqual(middle["signals"]["speed_rad_s"]["value"], 15.0)
        self.assertEqual(middle["signals"]["speed_reference"]["value"], 10.0)
        self.assertEqual(middle["signals"]["speed_reference"]["interpolation"], "zero_order_hold")
        self.assertEqual(last["source_time_sec"], .3)
        self.assertEqual(held["source_time_sec"], .3)
        self.assertEqual(held["phase_id"], "held")
        self.assertAlmostEqual(signal_value_at(trace["payload"]["signals"]["speed_rad_s"], .075, "linear"), 7.5)
        self.assertEqual(signal_value_at(trace["payload"]["signals"]["speed_reference"], .15, "zero_order_hold"), 10.0)
        self.assertEqual(source_time_to_x(.0,(0.0,.3),-5,5),-5)
        self.assertAlmostEqual(source_time_to_x(.2999,(0.0,.3),-5,5),4.9966666667)
        self.assertEqual(source_time_to_x(.3,(0.0,.3),-5,5),5)
        with self.assertRaisesRegex(ValueError, "outside timeline"):
            engineering_state_for_frame(trace, timeline, timeline["total_frames"])

    def test_engineering_playback_fps_changes_do_not_mutate_trace_or_clock(self):
        from core.mechanism.engineering_playback import engineering_state_for_frame
        trace = {"payload": {"kind":"time_series","timestamps": [0.0, .3], "signals": {
            "speed_rad_s": {"unit":"rad/s","timestamps":[0.0,.3],"values":[0.0,30.0]}}}}
        original = copy.deepcopy(trace)
        states = []
        for fps in (10, 20, 30):
            timeline = build_timeline([{"phase_id":"response","sec":.3,"caption":"x"}], fps=fps,
                source_range=(0.0,.3), phase_source={"response":{"source_start_sec":0.0,
                    "source_end_sec":.3,"playback_mode":"replay"}})
            states.append((engineering_state_for_frame(trace,timeline,0),
                           engineering_state_for_frame(trace,timeline,timeline["total_frames"]-1)))
        self.assertEqual(trace, original)
        for first,last in states:
            self.assertEqual(first["signals"]["speed_rad_s"]["value"],0.0)
            self.assertEqual(last["signals"]["speed_rad_s"]["value"],30.0)


if __name__ == "__main__":
    unittest.main()
