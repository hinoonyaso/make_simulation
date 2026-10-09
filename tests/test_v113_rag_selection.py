from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.produce_video import _run_rag


class RAGMediaSelectionTests(unittest.TestCase):
    def _case(self, preview: bool, *, final_status="PASS"):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        run_dir = root / "run"
        run_dir.mkdir()
        trace = root / "trace.json"
        trace.write_text("{}", encoding="utf-8")
        renderer_root = run_dir / "rag_render"
        nested = renderer_root / "rag-one"
        nested.mkdir(parents=True)
        preview_media = nested / "rag_video_preview.mp4"
        final_media = nested / "rag_video.mp4"
        preview_media.write_bytes(b"preview")
        final_media.write_bytes(b"final")
        report_path = nested / "production_report.json"

        def produce(command, **kwargs):
            report_path.write_text(json.dumps({
                "preview": {"status": "PASS", "media": str(preview_media)},
                "final": {"status": final_status, "media": str(final_media) if final_status == "PASS" else None},
            }), encoding="utf-8")

        return temp, trace, run_dir, preview_media, final_media, produce

    def test_preview_uses_preview_report_media_and_checks_540p30(self):
        temp, trace, run_dir, preview_media, _, produce = self._case(True)
        with temp, patch("scripts.produce_video.subprocess.run", side_effect=produce), \
             patch("scripts.produce_video.media_metadata", return_value={"width": 960, "height": 540}):
            actual = _run_rag(trace, run_dir, preview=True, render="manim")
            self.assertEqual(actual.read_bytes(), preview_media.read_bytes())
            self.assertEqual(actual.name, "preview.mp4")

    def test_final_uses_final_report_media_and_checks_1080p30(self):
        temp, trace, run_dir, _, final_media, produce = self._case(False)
        with temp, patch("scripts.produce_video.subprocess.run", side_effect=produce), \
             patch("scripts.produce_video.media_metadata", return_value={"width": 1920, "height": 1080}):
            actual = _run_rag(trace, run_dir, preview=False, render="manim")
            self.assertEqual(actual.read_bytes(), final_media.read_bytes())
            self.assertEqual(actual.name, "final.mp4")

    def test_final_fails_when_subreport_only_has_preview(self):
        temp, trace, run_dir, _, _, produce = self._case(False, final_status="NOT_RUN")
        with temp, patch("scripts.produce_video.subprocess.run", side_effect=produce):
            with self.assertRaisesRegex(RuntimeError, "RAG final render did not pass"):
                _run_rag(trace, run_dir, preview=False, render="manim")
            self.assertFalse((run_dir / "final.mp4").exists())

    def test_filename_does_not_allow_wrong_resolution(self):
        temp, trace, run_dir, _, _, produce = self._case(False)
        with temp, patch("scripts.produce_video.subprocess.run", side_effect=produce), \
             patch("scripts.produce_video.media_metadata", return_value={"width": 960, "height": 540}):
            with self.assertRaisesRegex(RuntimeError, "expected 1920x1080"):
                _run_rag(trace, run_dir, preview=False, render="manim")
            self.assertFalse((run_dir / "final.mp4").exists())


if __name__ == "__main__":
    unittest.main()
