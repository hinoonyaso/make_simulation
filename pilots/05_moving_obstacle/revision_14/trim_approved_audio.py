"""Remove seven repeated transition sentences locally; retain narration speed."""
import json,math,re,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;A=H/'assets/audio';O=H/'output'
audio=json.loads((A/'manifest.json').read_text());doc=json.loads((H/'visual_manifest.json').read_text());changes=[]
for r in audio:
 if r['beat'] not in ['B09','B11','B13','B16','B17','B19','B20']:continue
 original=A/f'{r["beat"]}.approved_original.wav';assert not original.exists(),'Local edit already applied'
 shutil.copy2(H/r['audio'],original)
 w=json.loads((A/f'{r["beat"]}.alignment.json').read_text())['result']['segments'][0]['words']
 i=next(i for i,x in enumerate(w) if x['word'].strip() in ['.','?','!']);cut=w[i+1]['start']-.08
 duration=math.ceil((r['duration']-cut-.1)*30)/30
 text=re.split(r'(?<=[.?!])\s+',r['text'],maxsplit=1)[1];caption=re.split(r'(?<=[.?!])\s+',r['caption'],maxsplit=1)[1]
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(original),'-af',f'atrim=start={cut},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,apad','-t',str(duration),'-ar','48000','-ac','1',str(H/r['audio'])],check=True)
 changes.append({'beat':r['beat'],'removed':r['text'][:len(r['text'])-len(text)].strip(),'source_cut_s':cut,'duration_s':duration})
 r.update(text=text,caption=caption,duration=duration,local_edit={'original':str(original.relative_to(H)),'cut_start_s':cut,'basis':'Known-script Whisper alignment at first sentence; 80ms pre-roll, 12ms fade; no speed change; tail shortened 100ms'})
now=0
for r in audio:r.update(start=now,end=now+r['duration']);now=r['end']
by={r['beat']:r for r in audio}
for b in doc['beats']:
 r=by[b['id']];b.update(text=r['text'],caption=r['caption'],sec=r['duration'],audio=r['audio'])
(A/'manifest.json').write_text(json.dumps(audio,ensure_ascii=False,indent=2)+'\n');(H/'visual_manifest.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
listing=A/'concat.txt';listing.write_text(''.join(f"file '{H/r['audio']}'\n" for r in audio));subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c:a','pcm_s16le',str(O/'narration.wav')],check=True)
(O/'local_audio_edits.json').write_text(json.dumps({'changes':changes,'final_duration_s':now,'speed_changed':False},ensure_ascii=False,indent=2)+'\n');assert 240<=now<=360,now;print('Locally edited duration:',now)
