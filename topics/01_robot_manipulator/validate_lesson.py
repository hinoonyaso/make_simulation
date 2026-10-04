"""Check mathematical correctness and final media/timing contracts."""
import json
import subprocess
import wave
from pathlib import Path
import numpy as np
from manipulator_video import fk, ik, jacobian, L1, L2

ROOT = Path(__file__).resolve().parent


def main():
    rng = np.random.default_rng(42)
    errors = []
    derivative_errors = []
    for a, b in rng.uniform(-np.pi, np.pi, (200, 2)):
        p = fk(a, b)
        for branch in [-1, 1]:
            errors.append(float(np.linalg.norm(fk(*ik(*p, branch=branch))-p)))
        eps = 1e-6
        finite = np.column_stack(((fk(a+eps,b)-fk(a-eps,b))/(2*eps),
                                  (fk(a,b+eps)-fk(a,b-eps))/(2*eps)))
        derivative_errors.append(float(np.max(np.abs(jacobian(a,b)-finite))))
        assert np.isclose(np.linalg.det(jacobian(a,b)), L1*L2*np.sin(b))
    assert max(errors) < 1e-9
    assert max(derivative_errors) < 1e-8
    assert np.allclose(fk(0,np.pi/2),[1,.8])
    for xy in [(1.9,0),(.1,0)]:
        try:
            ik(*xy)
            raise AssertionError("Unreachable target was accepted")
        except ValueError:
            pass
    records = json.loads((ROOT / "assets/audio/manifest.json").read_text())
    timeline_file = ROOT / "output/render_timeline.json"
    report = {"fk_ik_max_error_m":max(errors), "jacobian_max_error":max(derivative_errors),
              "narration_seconds":records[-1]["end"], "utterances":len(records)}
    rms_levels = []
    for rec in records:
        with wave.open(str(ROOT / rec["audio"]), "rb") as wav:
            assert wav.getnchannels() == 1 and wav.getsampwidth() == 2
            assert abs(wav.getnframes()/wav.getframerate()-rec["duration"]) < 1/48000
            samples = np.frombuffer(wav.readframes(wav.getnframes()),dtype=np.int16).astype(float)/32768
        rms = 20*np.log10(np.sqrt(np.mean(samples*samples))+1e-12)
        assert rms > -45, f"Unexpectedly quiet narration: {rec['audio']}"
        assert np.max(np.abs(samples)) < 1
        rms_levels.append(rms)
    report["narration_rms_dbfs_range"] = [float(min(rms_levels)),float(max(rms_levels))]
    if timeline_file.exists():
        rendered = json.loads(timeline_file.read_text())
        assert len(rendered) == len(records)
        drift = max(abs(a["start"]-b["start"]) for a,b in zip(rendered,records))
        assert drift < 1/30 + 1e-6, f"Timeline drift: {drift}"
        report["max_sync_drift_seconds"] = drift
    cue_file = ROOT / "output/caption_timing.json"
    if cue_file.exists():
        cues = json.loads(cue_file.read_text())
        for c,r in zip(cues,records):
            assert r["start"] <= c["start"] < c["end"] <= r["end"]
        assert len(cues) == len(records)
        report["whisper_timed_captions"] = sum(c["timing_source"] == "whisper" for c in cues)
    movie = ROOT / "output/robot_manipulator_education_ko.mp4"
    if movie.exists():
        info = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(movie)]))
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        assert (video["width"],video["height"],video["r_frame_rate"]) == (1920,1080,"30/1")
        assert video["codec_name"] == "h264" and audio["codec_name"] == "aac"
        assert abs(float(info["format"]["duration"])-records[-1]["end"]) < .1
        report["video"] = {"resolution":"1920x1080","fps":30,"codec":"H.264/AAC","duration":info["format"]["duration"]}
    (ROOT / "output/validation.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
