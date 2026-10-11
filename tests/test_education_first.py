from __future__ import annotations

import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.education.blueprint_registry import available_blueprints, get_blueprint
from core.education.education_planner import plan_lesson
from core.education.evidence_router import route_evidence
from core.education.lesson_spec import LessonSpec, validate_lesson_spec
from core.education.lesson_validator import validate_manifest
from core.mechanism.timeline import validate_timeline

ROOT = Path(__file__).resolve().parents[1]


class EducationFirstTests(unittest.TestCase):
    def load(self, name):
        return json.loads((ROOT / "examples/education" / name).read_text(encoding="utf-8"))

    def test_bearing_concept_spec_and_manifest(self):
        spec = self.load("bearing.json")
        json_schema = json.loads((ROOT / "core/education/lesson_spec.schema.json").read_text(encoding="utf-8"))
        self.assertIn("beats", json_schema["required"])
        self.assertEqual(json_schema["properties"]["schema"]["const"], "education-lesson-spec/v1")
        self.assertEqual(validate_lesson_spec(spec), [])
        self.assertEqual(LessonSpec.from_dict(spec).topic, "ball_bearing")
        planned = plan_lesson(spec)
        self.assertEqual(validate_manifest(planned["visual_manifest"]), [])
        self.assertEqual(planned["evidence"]["status"], "CONCEPT_ONLY")
        self.assertFalse(planned["evidence"]["execution_required"])
        self.assertEqual(validate_timeline(planned["timeline"],
                         expected_phase_ids=[b["phase_id"] for b in spec["beats"]]), [])
        self.assertEqual(sum(b["sec"] for b in spec["beats"]), spec["duration_target_sec"])

    def test_invalid_spec_and_manifest_are_rejected(self):
        self.assertTrue(validate_lesson_spec({"topic": "x"}))
        spec = self.load("education_smoke.json")
        spec["beats"][0]["tool"] = "X"
        with self.assertRaisesRegex(ValueError, "visual manifest"):
            plan_lesson(spec)

    def test_blueprint_registry_is_deterministic(self):
        self.assertEqual(set(available_blueprints()), {"exploded_assembly", "layered_structure", "signal_timing",
                         "coordinate_transform", "process_flow", "before_after"})
        self.assertIn("blender", get_blueprint("exploded_assembly")["renderers"])
        with self.assertRaises(ValueError):
            get_blueprint("unknown")

    def test_computed_mode_requires_solver(self):
        spec = self.load("bearing.json")
        spec["modes"] = ["computed_engineering_demonstration"]
        with self.assertRaisesRegex(ValueError, "requires a named solver"):
            route_evidence(spec, spec["beats"])

    def test_named_solver_is_not_reported_as_executed_without_adapter(self):
        spec = self.load("bearing.json")
        spec["modes"] = ["computed_engineering_demonstration"]
        spec["solver"] = "CalculiX"
        spec["trace"] = "future_trace.json"
        result = route_evidence(spec, spec["beats"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["execution_required"])

    def test_concept_smoke_plan_is_solver_free(self):
        planned = plan_lesson(self.load("education_smoke.json"))
        self.assertEqual(planned["evidence"]["status"], "CONCEPT_ONLY")
        self.assertEqual(len(planned["timeline"]["phases"]), 2)

    def test_caption_writer_splits_korean_sentences(self):
        from scripts.produce_lesson import write_captions
        spec = self.load("education_smoke.json")
        spec["beats"][0]["caption"] = "첫 문장입니다. 둘째 문장입니다."
        spec["beats"][1]["caption"] = ""
        with TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = plan_lesson(spec)["visual_manifest"]
            timeline = plan_lesson(spec)["timeline"]
            cues = write_captions(manifest, output, timeline)
            vtt = (output / "subtitles.ko.vtt").read_text(encoding="utf-8")
            srt = (output / "subtitles.ko.srt").read_text(encoding="utf-8")
            saved = json.loads((output / "caption_timing.json").read_text(encoding="utf-8"))
        self.assertIn("첫 문장입니다.", vtt)
        self.assertIn("둘째 문장입니다.", vtt)
        self.assertEqual(vtt.count(" --> "), 2)
        self.assertIn("첫 문장입니다.", srt)
        self.assertEqual(cues, saved)

    def test_burn_in_uses_the_saved_caption_cues(self):
        from scripts.produce_lesson import burn_captions
        cue = {"start": 1.234, "end": 2.345, "caption": "정렬된 자막 문장입니다."}
        with TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "input.mp4"
            video.touch()
            with patch("scripts.produce_lesson.subprocess.check_output",
                       return_value='{"streams":[{"width":1920,"height":1080}]}'), \
                 patch("scripts.produce_lesson.subprocess.run") as run:
                burn_captions(video, [cue], root / "burned.mp4")
            ass = (root / "subtitles.ko.ass").read_text(encoding="utf-8-sig")
        self.assertIn("PlayResX: 1920", ass)
        self.assertIn("Dialogue: 0,0:00:01.23,0:00:02.35,Default", ass)
        self.assertIn("정렬된 자막 문장입니다.", ass)
        self.assertTrue(run.called)

    def test_narration_mux_does_not_truncate_with_shortest(self):
        from scripts.produce_lesson import mux_narration
        with patch("scripts.produce_lesson.subprocess.run") as run:
            mux_narration(Path("silent.mp4"), Path("narration.wav"), Path("final.mp4"))
        command = run.call_args.args[0]
        self.assertIn("-c:a", command)
        self.assertNotIn("-shortest", command)

    def test_plan_only_never_invokes_tts_subprocess(self):
        from scripts.produce_lesson import main
        with TemporaryDirectory() as directory:
            with patch.object(sys, "argv", ["produce_lesson.py", "--spec",
                    str(ROOT / "examples/education/education_smoke.json"), "--plan-only",
                    "--output-root", directory, "--run-id", "silent-plan"]), \
                 patch("scripts.produce_lesson.subprocess.run") as run, redirect_stdout(StringIO()):
                self.assertEqual(main(), 0)
            self.assertFalse(run.called)
            report = json.loads((Path(directory) / "silent-plan/production_report.json").read_text())
        self.assertEqual(report["status"], "PLAN_VALIDATED")
        self.assertEqual(report["audio_status"], "NOT_REQUESTED")

    def test_plan_only_with_tts_errors_before_side_effects(self):
        from scripts.produce_lesson import main
        with TemporaryDirectory() as directory:
            stderr = StringIO()
            with patch.object(sys, "argv", ["produce_lesson.py", "--spec",
                    str(ROOT / "examples/education/education_smoke.json"), "--plan-only", "--with-tts",
                    "--output-root", directory]), \
                 patch("scripts.produce_lesson.subprocess.run") as run, redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as error:
                    main()
            self.assertEqual(error.exception.code, 2)
            self.assertIn("--plan-only cannot be combined with --with-tts", stderr.getvalue())
            self.assertFalse(run.called)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_delivery_resolution_for_all_render_and_audio_modes(self):
        from scripts.produce_lesson import main
        for preview in (True, False):
            for with_tts in (True, False):
                with self.subTest(preview=preview, with_tts=with_tts), TemporaryDirectory() as directory:
                    output_root = Path(directory)
                    run_id = f"case-{int(preview)}-{int(with_tts)}"
                    args = ["produce_lesson.py", "--spec", str(ROOT / "examples/education/education_smoke.json"),
                            "--output-root", str(output_root), "--run-id", run_id]
                    if preview:
                        args.append("--preview")
                    if with_tts:
                        args.append("--with-tts")

                    def fake_run(command, **kwargs):
                        if not any("prepare_audio.py" in str(part) for part in command):
                            return SimpleNamespace(returncode=0)
                        mode = command[-2]
                        manifest_path = Path(command[-1])
                        audio_output = manifest_path.parent / "output"
                        audio_output.mkdir(exist_ok=True)
                        if mode == "tts":
                            (audio_output / "narration.wav").write_bytes(b"mock")
                            audio_manifest = manifest_path.parent / "assets/audio/manifest.json"
                            audio_manifest.parent.mkdir(parents=True, exist_ok=True)
                            audio_manifest.write_text("[]", encoding="utf-8")
                        else:
                            cues = [{"start": 0, "end": 1, "caption": "mock caption"}]
                            (audio_output / "caption_timing.json").write_text(json.dumps(cues), encoding="utf-8")
                            (audio_output / "subtitles.ko.vtt").write_text("WEBVTT\n", encoding="utf-8")
                            (audio_output / "subtitles.ko.srt").write_text("", encoding="utf-8")
                        return SimpleNamespace(returncode=0)

                    def fake_render(_manifest, _timeline, run_dir, mode, **_kwargs):
                        video = run_dir / ("preview.mp4" if mode == "preview" else "silent_final.mp4")
                        video.write_bytes(b"mock-video")
                        return video, {"blender_render_sec": 0, "manim_render_sec": 0}

                    def fake_mux(_video, _narration, output):
                        output.write_bytes(b"mock-final-video")

                    probe = {"streams": [{"codec_type": "video", "codec_name": "h264", "width": 960 if preview else 1920,
                                "height": 540 if preview else 1080, "r_frame_rate": "30/1", "nb_frames": "30"}],
                             "format": {"duration": "1.0"}}
                    if with_tts:
                        probe["streams"].append({"codec_type": "audio", "codec_name": "aac"})
                    with patch.object(sys, "argv", args), \
                         patch("scripts.produce_lesson.subprocess.run", side_effect=fake_run) as run, \
                         patch("scripts.produce_lesson.render", side_effect=fake_render), \
                         patch("scripts.produce_lesson.mux_narration", side_effect=fake_mux), \
                         patch("scripts.produce_lesson.subprocess.check_output", return_value=json.dumps(probe)), \
                         redirect_stdout(StringIO()):
                        self.assertEqual(main(), 0)

                    expected = ["--min-width", "960" if preview else "1920",
                                "--min-height", "540" if preview else "1080"]
                    delivery_calls = [call.args[0] for call in run.call_args_list
                                      if any("validate_delivery.py" in str(part) for part in call.args[0])]
                    self.assertEqual(len(delivery_calls), 2 if with_tts else 1)
                    for command in delivery_calls:
                        indices = [command.index("--min-width"), command.index("--min-height")]
                        actual = [command[indices[0]], command[indices[0] + 1],
                                  command[indices[1]], command[indices[1] + 1]]
                        self.assertEqual(actual, expected)
                    production = json.loads((output_root / run_id / "production_report.json").read_text())
                    expected_audio_status = "PASS" if with_tts else "NOT_REQUESTED"
                    self.assertEqual(production["audio_status"], expected_audio_status)

    def test_audio_and_engineering_qa_states_are_explicit_and_consistent(self):
        from scripts.produce_lesson import write_qa_reports
        states = ("NOT_REQUESTED", "BLOCKED", "PASS", "FAIL")
        for status in states:
            with self.subTest(status=status), TemporaryDirectory() as directory:
                root = Path(directory)
                video = root / "preview.mp4"
                video.touch()
                streams = [{"codec_type": "video", "codec_name": "h264", "width": 960,
                            "height": 540, "r_frame_rate": "30/1", "nb_frames": "30"}]
                if status == "PASS":
                    streams.append({"codec_type": "audio", "codec_name": "aac"})
                probe = {"streams": streams, "format": {"duration": "1.0"}}
                production = {"status": "SILENT_PREVIEW", "audio_status": "PENDING"}
                with patch("scripts.produce_lesson.subprocess.check_output", return_value=json.dumps(probe)):
                    result = write_qa_reports(root, video, [{"caption": "문장"}], audio_status=status,
                        production_report=production, manifest_validated=True, timeline_validated=True,
                        evidence_types=["conceptual_illustration"])
                audio_qa = json.loads((root / "audio_qa.json").read_text())
                qa = json.loads((root / "qa_report.json").read_text())
                production_file = json.loads((root / "production_report.json").read_text())
                markdown = (root / "qa_report.md").read_text()
                self.assertEqual(audio_qa["status"], status)
                self.assertEqual(qa["audio"]["status"], status)
                self.assertEqual(production["audio_status"], status)
                self.assertEqual(production_file["audio_status"], status)
                self.assertIn(f"- Audio: {status}", markdown)
                self.assertEqual(result["audio_qa"]["status"], status)
                engineering = qa["engineering"]
                self.assertEqual(engineering["status"], "REVIEW_REQUIRED")
                self.assertEqual(engineering["manifest_contract"]["status"], "PASS")
                self.assertEqual(engineering["video_timeline"]["status"], "PASS")
                self.assertEqual(engineering["evidence"]["type"], "CONCEPTUAL_ILLUSTRATION")
                self.assertEqual(engineering["evidence"]["calculation_status"], "NOT_COMPUTED")
                self.assertEqual(engineering["human_accuracy_review"]["status"], "PENDING")
                self.assertIn("no contact force, friction, stress, or deformation calculation", markdown)

    def test_requested_audio_failure_writes_consistent_fail_reports(self):
        from scripts.produce_lesson import write_audio_failure_reports
        with TemporaryDirectory() as directory:
            root = Path(directory)
            report = {"status": "RUNNING", "audio_status": "NOT_REQUESTED"}
            write_audio_failure_reports(root, report, RuntimeError("mock validator failure"))
            audio = json.loads((root / "audio_qa.json").read_text())
            qa = json.loads((root / "qa_report.json").read_text())
            production = json.loads((root / "production_report.json").read_text())
            self.assertEqual(report["audio_status"], "FAIL")
            self.assertEqual(audio["status"], "FAIL")
            self.assertEqual(qa["audio"]["status"], "FAIL")
            self.assertEqual(production["audio_status"], "FAIL")
            self.assertIn("- Audio: FAIL", (root / "qa_report.md").read_text())

    def test_tts_generation_uses_mock_service_and_measured_durations(self):
        from core.narration import prepare_audio
        saved = []

        class FakeCommunicate:
            def __init__(self, text, voice, rate):
                saved.append((text, voice, rate))

            async def save(self, path):
                Path(path).write_bytes(b"mock-audio")

        fake_edge_tts = SimpleNamespace(Communicate=FakeCommunicate)
        with TemporaryDirectory() as directory:
            manifest = Path(directory) / "visual_manifest.json"
            manifest.write_text(json.dumps({"voice": "ko-test", "rate": "+0%", "language": "ko-KR",
                "beats": [{"id": "B1", "text": "베어링 설명입니다.", "caption": "베어링 설명입니다.",
                           "sec": 1, "min_sec": 1}]}), encoding="utf-8")
            with patch.dict(sys.modules, {"edge_tts": fake_edge_tts}), \
                 patch.object(prepare_audio, "duration", return_value=.2), \
                 patch.object(prepare_audio, "run"):
                import asyncio
                asyncio.run(prepare_audio.generate(manifest, 30))
            records = json.loads((Path(directory) / "assets/audio/manifest.json").read_text())
            updated = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(saved, [("베어링 설명입니다.", "ko-test", "+0%")])
        self.assertEqual(records[0]["duration"], 1.0)  # min_sec remains the visual floor
        self.assertEqual(updated["beats"][0]["audio"], "assets/audio/B1.wav")

    def test_final_delivery_validator_checks_muxed_audio_and_sync(self):
        from scripts import validate_delivery
        with TemporaryDirectory() as directory:
            root = Path(directory)
            media, audio_manifest, captions = root / "final.mp4", root / "audio.json", root / "cues.json"
            media.touch()
            audio_manifest.write_text(json.dumps([{"beat": "B1", "start": 0, "end": 1}]))
            captions.write_text(json.dumps([{"start": .1, "end": .9, "caption": "문장"}]))
            probe = {"streams": [{"codec_type": "video", "width": 1920, "height": 1080,
                        "r_frame_rate": "30/1", "duration": "1.0"},
                     {"codec_type": "audio", "codec_name": "aac", "duration": "1.0"}],
                     "format": {"duration": "1.0"}}
            args = ["validate_delivery.py", str(media), "--require-audio", "--fps", "30",
                    "--audio-manifest", str(audio_manifest), "--caption-timing", str(captions), "--full-decode"]
            with patch.object(sys, "argv", args), patch.object(validate_delivery, "ffprobe", return_value=probe), \
                 patch("scripts.validate_delivery.subprocess.run") as decode, redirect_stdout(StringIO()):
                self.assertEqual(validate_delivery.main(), None)
        self.assertTrue(decode.called)

    def test_final_delivery_validator_rejects_truncated_audio(self):
        from scripts import validate_delivery
        with TemporaryDirectory() as directory:
            root = Path(directory)
            media, audio_manifest = root / "final.mp4", root / "audio.json"
            media.touch()
            audio_manifest.write_text(json.dumps([{"beat": "B1", "start": 0, "end": 1}]))
            probe = {"streams": [{"codec_type": "video", "width": 1920, "height": 1080,
                        "r_frame_rate": "30/1", "duration": "1.0"},
                     {"codec_type": "audio", "codec_name": "aac", "duration": "0.8"}],
                     "format": {"duration": "1.0"}}
            args = ["validate_delivery.py", str(media), "--require-audio", "--audio-manifest",
                    str(audio_manifest)]
            with patch.object(sys, "argv", args), patch.object(validate_delivery, "ffprobe", return_value=probe), \
                 redirect_stdout(StringIO()):
                with self.assertRaisesRegex(SystemExit, "audio duration 0.800s"):
                    validate_delivery.main()

    def test_final_delivery_validator_rejects_missing_audio(self):
        from scripts import validate_delivery
        with TemporaryDirectory() as directory:
            media = Path(directory) / "silent.mp4"
            media.touch()
            probe = {"streams": [{"codec_type": "video", "width": 1920, "height": 1080,
                        "r_frame_rate": "30/1"}], "format": {"duration": "1.0"}}
            with patch.object(sys, "argv", ["validate_delivery.py", str(media), "--require-audio"]), \
                 patch.object(validate_delivery, "ffprobe", return_value=probe), redirect_stdout(StringIO()):
                with self.assertRaisesRegex(SystemExit, "audio stream required"):
                    validate_delivery.main()


if __name__ == "__main__":
    unittest.main()
