"""Local reading pauses after human feedback; no external transmission."""
import json,wave
from pathlib import Path
H=Path(__file__).resolve().parent;N=H/'narration_update';records=json.loads((N/'assets/audio/manifest.json').read_text());cues=json.loads((N/'output/caption_timing.json').read_text());r=records[0];p=N/r['audio']
backup=p.with_name('B14_before_reading_pauses.wav')
if backup.exists():raise RuntimeError('Already applied; restore before repeating')
backup.write_bytes(p.read_bytes());pauses=[(9.73,2),(14.45,3),(21.35,4)]
with wave.open(str(p)) as w:params=w.getparams();raw=w.readframes(w.getnframes());stride=w.getsampwidth()*w.getnchannels();rate=w.getframerate()
parts=[];cursor=0
for t,length in pauses:
 pos=round(t*rate)*stride;parts.extend([raw[cursor:pos],bytes(round(length*rate)*stride)]);cursor=pos
parts.append(raw[cursor:])
with wave.open(str(p),'wb') as w:w.setparams(params);w.writeframes(b''.join(parts))
for c in cues:
 if c['start']<30:
  st,en=c['start'],c['end'];c['start']=st+sum(n for t,n in pauses if st>=t-.001);c['end']=en+sum(n for t,n in pauses if en>t+.001);c['timing_source']='measured Whisper anchors + local reading pauses'
 else:c['start']+=9;c['end']+=9
r['duration']+=9;r['end']+=9
for r in records[1:]:r['start']+=9;r['end']+=9
for p,obj in [(N/'assets/audio/manifest.json',records),(N/'output/caption_timing.json',cues),(H/'output/pacing_edit.json',{'feedback':'수식들이 너무 빠르게 휙휙 넘어가버려','added_s':9,'pauses':pauses,'external_tts':False})]:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
