"""Synthesize each locked beat, measure it, and emit the shared frame timeline."""
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'

def run(args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL)

def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)]))

def stamp(t):
    ms=round(t*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

async def main():
    doc=json.loads((ROOT/'narration_manifest.json').read_text())
    audio=OUT/'audio'; audio.mkdir(parents=True,exist_ok=True)
    semaphore=asyncio.Semaphore(3)
    async def one(beat):
        async with semaphore:
            path=audio/(beat['id']+'.mp3')
            key=hashlib.sha256((beat['text']+'SunHiNeural-5%').encode()).hexdigest()
            cache=path.with_suffix('.sha256')
            if not path.exists() or not cache.exists() or cache.read_text()!=key:
                await asyncio.wait_for(edge_tts.Communicate(beat['text'],'ko-KR-SunHiNeural',rate='-5%').save(str(path)),90)
                cache.write_text(key)
            speech=duration(path)
            frames=math.ceil(max(beat['target_seconds'],speech+beat['pause_after']+.25)*30)
            wav=path.with_suffix('.wav')
            run(['ffmpeg','-v','error','-y','-i',str(path),'-af','adelay=250,apad','-t',str(frames/30),'-ar','48000','-ac','1',str(wav)])
            return dict(beat,frames=frames,duration=frames/30,speech_duration=speech,audio=str(wav.relative_to(ROOT)))
    beats=await asyncio.gather(*(one(b) for b in doc['beats']))
    frame=0
    for b in beats:
        b['start_frame']=frame; b['start']=frame/30
        frame+=b['frames']; b['end_frame']=frame; b['end']=frame/30
    timeline=dict(fps=30,width=1920,height=1080,frames=frame,duration=frame/30,beats=beats)
    (OUT/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
    concat=audio/'concat.txt'
    concat.write_text(''.join(f"file '{ROOT/b['audio']}'\n" for b in beats))
    run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c:a','pcm_s16le',str(OUT/'narration.wav')])
    captions=[]
    for b in beats:
        caption=b.get('caption',b['text'])
        captions.append(f"{len(captions)+1}\n{stamp(b['start']+.25)} --> {stamp(b['start']+.25+b['speech_duration'])}\n{caption}")
    (OUT/'subtitles.ko.srt').write_text('\n\n'.join(captions)+'\n')
    print(f"Locked {len(beats)} beats, {frame} frames, {frame/30:.2f}s")

if __name__=='__main__': asyncio.run(main())
