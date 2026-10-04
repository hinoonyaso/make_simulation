"""Check timing, streams, subtitles and the numerical example; decode the full video."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


def main():
    records = json.loads((ROOT / "assets/audio/manifest.json").read_text())
    timeline = json.loads((OUT / "render_timeline_v2.json").read_text())
    captions = json.loads((OUT / "caption_timing.json").read_text())
    assert len(records) == len(timeline) == len(captions) == 32
    drift = max(abs(a[k]-b[k]) for a,b in zip(records,timeline) for k in ("start","end"))
    assert drift < 1/30, f"Narration/animation timing drift: {drift}"
    for i,c in enumerate(captions):
        assert 0 <= c["start"] < c["end"] <= records[-1]["end"]
        assert records[i]["start"] <= c["start"] < c["end"] <= records[i]["end"]
        if i:
            assert captions[i-1]["end"] <= c["start"]
    sim = json.loads((OUT / "toy_training.json").read_text())
    losses = [f["loss"] for f in sim["frames"]]
    assert all(a >= b for a,b in zip(losses,losses[1:]))
    assert losses[-1] < losses[0]*.01
    assert 16*(4096+4096)/(4096*4096) == .0078125
    results = {}
    for name in ("qlora_education_ko_v2.mp4", "qlora_clean_ko_v2.mp4"):
        file = OUT / name
        info = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams",
            "-show_format","-show_chapters","-of","json",str(file)]))
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
        assert (video["width"],video["height"],video["r_frame_rate"],video["codec_name"]) == (1920,1080,"30/1","h264")
        assert audio["codec_name"] == "aac" and audio["sample_rate"] == "48000"
        assert abs(float(video["duration"])-records[-1]["end"]) < 1/30
        assert abs(float(video["duration"])-float(audio["duration"])) < .1
        assert len(info["chapters"]) == 9
        decode = subprocess.run(["ffmpeg","-v","error","-i",str(file),"-f","null","-"],capture_output=True,text=True)
        assert decode.returncode == 0 and not decode.stderr, decode.stderr
        results[name] = info
    results["checks"] = dict(narration_drift_seconds=drift, subtitle_cues=len(captions),
        whisper_timed_cues=sum(c["timing_source"] == "whisper" for c in captions),
        initial_loss=losses[0], final_loss=losses[-1], full_decode="passed")
    (OUT / "validation_v2.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
    print(json.dumps(results["checks"],indent=2))


if __name__ == "__main__":
    main()
