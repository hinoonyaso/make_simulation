import json,wave,math,array
from pathlib import Path
h=Path(__file__).resolve().parent; old=h.parent/'revision_14'
a=json.loads((old/'assets/audio/manifest.json').read_text()); cues=json.loads((old/'output/caption_timing.json').read_text()); doc=json.loads((h/'visual_manifest.json').read_text())
def read(p):
 with wave.open(str(p),'rb') as f:return f.getparams(),f.readframes(f.getnframes())
def write(p,param,data):
 with wave.open(str(p),'wb') as f:f.setparams(param);f.writeframes(data)
params,raw=read(old/'assets/audio/B14.wav'); frame=params.nchannels*params.sampwidth;rate=params.framerate
parts=[];last=0
for t in [8.19,14.31]:
 n=round(t*rate)*frame;parts.extend([raw[last:n],bytes(4*rate*frame)]);last=n
parts.append(raw[last:]);
# Short boundary ramps suppress clicks at local sentence edits, without changing speech rate.
for i,part in enumerate(parts):
 if i%2:continue
 x=array.array('h',part);n=round(.006*rate)
 if i>0:
  for j in range(min(n,len(x))):x[j]=round(x[j]*j/n)
 if i<len(parts)-1:
  for j in range(min(n,len(x))):x[-j-1]=round(x[-j-1]*j/n)
 parts[i]=x.tobytes()
write(h/'assets/audio/B14.wav',params,b''.join(parts))
params,raw=read(old/'assets/audio/B22.wav');cut=11.13;length=math.ceil((19.5333333333-cut)*30)/30
raw=raw[round(cut*rate)*frame:];x=array.array('h',raw);n=round(.012*rate)
for j in range(n):x[j]=round(x[j]*j/n)
raw=x.tobytes();raw+=bytes(max(0,round(length*rate)*frame-len(raw)));write(h/'assets/audio/B22.wav',params,raw)
newc=[];offset=0;allraw=[]
for row,beat in zip(a,doc['beats']):
 oldstart=row['start'];local=[dict(x,start=x['start']-oldstart,end=x['end']-oldstart) for x in cues if oldstart<=x['start']<row['end']]
 if row['beat']=='B14':
  for c in local:
   s,e=c['start'],c['end'];c['start']=s+sum(4 for p in [8.19,14.31] if s>=p-.001);c['end']=e+sum(4 for p in [8.19,14.31] if e>p+.001);c['timing_source']='approved whisper timings + local reading pauses'
  row['duration']+=8
 if row['beat']=='B22':
  local=[dict(c,start=c['start']-cut,end=c['end']-cut,timing_source='approved whisper timings + sentence cut') for c in local if c['start']>=cut-.001];row['duration']=length;row['text']=row['caption']=local[0]['caption'];beat['text']=beat['caption']=row['text'];beat['focus']='계획·명령·실제 응답을 구분해 정리'
 row['start']=offset;row['end']=offset+row['duration'];beat['sec']=row['duration'];beat['media']=beat['media_in']=beat['media_out']=None
 newc.extend(dict(c,start=c['start']+offset,end=c['end']+offset) for c in local);offset=row['end'];allraw.append(read(h/row['audio'])[1])
write(h/'output/narration.wav',params,b''.join(allraw))
for p,obj in [(h/'assets/audio/manifest.json',a),(h/'output/caption_timing.json',newc),(h/'visual_manifest.json',doc)]:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
(h/'output/pacing_edit.json').write_text(json.dumps({'user_feedback':'수식 도출이 빠름','B14':{'insert_silence_seconds':[{'at_source_s':8.19,'duration':4},{'at_source_s':14.31,'duration':4}]},'B22':{'remove_source_seconds':[0,cut],'kept':'final complete recap sentence'},'total_s':offset,'external_tts':False},ensure_ascii=False,indent=2)+'\n')
print(offset)
