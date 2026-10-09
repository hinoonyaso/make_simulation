import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


trace_mod = load("rag_trace", ROOT / "core/ai-mechanism/rag_trace.py")
primitives = load("primitives", ROOT / "core/ai-mechanism/primitives.py")
assets = load("asset_factory", ROOT / "core/visual-assets/asset_factory.py")


class AITraceTests(unittest.TestCase):
    def test_real_rag_run_adapts_and_validates(self):
        source = ROOT / "pilots/07_naive_rag/data/rag_run.json"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "trace.json"
            trace = trace_mod.adapt_rag_run(source, output)
            self.assertEqual(trace["schema"], "ai-mechanism-trace/v1")
            self.assertEqual(trace["outputs"][0]["retrieved_ids"], ["C08", "C11", "C07"])
            self.assertIsNone(trace["operations"][3]["execution_time_seconds"])
            self.assertGreater(trace["operations"][5]["execution_time_seconds"], 0)
            self.assertFalse(trace_mod.validate_trace(json.loads(output.read_text())))

    def test_rejects_invalid_operation_runtime(self):
        trace = {
            "schema": "ai-mechanism-trace/v1", "inputs": [{"id": "q"}],
            "operations": [{"id": "op", "evidence": "model_execution",
                             "execution_time_seconds": float("nan")}],
            "transitions": [{"id": "t", "operation_id": "op"}],
            "intermediate_values": [{"id": "v", "kind": "text"}],
            "outputs": [{"id": "out"}], "provenance": {"retrieval_runtime_seconds": None},
            "visualization": {"projection_is_lossy": True,
                              "render_time_semantics": "presentation time; not inference latency"},
        }
        self.assertTrue(any("execution_time_seconds" in e
                            for e in trace_mod.validate_trace(trace)))

    def test_rejects_bad_distance_and_projection_claim(self):
        trace = {
            "schema": "ai-mechanism-trace/v1", "inputs": [{"id": "q"}],
            "operations": [{"id": "op", "evidence": "model_execution"}],
            "transitions": [{"id": "t", "operation_id": "op"}],
            "intermediate_values": [{"id": "d", "kind": "squared_l2_distance", "value": -1}],
            "outputs": [{"id": "out"}], "provenance": {"retrieval_runtime_seconds": None},
            "visualization": {"projection_is_lossy": False,
                              "render_time_semantics": "presentation time; not inference latency"},
        }
        errors = trace_mod.validate_trace(trace)
        self.assertTrue(any("nonnegative" in e for e in errors))
        self.assertTrue(any("lossy projection" in e for e in errors))

    def test_rejects_duplicate_ids_and_unknown_operation(self):
        trace = {"schema": "ai-mechanism-trace/v1", "inputs": [{"id": "x"}],
                 "operations": [{"id": "op", "evidence": "model_execution"}],
                 "transitions": [{"id": "t", "operation_id": "missing"}],
                 "intermediate_values": [{"id": "x", "kind": "text"}],
                 "outputs": [{"id": "out"}], "provenance": {"retrieval_runtime_seconds": None},
                 "visualization": {"projection_is_lossy": True,
                                   "render_time_semantics": "presentation time; not inference latency"}}
        errors = trace_mod.validate_trace(trace)
        self.assertTrue(any("duplicate data id" in e for e in errors))
        self.assertTrue(any("unknown operation" in e for e in errors))


class PrimitiveTests(unittest.TestCase):
    def test_chunk_overlap_and_context_identity(self):
        chunks = primitives.chunk_windows("abcdefgh", 5, 2)
        self.assertEqual([c["text"] for c in chunks], ["abcde", "defgh"])
        context = primitives.assemble_context([{"id": "C1", "text": "one"},
                                              {"id": "C2", "text": "two"}])
        self.assertEqual(context, {"text": "one\n\ntwo", "source_ids": ["C1", "C2"]})
        with self.assertRaises(ValueError):
            primitives.assemble_context([{"id": "C1", "text": "a"}, {"id": "C1", "text": "b"}])

    def test_top_k_preserves_actual_score_order(self):
        ranked = [{"id": "C2", "distance": .2}, {"id": "C1", "distance": .1}]
        self.assertEqual([x["id"] for x in primitives.select_top_k(ranked, 1, "distance")], ["C1"])


class AssetFactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets/arm/mesh.obj").parent.mkdir(parents=True)
        (self.root / "assets/arm/mesh.obj").write_text("mesh")
        self.registry = self.root / "registry.json"
        self.registry.write_text(json.dumps({"assets": [{"id": "arm", "tool": "blender",
            "kind": "raw_mesh_set", "source": "assets/arm", "version": 1,
            "assumptions": "units m", "semantic_role": "arm", "provenance": "test",
            "license": "Apache-2.0"}]}))
        self.factory = assets.AssetFactory(self.root, self.registry, self.root / "cache")

    def tearDown(self):
        self.temp.cleanup()

    def test_local_resolution_validation_and_cache_reuse(self):
        resolved = self.factory.resolve_asset("arm")
        self.assertTrue(resolved.is_dir())
        self.assertEqual(self.factory.validate_asset("arm")["file_count"], 1)
        calls = []
        def converter(source, staging, metadata):
            calls.append(1)
            result = staging / "arm.glb"
            result.write_text("converted")
            return result
        first = self.factory.convert_asset("arm", "glb", converter)
        second = self.factory.convert_asset("arm", "glb", converter)
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)
        self.assertTrue(self.factory.invalidate_asset_cache("arm"))
        self.assertIsNone(self.factory.get_cached_asset("arm", "glb"))

    def test_blocks_source_escape_and_converter_escape(self):
        data = json.loads(self.registry.read_text())
        data["assets"][0]["source"] = "../outside"
        self.registry.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.factory.resolve_asset("arm")
        data["assets"][0]["source"] = "assets/arm"
        self.registry.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.factory.convert_asset("arm", "glb", lambda *_: self.root / "outside.glb")

    def test_register_rejects_duplicate_id(self):
        with self.assertRaises(ValueError):
            self.factory.register_asset(json.loads(self.registry.read_text())["assets"][0])


if __name__ == "__main__":
    unittest.main()
