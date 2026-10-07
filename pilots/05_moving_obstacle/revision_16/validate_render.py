"""Recorded poses, media dimensions, unchanged data/audio and re-used picture parts."""
import hashlib,json,subprocess,wave
from pathlib import Path
H=Path(__file__).resolve().parent;PREV=H.parent/'revision_14';O=H/'output'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for p in sorted((H/'data').glob('*.json')):
 assert sha(p)==sha(PREV/'data'/p.name);checks.append({'file':str(p.relative_to(H)),'sha256':sha(p),'matches_R14':True})
for p in sorted((H/'assets/audio').glob('B*.wav')):
 if p.stem in ['B14','B22']:continue
 assert sha(p)==sha(PREV/'assets/audio'/p.name);checks.append({'file':str(p.relative_to(H)),'sha256':sha(p),'matches_R14':True})
assert json.loads((O/'pacing_edit.json').read_text())['external_tts'] is False
audio=json.loads((H/'assets/audio/manifest.json').read_text())
raw=[]
for row in audio:
 with wave.open(str(H/row['audio']),'rb') as w:
  assert abs(w.getnframes()/w.getframerate()-row['duration'])<1/30+.001
  raw.append(w.readframes(w.getnframes()))
with wave.open(str(O/'narration.wav'),'rb') as w:assert w.readframes(w.getnframes())==b''.join(raw)
for row in audio:
 if row['beat'] not in ['B05','B07','B09','B11','B12','B13','B14','B15','B16','B17','B19','B22']:continue
 path=O/f'final_render/videos/reasoning_scene/1080p30/Patch{row["beat"]}.mp4'
 stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,duration','-of','json',str(path)],text=True))['streams'][0]
 assert (stream['width'],stream['height'],stream['r_frame_rate'])==(1920,1080,'30/1')
 assert abs(float(stream['duration'])-row['duration'])<=.25,(row['beat'],stream['duration'],row['duration'])
report={}
for k in ['equal','left','spin','stop']:
 d=O/'cases'/k;mapping=json.loads((d/'mapping_0001.json').read_text());rows=mapping['records']
 assert len(rows)==181 and [r['frame'] for r in rows]==list(range(1,182))
 assert all(r['wheel_pose_check']=='PASS' and r['variant']=='material' and 'recorded' in r['annotations'] for r in rows)
 assert all(rows[f-1]['ortho_scale_m']>.9 for f in [1,39,40,145,146,181])
 assert rows[75]['ortho_scale_m']<.7
 assert all((d/f'frames/frame_{f:04d}.png').exists() for f in range(1,182))
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(d/'raw.mp4')],text=True))['streams'][0]
 assert (info['width'],info['height'],info['r_frame_rate'],info['nb_frames'])==(1920,1080,'30/1','181')
 subprocess.run(['ffmpeg','-v','error','-i',str(d/'raw.mp4'),'-f','null','-'],check=True)
 report[k]={'status':'PASS','frames':181,'pose_checks':'181/181','probe':info,'physics_source':'read-only R14 run'}
(O/'case_render_validation.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'reuse_validation.json').write_text(json.dumps({'status':'PASS','checks':checks,'narration_and_captions':'B14 reading pauses; B22 complete sentence cut; other WAVs byte-identical to R14'},indent=2)+'\n')
print('RENDER / SOURCE REUSE PASS')
