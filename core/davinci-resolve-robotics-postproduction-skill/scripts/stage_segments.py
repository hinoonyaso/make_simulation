from __future__ import annotations
import json, sys
from pathlib import Path

# Consumes the Director visual_manifest.json after Manim/Blender filled each beat's `media`.
def main(manifest_path, out_path):
    manifest=Path(manifest_path).resolve(); base=manifest.parent
    d=json.loads(manifest.read_text(encoding='utf-8'))
    segs=[]; unrendered=[]
    for beat in d.get('beats',[]):
        media=beat.get('media') or beat.get('render')
        if not media:
            if beat.get('tool') in {'M','B'}: unrendered.append(beat.get('id','?'))
            continue
        p=(base/media).resolve()
        if not p.exists(): raise SystemExit(f'FAIL: missing media for {beat.get("id","?")}: {p}')
        audio=beat.get('audio')
        seg={'beat':beat.get('id',''), 'media':str(p), 'sec':beat.get('sec'),
             'audio':str((base/audio).resolve()) if audio else ''}
        # One rendered shot may carry several beats; media_in/out select the beat's range in it.
        for k in ('media_in','media_out'):
            if beat.get(k) is not None: seg[k]=float(beat[k])
        segs.append(seg)
    if unrendered: raise SystemExit(f'FAIL: Manim/Blender beats without media: {", ".join(unrendered)}')
    if not segs: raise SystemExit('FAIL: 0 segments; fill beats[].media after rendering')
    seen={}
    for g in segs:
        key=(g['media'],g.get('media_in'),g.get('media_out'))
        if key in seen: raise SystemExit(f'FAIL: {g["beat"]} repeats {seen[key]} media range; set media_in/media_out')
        seen[key]=g['beat']
    Path(out_path).write_text(json.dumps({'segments':segs},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(segs)} segments')
if __name__=='__main__':
    if len(sys.argv)!=3: raise SystemExit('usage: stage_segments.py visual_manifest.json sequence.json')
    main(sys.argv[1],sys.argv[2])
