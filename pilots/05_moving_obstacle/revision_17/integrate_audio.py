"""Integrate only the three explicitly approved R17 TTS utterances; reuse others exactly."""
import json,shutil,wave
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'revision_16';N=H/'narration_update';O=H/'output'
old=json.loads((P/'assets/audio/manifest.json').read_text());oldc=json.loads((P/'output/caption_timing.json').read_text());new={r['beat']:r for r in json.loads((N/'assets/audio/manifest.json').read_text())};newc=json.loads((N/'output/caption_timing.json').read_text());doc=json.loads((H/'visual_manifest.json').read_text());offset=0;records=[];cues=[];chunks=[]
for rec,beat in zip(old,doc['beats']):
 source=new.get(rec['beat'],rec);sourcec=newc if rec['beat'] in new else oldc;row=dict(source);duration=row['duration'];origin=row['start']
 if rec['beat'] in new:shutil.copy2(N/row['audio'],H/row['audio'])
 row['start']=offset;row['end']=offset+duration;beat['sec']=duration;beat['audio']=row['audio'];records.append(row)
 for c in sourcec:
  if origin<=c['start']<source['end']:cues.append(dict(c,start=c['start']-origin+offset,end=c['end']-origin+offset))
 with wave.open(str(H/row['audio']),'rb') as w:params=w.getparams();chunks.append(w.readframes(w.getnframes()))
 offset+=duration
with wave.open(str(O/'narration.wav'),'wb') as w:w.setparams(params);w.writeframes(b''.join(chunks))
for path,obj in [(H/'assets/audio/manifest.json',records),(O/'caption_timing.json',cues),(H/'visual_manifest.json',doc)]:path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print('Integrated audio:',offset,'seconds,',len(cues),'sentence captions')
