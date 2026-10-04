#!/usr/bin/env python3
"""Final-media gate. The optional checks replace the per-topic validate.py media blocks."""
from __future__ import annotations
import argparse, json, subprocess
from fractions import Fraction
from pathlib import Path


def ffprobe(path: Path):
    cmd=["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(path)]
    return json.loads(subprocess.check_output(cmd,text=True,encoding="utf-8"))


def main():
    ap=argparse.ArgumentParser(description="Fail delivery below the visual quality floor.")
    ap.add_argument("media")
    ap.add_argument("--min-width",type=int,default=1920)
    ap.add_argument("--min-height",type=int,default=1080)
    ap.add_argument("--require-audio",action="store_true")
    ap.add_argument("--fps",type=str,help="exact frame rate, e.g. 30 or 30000/1001")
    ap.add_argument("--audio-manifest",type=Path,help="assets/audio/manifest.json from core/narration/prepare_audio.py; video must end with the narration")
    ap.add_argument("--caption-timing",type=Path,help="output/caption_timing.json; every cue must stay inside its utterance window")
    ap.add_argument("--duration-tolerance",type=float,default=0.12)
    ap.add_argument("--full-decode",action="store_true",help="decode every frame to catch corrupt output")
    args=ap.parse_args(); path=Path(args.media)
    if not path.exists(): raise SystemExit(f"missing: {path}")
    data=ffprobe(path); streams=data.get("streams",[])
    videos=[s for s in streams if s.get("codec_type")=="video"]
    audios=[s for s in streams if s.get("codec_type")=="audio"]
    if not videos: raise SystemExit("FAIL: no video stream")
    v=videos[0]; w=int(v.get("width",0)); h=int(v.get("height",0))
    if w < args.min_width or h < args.min_height:
        raise SystemExit(f"FAIL: {w}x{h} < {args.min_width}x{args.min_height}; preview-sized media cannot be delivered")
    if args.require_audio and not audios: raise SystemExit("FAIL: audio stream required")
    report=[f"{w}x{h}", f"video={v.get('codec_name')}", f"audio_streams={len(audios)}"]
    if args.fps:
        fps=Fraction(v.get("r_frame_rate","0/1"))
        if fps!=Fraction(args.fps): raise SystemExit(f"FAIL: fps {fps} != {args.fps}")
        report.append(f"fps={args.fps}")
    records=None
    if args.audio_manifest:
        records=json.loads(args.audio_manifest.read_text(encoding="utf-8"))
        dur=float(data["format"]["duration"]); expected=records[-1]["end"]
        if abs(dur-expected)>args.duration_tolerance:
            raise SystemExit(f"FAIL: duration {dur:.3f}s differs from narration end {expected:.3f}s by >{args.duration_tolerance}s")
        report.append(f"duration={dur:.2f}s~narration")
    if args.caption_timing:
        if records is None: raise SystemExit("--caption-timing requires --audio-manifest")
        cues=json.loads(args.caption_timing.read_text(encoding="utf-8"))
        if len(cues)<len(records): raise SystemExit(f"FAIL: {len(cues)} caption cues < {len(records)} utterances")
        covered=set()
        for i,c in enumerate(cues):
            # A long utterance may be split into sentence cues; each must stay inside its own utterance.
            mid=(c["start"]+c["end"])/2
            owner=next((j for j,a in enumerate(records) if a["start"]<=mid<a["end"]),None)
            if owner is None or not records[owner]["start"]<=c["start"]<c["end"]<=records[owner]["end"]:
                raise SystemExit(f"FAIL: caption {i+1} {c['start']:.2f}-{c['end']:.2f}s outside its utterance")
            covered.add(owner)
        if len(covered)!=len(records): raise SystemExit(f"FAIL: utterances without captions: {sorted(set(range(len(records)))-covered)}")
        report.append(f"captions={len(cues)}")
    if args.full_decode:
        subprocess.run(["ffmpeg","-v","error","-i",str(path),"-f","null","-"],check=True)
        report.append("full_decode=passed")
    print("PASS: "+", ".join(report))

if __name__ == "__main__": main()
