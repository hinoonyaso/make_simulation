"""Render/review/finalize a 34-second vertical slice from saved real RAG execution."""
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "output"
mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
assert mode in {"preview", "final"}
size = "960,540" if mode == "preview" else "1920,1080"
quality = "-ql" if mode == "preview" else "-qh"
folder = OUT / f"{mode}_render"
folder.mkdir(parents=True, exist_ok=True)
log = OUT / f"{mode}_render.log"
with log.open("w") as stream:
    subprocess.run(["uv", "run", "manim", quality, "--fps", "30", "--resolution", size,
                    "--disable_caching", "--media_dir", str(folder),
                    str(HERE / "rag_mechanism_scene.py"), "RAGMechanismPoC"],
                   cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)

if mode in {"preview", "final"}:
    src = ROOT / "pilots/07_naive_rag/output/naive_rag_ko.mp4"
    manifest = json.loads((ROOT / "pilots/07_naive_rag/visual_manifest.json").read_text())
    cues = json.loads((ROOT / "pilots/07_naive_rag/output/caption_timing.json").read_text())
    beats = {b["id"]: b for b in manifest["beats"]}
    windows = [("B04", 9.5), ("B08", 9.5), ("B13", 9.0), ("B15", 7.5)]
    starts = {}; elapsed = 0.0
    for beat in manifest["beats"]:
        starts[beat["id"]] = elapsed
        elapsed += beat["sec"]
    # Reuse already approved voice from this exact source episode; no new TTS payload.
    audio = OUT / "narration.wav"
    filters = []
    inputs = []
    selected = []
    for i, (bid, local) in enumerate(windows):
        begin = starts[bid] + local
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(begin), "-i", str(src),
                        "-t", "8.5", "-vn", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le",
                        str(OUT / f"voice_{i}.wav")], check=True)
        inputs += ["-i", str(OUT / f"voice_{i}.wav")]
        filters.append(f"[{i}:a]")
        for cue in cues:
            if cue["end"] > begin and cue["start"] < begin + 8.5:
                selected.append({"start": max(cue["start"], begin) - begin + i*8.5,
                                 "end": min(cue["end"], begin + 8.5) - begin + i*8.5,
                                 "caption": cue["caption"]})
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
                    "".join(filters) + f"concat=n={len(windows)}:v=0:a=1[a]",
                    "-map", "[a]", "-c:a", "pcm_s16le", str(audio)], check=True)
    source_video = folder / "videos/rag_mechanism_scene/1080p30/RAGMechanismPoC.mp4"
    if mode == "preview":
        source_video = folder / "videos/rag_mechanism_scene/540p30/RAGMechanismPoC.mp4"
    srt = OUT / "subtitles.ko.srt"
    def stamp(sec):
        ms = round(sec*1000); hh, ms = divmod(ms, 3600000); mm, ms = divmod(ms, 60000); ss, ms = divmod(ms, 1000)
        return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
    srt.write_text("\n\n".join(f"{i+1}\n{stamp(c['start'])} --> {stamp(c['end'])}\n{c['caption']}"
                               for i,c in enumerate(selected)) + "\n", encoding="utf-8")
    size_name = "rag_mechanism_poc_preview.mp4" if mode == "preview" else "rag_mechanism_poc.mp4"
    target = OUT / size_name
    subtitle_size = 12 if mode == "preview" else 18
    style = f"FontName=NanumGothic,FontSize={subtitle_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00202020,BorderStyle=1,Outline=1,Shadow=0,MarginV=18"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source_video), "-i", str(audio),
                    "-filter_complex", f"[0:v]subtitles='{srt}':force_style='{style}'[v]",
                    "-map", "[v]", "-map", "1:a", "-t", "34", "-r", "30",
                    "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags",
                    "+faststart", str(target)], check=True)
    (OUT / "caption_timing.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2)+"\n")
    print(target, target.stat().st_size, "bytes")
