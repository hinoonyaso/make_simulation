import importlib.util
import hashlib
import json
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py"
spec = importlib.util.spec_from_file_location("visual_manifest_validator", VALIDATOR_PATH)
manifest_validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest_validator)
producer_spec = importlib.util.spec_from_file_location("produce_ai_video", ROOT / "scripts/produce_ai_video.py")
producer = importlib.util.module_from_spec(producer_spec)
producer_spec.loader.exec_module(producer)


class DirectorTraceRoutingTests(unittest.TestCase):
    def test_director_has_explicit_ai_and_robotics_routes(self):
        agent = (ROOT / ".codex/agents/director.toml").read_text(encoding="utf-8")
        routing = (ROOT / "ROUTING.md").read_text(encoding="utf-8")
        self.assertIn("ai-mechanism-trace/v1", agent)
        self.assertIn("Do not route AI computation to a generic slide deck", agent)
        self.assertIn("physical robotics lessons", agent)
        self.assertIn("must not fall back to a generic presentation/slide route", routing)

    def _manifest_with_trace(self, source_trace, evidence):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        shutil.copy(source_trace, root / "trace.json")
        manifest = {
            "language": "ko-KR",
            "beats": [{"id": "B01", "text": "검증된 trace를 재생합니다.", "sec": 5,
                       "object": "trace", "state_change": "loaded -> rendered",
                       "focus": "recorded values", "tool": "M", "evidence": evidence,
                       "trace": "trace.json"}],
        }
        path = root / "visual_manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return temp, path

    def test_ai_model_execution_trace_uses_ai_validator(self):
        temp, path = self._manifest_with_trace(
            ROOT / "pilots/v10_rag_poc/data/ai_trace.json", "model_execution")
        self.addCleanup(temp.cleanup)
        errors, _ = manifest_validator.validate(str(path))
        self.assertEqual(errors, [])

    def test_v9_robotics_trace_still_uses_robotics_validator(self):
        temp, path = self._manifest_with_trace(
            ROOT / "core/shared-data/trace_example.json", "trace_playback")
        self.addCleanup(temp.cleanup)
        errors, _ = manifest_validator.validate(str(path))
        self.assertEqual(errors, [])

    def test_threejs_projection_preserves_trace_ids_and_actual_scores(self):
        trace_path = ROOT / "pilots/v10_rag_poc/data/ai_trace.json"
        projection_path = ROOT / "pilots/v10_threejs_rag/data/embedding_space_3d.json"
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        projection = json.loads(projection_path.read_text(encoding="utf-8"))
        self.assertEqual(projection["source_trace_sha256"],
                         hashlib.sha256(trace_path.read_bytes()).hexdigest())
        self.assertEqual(projection["trace_id"], trace["trace_id"])
        self.assertEqual(projection["query_id"], "query:Q0")
        expected = sorted((item for item in trace["intermediate_values"]
                           if item["kind"] == "squared_l2_distance"),
                          key=lambda item: item["rank"])
        self.assertEqual(projection["retrieval"]["ranking"], [
            {"id": item["source_id"], "rank": item["rank"],
             "score": item["value"]} for item in expected])
        self.assertEqual(projection["retrieval"]["top_k_ids"],
                         trace["outputs"][0]["retrieved_ids"])

    def test_production_cli_routes_rag_to_validated_manim_pipeline(self):
        def fake_render(command, **_kwargs):
            output_dir = Path(command[command.index("--output-dir") + 1])
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "renderer_selection.json").write_text(json.dumps({
                "selected": "manim", "reason": "mock renderer selection"}), encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp, \
             patch.object(sys, "argv", ["produce_ai_video.py", "--topic", "rag",
                 "--trace", str(ROOT / "pilots/v10_rag_poc/data/ai_trace.json"),
                 "--render", "manim", "--preview-only", "--silent",
                 "--output-root", temp]), \
             patch.object(producer.subprocess, "run", side_effect=fake_render) as run:
            producer.main()
            command = run.call_args.args[0]
            self.assertEqual(command[2], "preview")
            self.assertIn("build_video.py", command[1])
            self.assertIn("--trace", command)
            self.assertIn("--manifest", command)
            self.assertIn("--silent", command)
            report = next(Path(temp).glob("rag-*/production_report.json"))
            self.assertEqual(json.loads(report.read_text())["preview"]["status"], "PASS")

    def test_production_cli_rejects_unimplemented_ai_topics(self):
        with patch.object(sys, "argv", ["produce_ai_video.py", "--topic", "attention"]):
            with self.assertRaisesRegex(SystemExit, "implemented topics: rag"):
                producer.main()


if __name__ == "__main__":
    unittest.main()
