"""Generate Korean narration; Whisper supplies speech boundaries for edited captions."""
import argparse
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets" / "audio"
OUT = ROOT / "output"


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ]))


async def generate():
    import edge_tts
    doc = json.loads((ROOT / "storyboard.json").read_text())
    ASSETS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(3)

    async def one(ci, li, text, caption):
        name = f"{ci:02d}_{li:02d}"
        mp3 = ASSETS / f"{name}.mp3"
        key = hashlib.sha256((text + doc["voice"] + doc["rate"]).encode()).hexdigest()
        stamp = ASSETS / f"{name}.sha256"
        async with sem:
            if not mp3.exists() or not stamp.exists() or stamp.read_text() != key:
                for attempt in range(3):
                    try:
                        await edge_tts.Communicate(text, doc["voice"], rate=doc["rate"]).save(str(mp3))
                        stamp.write_text(key)
                        break
                    except Exception:
                        if attempt == 2:
                            raise
                        await asyncio.sleep(2)
            seconds = math.ceil((duration(mp3) + 0.4) * 30) / 30
            wav = ASSETS / f"{name}.wav"
            run("ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-af", "apad",
                "-t", f"{seconds:.9f}", "-ar", "48000", "-ac", "1", str(wav))
            print(f"Audio {name}: {seconds:.2f}s", flush=True)
        return {"chapter": ci, "line": li, "text": text, "caption": caption,
                "audio": str(wav.relative_to(ROOT)), "duration": seconds}

    records = await asyncio.gather(*(one(ci, li, *line)
        for ci, ch in enumerate(doc["chapters"]) for li, line in enumerate(ch["lines"])))
    now = 0.0
    for rec in records:
        rec["start"] = now
        now += rec["duration"]
        rec["end"] = now
    (ASSETS / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
    concat = ASSETS / "concat.txt"
    concat.write_text("".join(f"file '{(ROOT / r['audio']).as_posix()}'\n" for r in records))
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:a", "pcm_s16le", str(OUT / "narration.wav"))
    print(f"Narration total: {now:.2f}s", flush=True)


def timestamp(t, separator=","):
    ms = round(t * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{separator}{ms:03d}"


def captions(model_name):
    import torch
    import whisper
    torch.set_num_threads(2)
    records = json.loads((ASSETS / "manifest.json").read_text())
    rawfile = OUT / "whisper_raw.json"
    stamp = OUT / "whisper_input.sha256"
    fingerprint = hashlib.sha256((OUT / "narration.wav").read_bytes() + model_name.encode()).hexdigest()
    if rawfile.exists() and stamp.exists() and stamp.read_text() == fingerprint:
        result = json.loads(rawfile.read_text())
    else:
        model = whisper.load_model(model_name, device="cpu")
        from whisper.audio import N_FRAMES
        from whisper.tokenizer import get_tokenizer
        from whisper.timing import find_alignment
        tokenizer = get_tokenizer(model.is_multilingual, num_languages=model.num_languages,
                                  language="ko", task="transcribe")
        # Checkpoint each utterance: interruption does not discard the whole ASR pass.
        segments = []
        for rec in records:
            wav = ROOT / rec["audio"]
            key = hashlib.sha256(wav.read_bytes() + model_name.encode()).hexdigest()
            asr_cache = wav.with_suffix(".asr.json")
            cache = wav.with_suffix(".alignment.json")
            existing = next((p for p in (asr_cache, cache) if p.exists()
                             and json.loads(p.read_text()).get("key") == key), None)
            if existing:
                chunk = json.loads(existing.read_text())["result"]
            else:
                # The exact TTS script is known. Whisper cross-attention + DTW
                # aligns it directly, avoiding needless autoregressive decoding.
                audio = whisper.load_audio(str(wav))
                mel = whisper.log_mel_spectrogram(audio, n_mels=model.dims.n_mels)
                aligned = find_alignment(model, tokenizer, tokenizer.encode(rec["text"]),
                    whisper.pad_or_trim(mel, N_FRAMES), mel.shape[-1])
                words = [{"word":w.word,"start":float(w.start),"end":float(w.end),
                          "probability":float(w.probability)} for w in aligned]
                chunk = {"text":rec["text"], "method":"Whisper forced alignment of known TTS script",
                         "segments":[{"start":0.,"end":rec["duration"],"words":words}]}
                cache.write_text(json.dumps({"key":key,"result":chunk},ensure_ascii=False))
            for seg in chunk["segments"]:
                seg["start"] += rec["start"]
                seg["end"] += rec["start"]
                for word in seg.get("words", []):
                    word["start"] += rec["start"]
                    word["end"] += rec["start"]
                segments.append(seg)
            print(f"Whisper checkpoint: {wav.name}",flush=True)
        result = {"language":"ko","segments":segments,
                  "method":"Whisper base: cached ASR + forced alignment of known narration script"}
        rawfile.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        stamp.write_text(fingerprint)
    words = [w for seg in result["segments"] for w in seg.get("words", [])]
    cues = []
    for rec in records:
        # TTS utterance windows prevent ASR text errors from shifting later captions.
        matched = [w for w in words if rec["start"] <= (w["start"] + w["end"]) / 2 < rec["end"] - 0.2]
        start = max(rec["start"] + 0.06, min((w["start"] for w in matched), default=rec["start"] + 0.1))
        end = min(rec["end"] - 0.12, max((w["end"] for w in matched), default=rec["end"] - 0.4) + 0.15)
        if end - start < 1.0:
            start, end = rec["start"] + 0.1, rec["end"] - 0.15
        cues.append({"start":start, "end":end, "caption":rec["caption"],
                     "timing_source":"whisper" if matched else "utterance_window"})
    (OUT / "caption_timing.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2))
    (OUT / "subtitles.ko.srt").write_text("\n\n".join(
        f"{i+1}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['caption']}"
        for i, c in enumerate(cues)) + "\n")
    (OUT / "subtitles.ko.vtt").write_text("WEBVTT\n\n" + "\n\n".join(
        f"{timestamp(c['start'], '.')} --> {timestamp(c['end'], '.')}\n{c['caption']}" for c in cues) + "\n")
    print(f"Edited Korean captions: {len(cues)} cues, Whisper words: {len(words)}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["tts", "captions"])
    parser.add_argument("--model", default="base")
    args = parser.parse_args()
    if args.stage == "tts":
        asyncio.run(generate())
    else:
        captions(args.model)
