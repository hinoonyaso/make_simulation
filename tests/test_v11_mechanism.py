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
from core.mechanism.adapters.attention import SelfAttentionAdapter
from core.mechanism.trace_contract import make_envelope, validate_envelope
from core.simulation.environments.registry import EnvironmentRegistry
from core.simulation.environments.loader import EnvironmentLoader


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

    def test_asymmetric_quantization_positive_negative_and_constant_ranges(self):
        from core.mechanism.adapters.quantization import quantize_array
        for values in ([1.0, 2.0], [-2.0, -1.0], [-2.0, 0.0, 1.0], [0.0, 0.0], [3.0, 3.0]):
            got = quantize_array(np.asarray(values, dtype=float), 8, "asymmetric", "per_tensor")
            self.assertGreater(float(np.asarray(got["scale"]).min()), 0)
            self.assertTrue(np.all(np.asarray(got["quantized_integer"]) >= got["qmin"]))
            self.assertTrue(np.all(np.asarray(got["quantized_integer"]) <= got["qmax"]))
            self.assertTrue(np.allclose(np.asarray(got["dequantized"]),
                                        (np.asarray(got["quantized_integer"]) - got["zero_point"]) * got["scale"]))
            if values == [1.0, 2.0] or values == [-2.0, -1.0]:
                self.assertLess(got["max_absolute_error"], .01)

    def test_quantization_int4_int8_schemes_granularity_and_saturation(self):
        from core.mechanism.adapters.quantization import quantize_array
        values = np.array([[-100.0, 0, 100.0], [-.5, .25, .75]])
        for bits in (4, 8):
            for scheme in ("symmetric", "asymmetric"):
                for granularity in ("per_tensor", "per_channel"):
                    got = quantize_array(values, bits, scheme, granularity)
                    q = np.asarray(got["quantized_integer"])
                    self.assertTrue(np.all((q >= got["qmin"]) & (q <= got["qmax"])))
                    self.assertGreater(float(np.asarray(got["scale"]).min()), 0)
                    self.assertEqual(np.asarray(got["saturation_mask"]).shape, values.shape)

    def test_quantization_validator_rejects_tampered_codes(self):
        adapter = QuantizationAdapter()
        trace = adapter.execute({"weights": [1.0, 2.0], "scheme": "asymmetric"})
        trace["payload"]["quantized_integer"][1] = 17
        self.assertTrue(adapter.validate(trace))

    def test_registry_resolves_korean_aliases_and_reports_ambiguous(self):
        registry = MechanismRegistry()
        for alias, topic in (("양자화", "quantization"), ("INT8 양자화", "quantization"),
                             ("비최대 억제", "nms"), ("객체 탐지", "object_detection"),
                             ("모터 PID", "mcu_pid"), ("로봇팔 순기구학", "forward_kinematics"),
                             ("자율주행", "navigation2"), ("자기주의", "self_attention")):
            self.assertEqual(registry.resolve(alias)["topic"], topic)
        ambiguous = registry.resolve_detailed("attention")
        self.assertEqual(ambiguous["status"], "ambiguous")
        self.assertIsNone(registry.resolve("attention"))

    def test_nms_computes_iou_and_top_candidates(self):
        adapter = NMSAdapter()
        trace = adapter.execute({})
        self.assertEqual(adapter.validate(trace), [])
        self.assertAlmostEqual(intersection_over_union(np.array([0, 0, 2, 2]), np.array([1, 1, 3, 3])), 1/7)
        self.assertEqual(trace["payload"]["kept_ids"], ["box-01", "box-03", "box-05"])

    def test_nms_validator_recomputes_comparisons_and_selection(self):
        adapter = NMSAdapter(); trace = adapter.execute({})
        trace["payload"]["steps"][0]["comparisons"][0]["iou"] = .01
        self.assertTrue(adapter.validate(trace))

    def test_pid_samples_are_monotonic_and_pwm_bounded(self):
        adapter = MCUPIDAdapter(); trace = adapter.execute({"duration": .2, "dt": .02})
        self.assertEqual(adapter.validate(trace), [])
        rows = trace["payload"]["samples"]
        self.assertEqual(len(rows), 11)
        self.assertEqual([r["time_s"] for r in rows], sorted(r["time_s"] for r in rows))
        self.assertTrue(all(-1 <= r["pwm_duty"] <= 1 for r in rows))
        self.assertFalse(trace["payload"]["hardware_firmware_executed"])

    def test_pid_validator_rejects_plant_and_encoder_tampering(self):
        adapter = MCUPIDAdapter(); trace = adapter.execute({"duration": .2, "dt": .02})
        trace["payload"]["samples"][2]["motor_speed_rad_s"] += .2
        self.assertTrue(adapter.validate(trace))

    def test_self_attention_trace_computes_qk_softmax_and_weighted_values(self):
        adapter = SelfAttentionAdapter()
        trace = adapter.execute({"causal_mask": True})
        self.assertEqual(adapter.validate(trace), [])
        weights = np.asarray(trace["payload"]["attention_weights"])
        self.assertTrue(np.allclose(weights.sum(axis=1), 1))
        self.assertEqual(weights[0, 1:].tolist(), [0.0, 0.0])
        trace["payload"]["output"][0][0] += 1
        self.assertTrue(adapter.validate(trace))

    def test_environment_registry_never_claims_unrun_backend_as_ready(self):
        registry = EnvironmentRegistry()
        self.assertIn("clearpath.office.v1", {row["id"] for row in registry.list()})
        preflight = EnvironmentLoader(registry).preflight("clearpath.office.v1")
        self.assertFalse(preflight["ready"])
        self.assertEqual(preflight["environment"]["load_test_status"], "blocked_missing_ros2_gazebo")

    def test_safe_archive_extractor_rejects_path_traversal(self):
        import importlib.util, stat, tempfile, zipfile
        module_path = ROOT / "core/visual-assets/safe_archive.py"
        spec = importlib.util.spec_from_file_location("safe_archive", module_path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as bundle: bundle.writestr("../escape.txt", "bad")
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                module.safe_extract_archive(archive, root / "out")
            self.assertFalse((root / "escape.txt").exists())
            symlink_archive = root / "link.zip"
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(symlink_archive, "w") as bundle: bundle.writestr(info, "../../outside")
            with self.assertRaisesRegex(ValueError, "symlink"):
                module.safe_extract_archive(symlink_archive, root / "links")
            size_archive = root / "large.zip"
            with zipfile.ZipFile(size_archive, "w") as bundle: bundle.writestr("payload", "123456")
            with self.assertRaisesRegex(ValueError, "expanded size limit"):
                module.safe_extract_archive(size_archive, root / "large", max_expanded_bytes=5)

    def test_pinned_archive_fetch_hashes_atomically_and_reuses_verified_cache(self):
        import hashlib, importlib.util, io, tempfile, zipfile
        from unittest.mock import patch
        module_path = ROOT / "core/visual-assets/safe_archive.py"
        spec = importlib.util.spec_from_file_location("safe_archive_fetch", module_path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as bundle: bundle.writestr("models/asset.txt", "verified")
        archive = buffer.getvalue(); digest = hashlib.sha256(archive).hexdigest()
        class Response:
            def __init__(self, body=b"", headers=None): self.body=body; self.headers=headers or {}; self.offset=0
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self, size=-1):
                part=self.body[self.offset:] if size < 0 else self.body[self.offset:self.offset+size]
                self.offset += len(part); return part
        class Opener:
            def __init__(self): self.calls=0
            def open(self, request, timeout):
                self.calls += 1
                if getattr(request, "method", None) == "HEAD": return Response(headers={"Content-Length":str(len(archive))})
                return Response(archive)
        opener = Opener()
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "asset"
            with patch.object(module.urllib.request, "build_opener", return_value=opener):
                result = module.fetch_pinned_archive(url="https://example.org/a.zip", destination=destination,
                    sha256=digest, size_bytes=len(archive), allowed_hosts=["example.org"])
                self.assertEqual(result["status"], "downloaded_and_hash_verified")
                self.assertEqual((destination / "models/asset.txt").read_text(), "verified")
                cached = module.fetch_pinned_archive(url="https://example.org/a.zip", destination=destination,
                    sha256=digest, size_bytes=len(archive), allowed_hosts=["example.org"])
                self.assertEqual(cached["status"], "cache_hit")
                self.assertEqual(opener.calls, 2)

    def test_attention_domain_validator_is_used_by_manifest(self):
        import importlib.util, tempfile
        validator_path = ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py"
        spec = importlib.util.spec_from_file_location("manifest_v11", validator_path)
        validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
        trace = SelfAttentionAdapter().execute({})
        trace["payload"]["output"][0][0] += 1
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); (folder / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
            manifest = {"beats":[{"id":"B1","text":"검증","caption":"검증","sec":2,
                "object":"trace","state_change":"computed → checked","focus":"calculation",
                "tool":"M","evidence":"toy_simulation","trace":"trace.json"}]}
            path = folder / "visual_manifest.json"; path.write_text(json.dumps(manifest), encoding="utf-8")
            errors, _ = validator.validate(str(path))
            self.assertTrue(any("attention output" in error for error in errors), errors)

    def test_manifest_rejects_unknown_mechanism_envelope_topic(self):
        import importlib.util, tempfile
        validator_path = ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py"
        spec = importlib.util.spec_from_file_location("manifest_unknown_v11", validator_path)
        validator = importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)
        trace = make_envelope(domain="unknown", topic="made_up", execution_type="toy_simulation",
                              inputs=[], operations=[], outputs=[], payload={})
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp); (folder / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
            manifest = {"beats":[{"id":"B1","text":"검증","caption":"검증","sec":2,
                "object":"trace","state_change":"computed → checked","focus":"calculation",
                "tool":"M","evidence":"toy_simulation","trace":"trace.json"}]}
            path = folder / "visual_manifest.json"; path.write_text(json.dumps(manifest), encoding="utf-8")
            errors, _ = validator.validate(str(path))
            self.assertTrue(any("unknown mechanism topic" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
