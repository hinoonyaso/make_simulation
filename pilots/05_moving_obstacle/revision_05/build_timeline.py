"""Derive the combined timeline from one manifest and retained/new local audio."""
import json,subprocess,shutil
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output';OLD=H.parent/'revision_04'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
if not (O/'new_audio_manifest.json').exists():
 shutil.copyfile(H/'assets/audio/manifest.json',O/'new_audio_manifest.json');shutil.copyfile(O/'caption_timing.json',O/'new_caption_timing.json')
new=read(O/'new_audio_manifest.json');old=read(OLD/'assets/audio/manifest.json');by={r['beat']:r for r in new+old}
newbeats={b['id']:b for b in read(H/'new_audio.json')['beats']};doc=read(H/'visual_manifest.json');records=[];cues=[];now=0
for b in doc['beats']:
 bid=b['id'];src=by[bid];r=src.copy();r['start']=now;r['end']=now+r['duration'];b['sec']=r['duration']
 if bid.startswith('B'):r['audio']='../revision_04/'+r['audio']
 b['audio']=r['audio']
 source_cues=read(OLD/'output/caption_timing.json') if bid.startswith('B') else read(O/'new_caption_timing.json')
 for c in source_cues:
  if src['start']<=(c['start']+c['end'])/2<src['end']:
   cues.append({**c,'start':c['start']+now-src['start'],'end':c['end']+now-src['start']})
 records.append(r);now=r['end']
write(H/'visual_manifest.json',doc);write(H/'assets/audio/manifest.json',records);write(O/'caption_timing.json',cues)
(O/'subtitles.ko.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["caption"]}' for i,c in enumerate(cues))+'\n')
concat=H/'assets/audio/concat.txt';concat.write_text(''.join(f"file '{(H/r['audio']).resolve().as_posix()}'\n" for r in records))
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c:a','pcm_s16le',str(O/'narration.wav')],check=True)
print('TIMELINE',now,'seconds',len(cues),'sentence cues')
