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
visual_data = load("rag_visual_data", ROOT / "core/ai-mechanism/rag_visual_data.py")
execute_rag = load("execute_local_rag", ROOT / "core/ai-mechanism/execute_local_rag.py")


class AITraceTests(unittest.TestCase):
    def test_checked_in_trace_validates_without_source_episode(self):
        path = ROOT / "pilots/v10_rag_poc/data/ai_trace.json"
        trace = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(trace_mod.validate_trace(trace))
        self.assertEqual(trace["schema"], "ai-mechanism-trace/v1")
        self.assertEqual(trace["outputs"][0]["retrieved_ids"], ["C08", "C11", "C07"])
        self.assertEqual(len(trace["inputs"][1]["embedding"]), 384)
        source_text = trace["inputs"][0]["text"]
        for chunk in (value for value in trace["intermediate_values"]
                      if value["kind"] == "text_chunk"):
            self.assertEqual(chunk["value"], source_text[chunk["char_start"]:chunk["char_end"]])

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


class GenericRAGExecutionTests(unittest.TestCase):
    def test_three_chunks_without_overlap_and_top_k_one(self):
        document = "로봇 바퀴 이동. 센서 거리 측정. 지도 위치 추정."
        trace = execute_rag.execute_lexical_rag(document, "바퀴 이동", chunk_size=12,
                                                overlap=0, top_k=1)
        self.assertFalse(trace_mod.validate_trace(trace))
        data = visual_data.prepare_rag_visual_data(trace)
        self.assertEqual(len(data["chunks"]), 3)
        self.assertEqual(data["overlaps"], [])
        self.assertEqual(len(data["top_ids"]), 1)
        self.assertEqual(data["metric"], "TF-IDF cosine similarity")

    def test_eleven_chunks_with_observed_overlap(self):
        document = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 6 + "ABCDEFGHIJKLMN"  # 170 characters -> 11 windows.
        trace = execute_rag.execute_lexical_rag(document, "ABC", chunk_size=20,
                                                overlap=5, top_k=3)
        data = visual_data.prepare_rag_visual_data(trace)
        self.assertEqual(len(data["chunks"]), 11)
        self.assertTrue(data["representative_overlap"])
        self.assertEqual(data["representative_overlap"]["length"], 5)

    def test_fifteen_long_chunks_with_overlap_and_top_k_five(self):
        sentence = "바퀴 회전 거리와 센서 위치를 비교합니다. "
        document = sentence * 25
        trace = execute_rag.execute_lexical_rag(document, "바퀴 회전 거리", chunk_size=48,
                                                overlap=12, top_k=5)
        data = visual_data.prepare_rag_visual_data(trace)
        self.assertGreaterEqual(len(data["chunks"]), 15)
        self.assertTrue(data["overlaps"])
        self.assertEqual(len(data["top_ids"]), 5)
        self.assertEqual(len(set(data["top_ids"])), 5)
        self.assertTrue(all(item["char_end"] - item["char_start"] <= 48
                            for item in data["chunks"]))

    def test_arbitrary_ids_and_variable_top_k_are_data_driven(self):
        trace = execute_rag.execute_lexical_rag("alpha beta gamma delta", "gamma", chunk_size=7,
                                                overlap=1, top_k=3)
        chunks = [item for item in trace["intermediate_values"] if item["kind"] == "text_chunk"]
        for index, chunk in enumerate(chunks):
            chunk["id"] = f"source-{index + 20}"
            chunk["source_id"] = "document:source"
            vector = next(item for item in trace["intermediate_values"]
                          if item["id"] == f"vector:chunk-{index+1:03d}")
            vector["id"] = f"vector:{chunk['id']}"
            vector["source_id"] = chunk["id"]
        scores = [item for item in trace["intermediate_values"] if item["kind"] == "retrieval_score"]
        for item in scores:
            original = item["source_id"]
            suffix = int(original.split("-")[-1])
            item["source_id"] = f"source-{suffix + 19}"
            item["id"] = f"score:{item['source_id']}"
        for output in trace["outputs"]:
            output["retrieved_ids"] = [item["source_id"] for item in
                                       sorted(scores, key=lambda item: item["rank"])[:3]]
        trace["retrieval"]["top_k_ids"] = trace["outputs"][0]["retrieved_ids"]
        self.assertFalse(trace_mod.validate_trace(trace))
        data = visual_data.prepare_rag_visual_data(trace)
        self.assertEqual(data["top_ids"], [f"source-{int(v['source_id'].split('-')[-1])}"
                                          for v in sorted(scores, key=lambda item: item["rank"])[:3]])


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

    def test_converter_identity_version_and_configuration_partition_cache(self):
        calls = []
        def converter(source, staging, metadata):
            calls.append(1)
            result = staging / "arm.glb"
            result.write_text("converted")
            return result
        first = self.factory.convert_asset("arm", "glb", converter, converter_id="mesh-converter",
                                           converter_version="1", converter_config={"scale": 1})
        reused = self.factory.convert_asset("arm", "glb", converter, converter_id="mesh-converter",
                                            converter_version="1", converter_config={"scale": 1})
        changed = self.factory.convert_asset("arm", "glb", converter, converter_id="mesh-converter",
                                             converter_version="2", converter_config={"scale": 2})
        self.assertEqual(first, reused)
        self.assertNotEqual(first, changed)
        self.assertEqual(len(calls), 2)

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
