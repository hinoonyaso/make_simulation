"""Shared narration stage: TTS -> measured durations -> Whisper-aligned captions.

Promoted from the identical per-topic copies (topics/02..09/prepare_audio.py).
Input is either a topic storyboard.json (chapters[].lines[] = [text, caption]) or a
Director visual_manifest.json (beats[]). For a visual manifest, `tts` writes the measured
audio length back into beats[].sec and beats[].audio: recorded audio is authoritative.
An optional beats[].min_sec pads the utterance with trailing silence when the visual needs longer.

    uv run python core/narration/prepare_audio.py tts      topics/<topic>/storyboard.json
    uv run python core/narration/prepare_audio.py captions topics/<topic>/storyboard.json
"""
import argparse
import asyncio
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path)
    ]))


def utterances(doc):
    """Yield (file stem, record identity fields, text, caption) in narration order."""
    if "beats" in doc:
        for beat in doc["beats"]:
            yield beat["id"], {"beat": beat["id"]}, beat["text"], beat.get("caption") or beat["text"], beat.get("min_sec")
    else:
        for ci, ch in enumerate(doc["chapters"]):
            for li, (text, caption) in enumerate(ch["lines"]):
                yield f"{ci:02d}_{li:02d}", {"chapter": ci, "line": li}, text, caption, None


async def generate(doc_path, fps):
    import edge_tts
    root = doc_path.parent
    assets, out = root / "assets" / "audio", root / "output"
    doc = json.loads(doc_path.read_text())
    assets.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(3)

    async def one(name, ident, text, caption, min_sec):
        mp3 = assets / f"{name}.mp3"
        key = hashlib.sha256((text + doc["voice"] + doc["rate"]).encode()).hexdigest()
        stamp = assets / f"{name}.sha256"
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
            # 0.4s tail, rounded up to a whole video frame so cuts land on frame boundaries.
            seconds = math.ceil((duration(mp3) + 0.4) * fps) / fps
            if min_sec:  # the visual needs more time than the line: pad with silence
                seconds = max(seconds, math.ceil(float(min_sec) * fps) / fps)
            wav = assets / f"{name}.wav"
            run("ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-af", "apad",
                "-t", f"{seconds:.9f}", "-ar", "48000", "-ac", "1", str(wav))
            print(f"Audio {name}: {seconds:.2f}s", flush=True)
        return {**ident, "text": text, "caption": caption,
                "audio": str(wav.relative_to(root)), "duration": seconds}

    records = await asyncio.gather(*(one(*u) for u in utterances(doc)))
    now = 0.0
    for rec in records:
        rec["start"] = now
        now += rec["duration"]
        rec["end"] = now
    (assets / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
    concat = assets / "concat.txt"
    concat.write_text("".join(f"file '{(root / r['audio']).as_posix()}'\n" for r in records))
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:a", "pcm_s16le", str(out / "narration.wav"))
    print(f"Narration total: {now:.2f}s", flush=True)
    if "beats" in doc:
        sync_manifest(doc_path, doc, records)


def sync_manifest(doc_path, doc, records):
    by_id = {r["beat"]: r for r in records}
    for beat in doc["beats"]:
        rec = by_id[beat["id"]]
        planned = float(beat.get("sec") or 0)
        if planned and abs(rec["duration"] - planned) / planned > 0.15:
            print(f"Timing {beat['id']}: planned {planned:.2f}s -> measured {rec['duration']:.2f}s", flush=True)
        beat["sec"] = rec["duration"]
        beat["audio"] = rec["audio"]
    doc_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    print(f"Synced sec/audio into {doc_path.name}", flush=True)


SENTENCE = re.compile(r"(?<=[.?!])\s+")


def split_sentences(rec, matched, start, end):
    """One cue per sentence when a caption holds several; boundaries follow Whisper word times."""
    source = "whisper" if matched else "utterance_window"
    captions = [c for c in SENTENCE.split(rec["caption"].strip()) if c]
    spoken = [t for t in SENTENCE.split(rec["text"].strip()) if t]
    if len(captions) < 2 or not matched:
        return [{"start": start, "end": end, "caption": rec["caption"], "timing_source": source}]
    # Spoken sentences index the aligned words; fall back to caption lengths if counts differ.
    weights = [len(t) for t in (spoken if len(spoken) == len(captions) else captions)]
    lengths = [len(w["word"].strip()) or 1 for w in matched]
    total, acc, k, bounds = sum(lengths), 0, 0, []
    target = sum(weights[:1]) / sum(weights) * total
    for w, n in zip(matched, lengths):
        acc += n
        if k < len(captions) - 1 and acc >= target:
            bounds.append(w["end"] + 0.05)
            k += 1
            target = sum(weights[:k + 1]) / sum(weights) * total
    edges = [start] + bounds + [end]
    return [{"start": a, "end": b, "caption": c, "timing_source": source}
            for a, b, c in zip(edges, edges[1:], captions)]


def timestamp(t, separator=","):
    ms = round(t * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{separator}{ms:03d}"


def captions(doc_path, model_name):
    import torch
    import whisper
    torch.set_num_threads(2)
    root = doc_path.parent
    assets, out = root / "assets" / "audio", root / "output"
    language = json.loads(doc_path.read_text()).get("language", "ko").split("-")[0]
    records = json.loads((assets / "manifest.json").read_text())
    rawfile = out / "whisper_raw.json"
    stamp = out / "whisper_input.sha256"
    fingerprint = hashlib.sha256((out / "narration.wav").read_bytes() + model_name.encode()).hexdigest()
    if rawfile.exists() and stamp.exists() and stamp.read_text() == fingerprint:
        result = json.loads(rawfile.read_text())
    else:
        model = whisper.load_model(model_name, device="cpu")
        from whisper.audio import N_FRAMES
        from whisper.tokenizer import get_tokenizer
        from whisper.timing import find_alignment
        tokenizer = get_tokenizer(model.is_multilingual, num_languages=model.num_languages,
                                  language=language, task="transcribe")
        # Checkpoint each utterance: interruption does not discard the whole ASR pass.
        segments = []
        for rec in records:
            wav = root / rec["audio"]
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
        result = {"language":language,"segments":segments,
                  "method":f"Whisper {model_name}: cached ASR + forced alignment of known narration script"}
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
        cues.extend(split_sentences(rec, matched, start, end))
    (out / "caption_timing.json").write_text(json.dumps(cues, ensure_ascii=False, indent=2))
    (out / f"subtitles.{language}.srt").write_text("\n\n".join(
        f"{i+1}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['caption']}"
        for i, c in enumerate(cues)) + "\n")
    (out / f"subtitles.{language}.vtt").write_text("WEBVTT\n\n" + "\n\n".join(
        f"{timestamp(c['start'], '.')} --> {timestamp(c['end'], '.')}\n{c['caption']}" for c in cues) + "\n")
    print(f"Edited captions ({language}): {len(cues)} cues, Whisper words: {len(words)}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["tts", "captions"])
    parser.add_argument("doc", type=Path, help="storyboard.json or visual_manifest.json")
    parser.add_argument("--model", default="base")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()
    doc = args.doc.resolve()
    if args.stage == "tts":
        asyncio.run(generate(doc, args.fps))
    else:
        captions(doc, args.model)
