"""Validate R17 audio reuse, solver state boundaries and rendered dimensions."""
import hashlib,json,subprocess,wave
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output';P=H.parent/'revision_16'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for p in (H/'data').glob('*.json'):
 assert sha(p)==sha(P/'data'/p.name);checks.append(str(p.relative_to(H)))
for p in (H/'assets/audio').glob('B*.wav'):
 if p.stem not in ['B14','B19','B20']:assert sha(p)==sha(P/'assets/audio'/p.name)
rows=json.loads((H/'assets/audio/manifest.json').read_text());pcm=[]
for r in rows:
 with wave.open(str(H/r['audio'])) as w:
  assert abs(w.getnframes()/w.getframerate()-r['duration'])<.034;pcm.append(w.readframes(w.getnframes()))
with wave.open(str(O/'narration.wav')) as w:assert w.readframes(w.getnframes())==b''.join(pcm)
for bid in ['B14','B19']:
 p=O/f'final_render/videos/reasoning_scene/1080p30/Patch{bid}.mp4'
 stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,duration','-of','json',str(p)],text=True))['streams'][0]
 assert (stream['width'],stream['height'],stream['r_frame_rate'])==(1920,1080,'30/1')
 assert abs(float(stream['duration'])-next(r['duration'] for r in rows if r['beat']==bid))<.25
mapping=json.loads((O/'cases/left/mapping_0001.json').read_text())['records'];assert len(mapping)==181
assert all(r['wheel_pose_check']=='PASS' for r in mapping)
assert [r['frame'] for r in mapping]==list(range(1,182))
assert all(r['view']=='wheel_ground' for r in mapping[99:125])
hand=json.loads((O/'handoff/mapping.json').read_text());assert hand['status']=='PASS' and hand['source_pose_sample']==119 and hand['next_encoded_source_sample']==120
original=json.loads((H.parent/'revision_10/output/blender/source_mapping.json').read_text());assert original[316]['source_index']==120 and original[316]['frame']==317
assert all(a['source_index']<=b['source_index'] for a,b in zip(original[316:722],original[317:722]))
(O/'reuse_validation.json').write_text(json.dumps({'status':'PASS','data_identical_R16':checks,'audio_replaced':['B14','B19','B20'],'other_audio':'byte identical R16','handoff':hand,'case_pose_checks':181},indent=2)+'\n')
print('R17 RENDER / REUSE / SOURCE CONTINUITY PASS')
